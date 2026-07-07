"""巨潮(cninfo) A股公告采集器（阶段B·B1，原第0批 T1）。

本刀只做"抓"——拉某票某时间段的公告列表，返回结构化记录，**不入库**（落库是下一刀）。
红线：只忠实抓取公开公告事实，不解读、不抽事件、不打标签。

避坑（《雷达_开源借鉴参考》第1章，已核实）：
  ① announcementTime 是 Unix **毫秒整数** → 转 timezone-aware **UTC** datetime（入 valid_time）。
     别转成 '%Y-%m-%d' 字符串——丢时分秒和时区会破坏 bitemporal 精度。
  ② orgId 不是统一 gssh0{code} 格式（601xxx 段尤其乱）→ 拉官方映射表 szse_stock.json
     (~6198 只) 做模块级缓存；查不到再回退硬编码。硬编码会大量静默查不到公告。
  ③ 接口 POST cninfo.com.cn/new/hisAnnouncement/query；防风控=串行限流(≥1s+抖动)+会话复用。

依赖：仅标准库（urllib/json）——低频串行采集无需第三方 HTTP 客户端。
"""
import datetime as dt
import json
import random
import time
import urllib.error
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
QUERY_URL = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
ORGID_URL = "http://www.cninfo.com.cn/new/data/szse_stock.json"
STATIC_BASE = "http://static.cninfo.com.cn/"

MIN_INTERVAL = 1.0   # 串行限流：相邻请求最小间隔（秒）
JITTER = 0.6         # 随机抖动上限（秒）
PAGE_SIZE = 30

# 巨潮间歇性抽风（实测会对单票分页查询偶发 404，重试即恢复）。瞬时 4xx/5xx + 网络错
# 重试+指数退避，避免一只票一次抖动拖垮整条采集→整条 cron→夜里飞书误报。
# 持续失败（重试用尽）仍抛出，由上层跳过该票并最终告警，不静默吞（守 dead-man）。
RETRYABLE_HTTP = {404, 429, 500, 502, 503, 504}
MAX_TRIES = 3
BACKOFF = 1.5        # 退避基数（秒）：约 1.5 / 3 / 6 + 抖动

_ORGID_MAP: dict[str, str] = {}
_last_req = 0.0


def _throttle() -> None:
    """串行限流：保证相邻请求间隔 ≥ MIN_INTERVAL + 随机抖动（合规/防风控）。"""
    global _last_req
    wait = MIN_INTERVAL + random.uniform(0, JITTER) - (time.monotonic() - _last_req)
    if wait > 0:
        time.sleep(wait)
    _last_req = time.monotonic()


def _retry(fn, what: str):
    """对单次请求做重试+指数退避：可重试 HTTP 码 / 网络错误才重试，余者立即抛。
    每次尝试内部各自 _throttle()（含每次 urlopen 调用），保持限流纪律。"""
    for i in range(1, MAX_TRIES + 1):
        try:
            return fn()
        except urllib.error.HTTPError as e:
            if e.code not in RETRYABLE_HTTP or i == MAX_TRIES:
                raise
            reason = f"HTTP {e.code}"
        except (urllib.error.URLError, TimeoutError) as e:  # 含连接/超时
            if i == MAX_TRIES:
                raise
            reason = type(e).__name__
        wait = BACKOFF * (2 ** (i - 1)) + random.uniform(0, JITTER)
        print(f"[cninfo] {what} {reason}，{wait:.1f}s 后重试 ({i}/{MAX_TRIES})")
        time.sleep(wait)


def _http_get(url: str, timeout: float = 15) -> bytes:
    def attempt() -> bytes:
        _throttle()
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    return _retry(attempt, f"GET {url}")


def _http_post(url: str, form: dict, timeout: float = 20) -> dict:
    body = urllib.parse.urlencode(form).encode()

    def attempt() -> dict:
        _throttle()
        req = urllib.request.Request(url, data=body, headers={
            "User-Agent": UA,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "http://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice",
        })
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    return _retry(attempt, f"POST {url}")


def ts_to_utc(ms) -> dt.datetime | None:
    """巨潮 announcementTime（Unix 毫秒整数）→ timezone-aware UTC datetime（避坑①）。"""
    if isinstance(ms, (int, float)):
        return dt.datetime.fromtimestamp(ms / 1000, tz=dt.timezone.utc)
    return None


def orgid(code: str) -> str:
    """查股票真实 orgId：优先官方映射表（模块级缓存），查不到回退硬编码（避坑②）。"""
    global _ORGID_MAP
    if not _ORGID_MAP:
        try:
            data = json.loads(_http_get(ORGID_URL).decode("utf-8"))
            _ORGID_MAP = {s["code"]: s["orgId"] for s in data.get("stockList", [])}
            print(f"[cninfo] orgId 映射表已加载 {_ORGID_MAP.__len__()} 只")
        except Exception as e:  # noqa: BLE001
            print(f"[WARN] orgId 映射表拉取失败，回退硬编码: {e}")
    org = _ORGID_MAP.get(code)
    if org:
        return org
    return f"gssh0{code}" if code.startswith("6") else ""


def _column(code: str) -> str:
    """板块列：沪市=sse，深市=szse，北交所=bj。"""
    if code.startswith("6"):
        return "sse"
    if code[0] in ("0", "3"):
        return "szse"
    return "bj"


def fetch_announcements(code: str, start: dt.date, end: dt.date,
                        category: str = "") -> list[dict]:
    """抓单票 [start, end] 公告列表（不入库）。返回结构化记录，valid_time 已转 UTC。

    code: 无后缀股票代码，如 '300308'。category: 巨潮类目代码，空=全部。
    """
    org = orgid(code)
    if not org:
        # P0-3：orgId 缺失=深市票必然查空。带空串照常查会静默入库 0 条且链报 OK，
        # 绕过全部 dead-man（审视 P0-3）。改为抛错进单票隔离通道：该票记 failed_codes，
        # 持续失败 exit(1) → 链 FAIL → 飞书出声。
        raise RuntimeError(f"{code} orgId 未解析（映射表拉取失败且无硬编码回退），拒绝静默空查")
    se_date = f"{start.isoformat()}~{end.isoformat()}"
    column = _column(code)
    out: list[dict] = []
    page = 1
    while True:
        resp = _http_post(QUERY_URL, {
            "stock": f"{code},{org}",
            "tabName": "fulltext",
            "pageSize": str(PAGE_SIZE),
            "pageNum": str(page),
            "column": column,
            "category": category,
            "plate": "",
            "seDate": se_date,
            "searchkey": "",
            "secid": "",
            "sortName": "",
            "sortType": "",
            "isHLtitle": "false",   # 关高亮，拿干净标题
        })
        anns = resp.get("announcements") or []
        for a in anns:
            out.append({
                "announcement_id": a.get("announcementId"),
                "stock_code": a.get("secCode") or code,
                "raw_company_name": a.get("secName"),
                "title": (a.get("announcementTitle") or "").strip(),
                "valid_time": ts_to_utc(a.get("announcementTime")),
                "announcement_type": a.get("announcementType") or None,
                "source_url": (STATIC_BASE + a["adjunctUrl"]) if a.get("adjunctUrl") else None,
            })
        if not resp.get("hasMore"):
            break
        page += 1
    return out

#!/usr/bin/env python3
"""exp24 数据前置 · SOX 第二源交叉校验(Yahoo ^SOX;人令 2026-07-27 二,裁定 A4)。

AWS 出口执行(Yahoo 阿里云出口不可靠)。只做交叉校验:Yahoo 原始响应与 SHA256 **仅存
内部证据包**(裁定 A4 原文),不入库、不入仓;主锚数据(qbase sox_daily_snap)不因交叉
差异回改——差异如实入报告(NOT_FOR_VERDICT 性质的数据质量事实)。

输入:--qbase-csv = 主锚批导出 CSV(trade_date,close;由只读 psql COPY 导出)。
输出:证据包内 yahoo_SOX_raw.json(+SHA)与 cross_check_report.txt。

用法:python sox_cross_check.py --qbase-csv sox_batch.csv --evidence <dir>
"""
import argparse
import csv
import hashlib
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal

UA = "Mozilla/5.0 (X11; Linux x86_64)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--qbase-csv", required=True)
    ap.add_argument("--evidence", required=True)
    a = ap.parse_args()
    os.makedirs(a.evidence, exist_ok=True)

    qrows = {}
    with open(a.qbase_csv, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            qrows[r["trade_date"]] = Decimal(r["close"])
    dmin, dmax = min(qrows), max(qrows)
    p1 = int(datetime.strptime(dmin, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()) - 86400
    p2 = int(datetime.strptime(dmax, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()) + 2 * 86400
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/%5ESOX"
           f"?period1={p1}&period2={p2}&interval=1d&events=history")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read()
    sha = hashlib.sha256(raw).hexdigest()
    raw_path = os.path.join(a.evidence, "yahoo_SOX_raw.json")
    with open(raw_path, "wb") as f:
        f.write(raw)

    doc = json.loads(raw)
    res = doc["chart"]["result"][0]
    tz = res["meta"].get("exchangeTimezoneName")
    ts = res["timestamp"]
    closes = res["indicators"]["quote"][0]["close"]
    yrows = {}
    for t, c in zip(ts, closes):
        if c is None:
            continue
        # Yahoo timestamp=交易日开盘时刻(美东);按美东日期归日
        d = datetime.fromtimestamp(t, tz=timezone.utc).astimezone(
            __import__("zoneinfo").ZoneInfo("America/New_York")).date().isoformat()
        yrows[d] = Decimal(str(c))

    common = sorted(set(qrows) & set(yrows))
    only_q = sorted(set(qrows) - set(yrows))
    only_y = sorted(d for d in yrows if dmin <= d <= dmax and d not in qrows)
    diffs = [(d, qrows[d], yrows[d], abs(qrows[d] - yrows[d])) for d in common]
    max_abs = max((x[3] for x in diffs), default=Decimal(0))
    n_2dp = sum(1 for x in diffs if x[3] < Decimal("0.005"))
    n_gt01 = [x for x in diffs if x[3] >= Decimal("0.1")]

    lines = [
        f"SOX 交叉校验(主锚=nasdaq_giw:sox_daily / 第二源=Yahoo ^SOX chart API)",
        f"fetch_time={datetime.now(timezone.utc).isoformat()}",
        f"yahoo_raw sha256={sha}  exchangeTimezoneName={tz}",
        f"主锚行数={len(qrows)}  范围={dmin}..{dmax}",
        f"Yahoo 同范围行数={len([d for d in yrows if dmin <= d <= dmax])}",
        f"共同交易日={len(common)}  仅主锚有={len(only_q)}  仅Yahoo有={len(only_y)}",
        f"收盘差(|q−y|): max={max_abs}  <0.005(2位小数一致)={n_2dp}/{len(common)}",
        f"差≥0.1 的日数={len(n_gt01)}",
    ]
    if only_q:
        lines.append(f"仅主锚有(前10): {only_q[:10]}")
    if only_y:
        lines.append(f"仅Yahoo有(前10): {only_y[:10]}")
    for d, q, y, ad in sorted(diffs, key=lambda x: -x[3])[:10]:
        lines.append(f"  最大差样本 {d}: 主锚={q} yahoo={y} |Δ|={ad}")
    report = "\n".join(lines) + "\n"
    with open(os.path.join(a.evidence, "cross_check_report.txt"), "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())

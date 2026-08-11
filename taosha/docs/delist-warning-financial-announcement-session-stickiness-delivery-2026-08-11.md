# exp22 公告索引会话粘性 v7 窄修交付

时间口径：2026-08-11，Asia/Shanghai（UTC+8）。

## 一、结论

本地窄修验收通过，停在推送与阿里云续跑边界。生产 commit：
`eac30dcdf25ee86d7c04a791ebd10cd2ef392983`。

根因不是公告规范化或双读规则错误，而是旧客户端每次请求均调用独立
`urlopen`，未保留官方响应设置的 `JSESSIONID`，使一次多页扫描可能跨后台索引视图。

## 二、失败证据与只读复现

- v6 失败锚：`000607.SZ / 2021-04-30`，metadata 非零退出，51/646 停止。
- pass A/B 请求逐字相同，各 32 行、无页内或跨页重复；共同 30 行，共同行逐字段相等。
- A 独有 ID：`1209863286 / 1209863287`；B 独有 ID：`1209863291 / 1209863314`。
- 页 1 `totalAnnouncement=32/35`，页 2 均为 32，证明分页期间官方视图漂移。
- 固定一个 Cookie 会话的限定四读 `1→2→1→2` 两遍均为 `35=30+5`，ID 集一致。

v1—v6 原始页、失败日志、错误记录、容器与 51 个合法 marker 均未修改。

## 三、生产改动

1. `qbase/ingest/cninfo.py`：GET/POST 共用一个含 `HTTPCookieProcessor` 的进程内
   opener；Cookie 只来自官方响应并由标准库管理。限流、超时、三次网络重试和解析不变。
2. `delist_warning_announcement_index.py`：新写入布局改为 `bisect_v7`；`bisect_v6`
   加入旧布局自验集合。
3. 攻击 fixture：证明 CookieProcessor 在场、GET/POST 使用同一 opener、v6 失败页不
   覆盖、v6 合法 marker 继续自验。

双遍规范化全集逐字段相等、每遍分页完整性、跨页 ID 唯一、API 计数闭合、混票/越界/
短页/页数上限等硬门均未修改。没有新增第三遍、交并集、择一、容差或重试到一致。

## 四、本地验收

```text
verify_delist_warning_announcement_bisection  34/34 PASS
verify_delist_warning_announcement_index      46/46 PASS
verify_delist_warning_announcement_localization 6/6 PASS
verify_delist_warning_routes                    6/6 PASS
verify_code_size: PASS; files=241, lines=36034, functions=1096,
  debt_files=20, debt_functions=50
verify_architecture: PASS; modules=172, edges=377, cross_experiment_debts=2
py_compile / git diff --check: PASS
```

第一次路由 fixture 命令误写为不存在的 `qbase.ingest.verify_delist_warning_routes`，在导入
阶段退出；随后用仓内真实入口 `taosha.harness.verify_delist_warning_routes` 复跑 6/6。
该命令错误没有修改代码、远端或证据。

## 五、停止线与下一步

当前未推送、未修改阿里云代码、未创建 v7 容器、未恢复监督或监控。下一步只能是：
推送两笔本地提交，阿里云精确 fast-forward，钉版镜像内复跑全部闸门；只在基线精确
等于 `routes646 / valid_done51 / first_pending 000607.SZ / errors6 / downstream0` 且旧
证据仍在时，才可用全新 `bisect_v7` 容器从 51/646 续跑。

E1 继续 `OPEN_FAIL_CLOSED`；零数据库写入、零利润 PIT、零终版 PAP、零密封、零冻结、
零 StudySnapshot、零研究 manifest、零收益读取、零正式研究运行、零 persist。

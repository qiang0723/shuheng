# exp24 §7 · JSON键序列化阻塞（2026-07-28）

## 结论

exp24 专属研究 manifest 已生成并完成三处发布；正式 §7 尚未执行。manifest 248 上的运行前 recon 在写 JSON 证据文件时，因 `selection_audit.pool_members_by_event_date` 使用 `datetime.date` 作为字典键而失败。正式 result 包含同一审计块，若继续也会在写 `result_exp24.json` 时以同样原因失败，因此按人令停止，不自动重跑、不绕过证据输出。

## 已完成且有效

- 人已确认 DSN 布线令确系本人发出，并授权继续既有 exp24 §7 令；
- 精确代码 commit：`2fb59655a6a40406d0be6b669cd0b3c4b142a67d`；生产镜像：`sha256:031efd1d1e9a179df71606fc4011c75034ab4db25d97723fba041aa9abb38581`，非 root 用户 `shuheng`；
- snapshot 247 钉批复现：最终事件 `19,258`，selection SHA256=`7a7840e596b755746fe5f038928fad622e2df83a32ba64d6105e9a9513b2acee`；
- exp24 专属研究 manifest：`snapshot_id=248`，digest=`c82d8a82eb69331799402ce9f025c35574a27ba8b3d6f2051dfaa1b8c881250a`；向量含 `daily=6 / adj_factor=7 / stock_basic=6 / namechange=7 / trade_cal=10 / sox_daily=13 / sw_member=14`；
- manifest 权威行、qbase 镜像、publication attestation 已发布；`verify_manifest_lineage 24/24`、`verify_snapshot_mirror 11/11`；
- manifest 248 recon 的标准输出已完成冻结漏斗计算：`314→301→碰撞9日剔22→292→19,258`，重复键0；但 JSON 文件在审计字典键处部分写入后退出，RC非零，该残件不得作为交付原件。

## 阻塞实物与最小修复面

- 失败位置：`taosha/harness/run_sox_spillover_study.py::_write_recon()` 的 `json.dump(...)`；
- 根因来源：`selection_audit()` 原样把 `pool_members_by_event_date: dict[date, int]` 放入 JSON 对象；`default=str`只转换值，不转换字典键；
- 最小修复建议：仅在 `selection_audit()` 的报告/JSON边界把该字典键确定性转换为 ISO `YYYY-MM-DD` 字符串，核心规则函数仍保留 `date` 键；fixture 增加真实 `date` 键审计块可完整 `json.dumps` 且键为ISO字符串的攻击断言；重跑专项、既有回归与合成e2e。不得改变规则、漏斗、统计或PAP。

该修复不在当前“manifest+§7单跑”既有授权内，须人另行明示后施工。修复验收通过后，应在 manifest 248 上重新运行 recon；通过后才执行正式 §7 一次。manifest 248 已合法发布，不重复生成。

## 停止线

- exp24 仍须保持 `frozen`，`result_json/done_at`为空；
- 正式收益未读取，正式单跑名额未消耗，persist 未授权；
- 阿里云证据目录：`/root/s24run/`；部分写入的 `out/recon_manifest248.json`须保留为失败痕迹，不得冒充成功件。

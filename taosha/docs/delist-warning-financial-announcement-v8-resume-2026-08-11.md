# exp22 公告索引 bisect_v8 续跑回执（2026-08-11，UTC+8）

## 结论

`bisect_v8` 已在完成本地与阿里云钉版镜像验收后，从既有合法检查点
`51/646` 启动。新证据只写入 `bisect_v8`；v1—v7 的容器、日志、错误记录、
失败页和 51 个合法完成 marker 均保留。

## 推送与远端代码身份

- GitHub `origin/main`：`269d60727f147df8f7a3d06914c246564e97f18f`
- 阿里云 `/opt/quant`：同一 commit，启动前工作树干净
- 镜像：`shuheng-quant:579a354`
- 镜像 ID：`sha256:e7b9b27078353243490c557c103cfeda95b139ebd11dfea3a31b606ede6ebfc3`

## 启动前只读硬闸

只读预检逐项命中：

- routes=`646`
- valid_done=`51`
- first_pending=`000607.SZ`
- historical errors=`7`
- raw pages：`annual_v2=121 / v3=320 / v4=494 / v5=3469 / v6=13982 / v7=359 / v8=0`
- `document_manifest.json`、`contract_queue.json`、`readback.json` 均不存在

预检同时为 v2—v7 每个旧布局计算只读页树 SHA256。首次预检因脚本文件权限
为 `600`、容器内非 root 用户不可读而在 Python 启动前退出；只把预检脚本改为
`644` 后重跑通过，监督脚本仍为 `700`，业务证据零变化。

## v8 启动身份

- 元数据容器：`s22-ann-index-v8`
- 容器 ID：`995cbbed3c599b43d3606c0b241fe53c694501ab16ed4685370f7181267d76c0`
- 启动时间：`2026-08-11 12:03:35+08`
- 监督 PID：`814665`
- 监督脚本 SHA256：`602d0e15c0eda26980a55e3a50009cd3b583a69af6d2e28a75e1f4d1297e32a4`

监督链只在上游阶段 exit 0 后依次进入：

1. metadata index；
2. document materialization；
3. evidence contract / `UNPROVEN` queue；
4. 12 票独立 readback。

任一阶段非零即 fail-closed，禁止自动重启。

## 启动后首读

首读为 `container=running / supervisor_alive=1 / valid_done=51 / errors=7 /
downstream=0`。首个完整 v8 原始页尚未落盘；进程处于与巨潮官方端的已建立
连接中，因此仅登记“已启动、尚未形成新完成页”，不冒充实质进度。

15 分钟 UTC+8 监控已从 `PAUSED` 更新为 `ACTIVE` 并切换至 v8。监控只读，
只在进度实质变化、阶段切换、失败或全部完成时回报。

## 停止线

本次没有数据库写入、利润 PIT、终版 PAP、密封、冻结、StudySnapshot、研究
manifest、收益读取、正式研究运行或 persist。E1 仍为 `OPEN_FAIL_CLOSED`。

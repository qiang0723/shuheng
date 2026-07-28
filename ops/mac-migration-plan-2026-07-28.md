# 开发工作面迁移方案 · AWS 工作机 → 本地 Mac Pro(2026-07-28)

> 人裁(2026-07-28):现 AWS 工作机(43.212.20.35)**不保留、将删除**;开发迁本地 Mac Pro。
> 本文=迁移施工单权威记录。状态更新走 ops/STATE.md,本文只在方案改判时改(显式作废旧条目)。

## 改判记(2026-07-28 二笔,人裁,当日晚)

1. **阶段 1 OSS 方案作废**:不开 OSS/RAM。异地备份由 **Mac Pro 承接每日拉取**(30 份轮转),AWS 现存 27G/30 份历史亦迁 Mac 存。阿里云侧 backup.sh 与本地 5 份留存**不变**。
2. **挂账 #1 落定**:22 端口=**全网放开**,端口形态之后再调整 → 关密码登录紧迫度升高,列为阶段 0 收尾硬步骤。
3. **挂账 #2 落定**:OSS 批复=否决(见第 1 条)。
4. **挂账 #4 落定**:老 AWS 雷达源机(43.213.181.243)**保留不动**。
5. **口径确认**:aliyun-new **不删除**;本迁移只删本 AWS 工作机(43.212.20.35),其余机器一律不动。
6. 阶段 0 加钥已闭:Mac 公钥(`ssh-ed25519 …LU/WIZ john`)已在 aliyun-new root 与本 AWS 机 authorized_keys 各 1 条(2026-07-28 核实)。

## 0. 现状盘点:AWS 工作机身上挂着什么

| 职责 | 现状 | 去向 |
|---|---|---|
| 开发工作面(仓 clone、Claude Code、会话) | `~/shuheng/quant`,HEAD 与两台同步 | → Mac Pro |
| **异地备份接收点(最后防线)** | cron 03:30 拉阿里云密文,30 份轮转,现存 27G | → **Mac Pro 承接每日拉取**(~~原方案 b 境内 OSS~~ 作废,改判记 #1) |
| 阿里云 22 端口白名单出口 | ~~43.212.20.35 在白名单~~ 作废:22 已全网放开(改判记 #2) | 端口形态之后人再调整 |
| GitHub 写权 deploy key | `~/.ssh/shuheng_ops` | → 撤销;Mac 用人账号 key(已加) |
| 交付/取证包 | `~/shuheng/s*_delivery_*` 共 20 包 30M | → 打包迁 Mac |
| Claude 记忆 | `~/.claude` 138M(按工作路径索引) | → 迁 Mac 并按新路径 key 重挂 |
| 老 AWS 雷达源私钥 | `~/shuheng/john-test.pem`(600) | → 安全迁 Mac(雷达源机保留,借阅通道续用) |

**铁序:阶段 1(备份链改道)验收完毕之前,不得删机。** AWS 机现兜着全体系仅有的 30 天备份史(本地阿里云已裁定只留 5 份)。顺序错 = 丢备份史。

## 1. 四阶段施工单

### 阶段 0 · Mac 侧就绪(人做,进行中)
- [x] 阿里云 22 端口放开(2026-07-28 人告知;**人裁=全网放开,之后再调整**)
- [x] Mac GitHub key 已加(2026-07-28 人告知)
- [x] Mac 网络拓扑固化(2026-07-28 人告知,见 §2)
- [x] Mac 公钥加入 aliyun-new authorized_keys + 本 AWS 机 authorized_keys(2026-07-28 核实各 1 条)
- [ ] Mac 侧验证(人做):`ssh root@47.103.32.81` 通 + `git clone git@github.com:qiang0723/shuheng.git` 通 + `ssh ubuntu@43.212.20.35` 通(拉 27G 历史用)
- [ ] 验证通过后**立即**:关闭 aliyun-new 密码登录 + root 密码登录(22 现全网开放且 root+密码可登,窗口期风险高;先有钥匙再锁门,验证一过就锁)

### 阶段 1 · 备份链改道 Mac Pro(~~原 OSS 方案作废~~,改判记 #1)
- [ ] 27G/30 份历史密文:Mac 从本 AWS 机 `~/shuheng-backups` rsync 拉走,校验份数+抽验 SHA
- [ ] Mac 侧每日拉取:适配 `offsite_pull_aws.sh` 为 Mac 版(launchd/cron;须容忍 Mac 关机漏拉=唤醒后补拉最近未取份),30 份轮转
- [ ] 验收(骗不了人):Mac 连续两日拉取成功 + 从 Mac 密文解密→pg_restore 演练通过
- [ ] 收尾:停用本 AWS 机 offsite_pull_aws.sh cron;文档改判(backup-chain 留档"AWS 异地"→"Mac 异地")
- 阿里云侧零改动:backup.sh、本地 5 份留存均不变(拉取模式,接收端换人)

### 阶段 2 · 工作面迁移
- [ ] 交付包(30M)+ john-test.pem 安全迁 Mac
- [ ] Claude 记忆迁移:`~/.claude` 打包 → Mac;枢衡项目记忆目录按 Mac 新工作路径改名重挂(具体命令届时出一行清单)
- [ ] Mac 试开工:读 STATE + 查库只读核对 + 试 push,全链路走通

### 阶段 3 · 收尾与删机(人做,全部验收过才动)
- [ ] GitHub 撤销 AWS deploy key(shuheng_ops);aliyun-new authorized_keys 删 AWS 公钥(`…shuheng-ops-aws` 条目)
- [ ] 文档终改判:STATE/ops 文档中 AWS 侧描述显式作废
- [ ] **最后删机**(只删 43.212.20.35;aliyun-new / 老 AWS 雷达源机不动)

## 2. Mac Pro 网络拓扑(人 2026-07-28 固化)

- 海外(Codex/GitHub/论文):macOS 系统代理 → Clash → 海外节点
- Docker 镜像:Docker Desktop 代理 → Clash
- 国内数据(tushare 等):scheduler 容器清空代理变量 + NO_PROXY/Docker bypass → ISP 国内直连(实测 2026-07-28:交易日历 8 行,461ms,HTTP/HTTPS/ALL 代理均未设置)
- 本地 Web:仅 127.0.0.1
- 未来海外采集:独立 research-overseas profile 显式走代理,不影响 scheduler
- 临时宿主机国内采集:进程级直连,不动 Clash / 系统网络

**要点:** ①SSH 阿里云走 ISP 直连(终端 ssh 不吃系统代理,Clash 国内直连);~~白名单对准家宽公网 IP~~ 22 现全网放开(改判记 #2),连不上不再有白名单因素;**绝不把 SSH 引到海外节点**(来源不稳 + 绕境外连境内库双重问题)。②GitHub 走 Clash、aliyun 走直连,部署链两段各走各路,成立。③Mac 承接每日备份拉取后,Mac 03:30 前后须在线或依赖补拉逻辑(阶段 1 施工时落实)。

## 3. 挂账待人裁

1. ~~22 端口"放开"形态澄清~~ **已裁(2026-07-28):全网放开,之后再调整**(改判记 #2)
2. ~~OSS 方案批复~~ **已裁(2026-07-28):否决,改 Mac 承接**(改判记 #1、#3)
3. **采集端是否迁 Mac(独立裁定,本迁移不含)**:当前口径=采集在 aliyun-new(库在哪采在哪,lineage 干净);Mac scheduler 容器若将来承担 qbase 采集=经公网写库的口径变化,须人另拍 —— **仍挂账**
4. ~~老 AWS 雷达源机去留~~ **已裁(2026-07-28):保留不动**(改判记 #4)

— 记录:2026-07-28;改判:2026-07-28 二笔;迁移进度以 ops/STATE.md 为准 —

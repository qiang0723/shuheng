# 开发工作面迁移方案 · AWS 工作机 → 本地 Mac Pro(2026-07-28)

> 人裁(2026-07-28):现 AWS 工作机(43.212.20.35)**不保留、将删除**;开发迁本地 Mac Pro。
> 本文=迁移施工单权威记录。状态更新走 ops/STATE.md,本文只在方案改判时改(显式作废旧条目)。

## 0. 现状盘点:AWS 工作机身上挂着什么

| 职责 | 现状 | 去向 |
|---|---|---|
| 开发工作面(仓 clone、Claude Code、会话) | `~/shuheng/quant`,HEAD 与两台同步 | → Mac Pro |
| **异地备份接收点(最后防线)** | cron 03:30 拉阿里云密文,30 份轮转,现存 27G | → **境内 OSS**(方案 b,§2.1 预裁方向) |
| 阿里云 22 端口白名单出口 | 43.212.20.35 在白名单 | → Mac ISP 出口 IP(人自理) |
| GitHub 写权 deploy key | `~/.ssh/shuheng_ops` | → 撤销;Mac 用人账号 key(已加) |
| 交付/取证包 | `~/shuheng/s*_delivery_*` 共 20 包 30M | → 打包迁 Mac |
| Claude 记忆 | `~/.claude` 138M(按工作路径索引) | → 迁 Mac 并按新路径 key 重挂 |
| 老 AWS 雷达源私钥 | `~/shuheng/john-test.pem`(600) | → 安全迁 Mac(若保留借阅通道) |

**铁序:阶段 1(备份链改道)验收完毕之前,不得删机。** AWS 机现兜着全体系仅有的 30 天备份史(本地阿里云已裁定只留 5 份)+ 白名单既有出口。顺序错 = 同时丢备份史与跳板。

## 1. 四阶段施工单

### 阶段 0 · Mac 侧就绪(人做,进行中)
- [x] 阿里云 22 端口放开(2026-07-28 人告知;**待澄清:全网开放 or 白名单加 IP**——若全网开放,sshd 现为 root+密码可登,须尽快关密码登录)
- [x] Mac GitHub key 已加(2026-07-28 人告知)
- [x] Mac 网络拓扑固化(2026-07-28 人告知,见 §2)
- [ ] **Mac 公钥加入 aliyun-new authorized_keys**(人发公钥我代加,或人自加)
- [ ] Mac 侧验证:`ssh root@47.103.32.81` 通 + `git clone git@github.com:qiang0723/shuheng.git` 通
- [ ] 验证通过后:关闭 aliyun-new 密码登录 + root 密码登录(先有钥匙再锁门)

### 阶段 1 · 备份链改道境内 OSS(人开资源→我施工→恢复演练验收)
- [ ] 人:开境内 OSS bucket + RAM 子账号(**仅该 bucket PutObject,无删无覆盖**,保持"备份端无删除权"防勒索姿态);AK 落 aliyun-new `/etc/shuheng/`(root 600 不进 git)
- [ ] 我:backup.sh 加密后追加推 OSS 步骤 + OSS 侧 30 份轮转(lifecycle);AWS 现存 27G 历史全量垫入 OSS
- [ ] 验收(骗不了人):连续两日推送成功 + 从 OSS 拉回密文→解密→pg_restore 演练通过
- [ ] 收尾:停用 AWS 侧 offsite_pull_aws.sh cron;文档改判(backup-chain 留档"AWS 异地"→"OSS 异地")

### 阶段 2 · 工作面迁移
- [ ] 交付包(30M)+ john-test.pem 安全迁 Mac
- [ ] Claude 记忆迁移:`~/.claude` 打包 → Mac;枢衡项目记忆目录按 Mac 新工作路径改名重挂(具体命令届时出一行清单)
- [ ] Mac 试开工:读 STATE + 查库只读核对 + 试 push,全链路走通

### 阶段 3 · 收尾与删机(人做,全部验收过才动)
- [ ] GitHub 撤销 AWS deploy key(shuheng_ops);aliyun-new authorized_keys 删 AWS 公钥;白名单删 43.212.20.35
- [ ] 文档终改判:STATE/ops 文档中 AWS 侧描述显式作废
- [ ] **最后删机**

## 2. Mac Pro 网络拓扑(人 2026-07-28 固化)

- 海外(Codex/GitHub/论文):macOS 系统代理 → Clash → 海外节点
- Docker 镜像:Docker Desktop 代理 → Clash
- 国内数据(tushare 等):scheduler 容器清空代理变量 + NO_PROXY/Docker bypass → ISP 国内直连(实测 2026-07-28:交易日历 8 行,461ms,HTTP/HTTPS/ALL 代理均未设置)
- 本地 Web:仅 127.0.0.1
- 未来海外采集:独立 research-overseas profile 显式走代理,不影响 scheduler
- 临时宿主机国内采集:进程级直连,不动 Clash / 系统网络

**要点:** ①SSH 阿里云走 ISP 直连(终端 ssh 不吃系统代理,Clash 国内直连),白名单对准家宽公网 IP;IP 漂移时 Mac 连不上先查这个;**绝不把 SSH 引到海外节点**(来源不稳 + 绕境外连境内库双重问题)。②GitHub 走 Clash、aliyun 走直连,部署链两段各走各路,成立。

## 3. 挂账待人裁

1. 22 端口"放开"形态澄清(全网 or 白名单)→ 决定关密码登录的紧迫度
2. OSS 方案批复 + bucket/RAM 开通(阶段 1 前置)
3. **采集端是否迁 Mac(独立裁定,本迁移不含)**:当前口径=采集在 aliyun-new(库在哪采在哪,lineage 干净);Mac scheduler 容器若将来承担 qbase 采集=经公网写库的口径变化,须人另拍
4. 老 AWS 雷达源机(43.213.181.243)去留(本迁移不含,现状=已复核备份源)

— 记录:2026-07-28;迁移进度以 ops/STATE.md 为准 —

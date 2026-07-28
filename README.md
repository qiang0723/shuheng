# 枢衡 · quant/ monorepo

新架构承载体。起步两个住户:**qbase**(L1 数据底座,公共事实 + 归一视图)与
**淘沙 taosha**(L2 事件研究引擎 + 假设台账)。部署形态:本地 Mac 工地负责开发与容器验证;
阿里云本体持有唯一生产写权限、数据库、批算与主备份。

> 权威文档见 `docs/`;各目录 `CLAUDE.md` 为该模块不可违反的红线;与速览冲突以 CLAUDE.md 为准。

## 目录

```
qbase/    CLAUDE.md — L1 数据底座(公共事实 + 归一视图),零判断零加工
taosha/   CLAUDE.md + docs/ — 事件研究引擎 + 假设台账(只证伪不优化)
docs/     设计方案 / 施工清单 / 哨兵加固 / 体系速览
```

## 铁则(架构层)

- **模块边界 = 目录边界**:`qbase/` ↔ `taosha/` 零 import,只经数据库表/视图交换。
- **compute 纯函数、零副作用**;单一职责;**单文件 ≤ 500 行**,超了就拆;公共逻辑下沉不复制。
- **跨云三铁则**:写权限只在阿里云 / 代码单向下行数据不上行 / 服务只读结果副本。
- **秘钥只住 `.env`**,不进代码不进 git(见 `.env.example`)。

## Docker 开发与部署

运行时钉死为 Python 3.14.4 与 `ops/runtime/requirements-qbase-ingest.lock`。
镜像不包含 `.env`,默认以非 root 用户运行;Compose 默认断网、只读挂载源码,用于本地确定性验证:

```bash
docker compose build tooling
docker compose run --rm tooling
docker compose run --rm tooling python -m taosha.harness.verify_high_pullback_rules
```

需要数据库的集成套件不在本地Compose注入生产凭据,只在阿里云授权环境执行。

生产数据库凭据只住阿里云 `/opt/quant/.env`。需要数据库的单次任务仅在阿里云显式运行:

```bash
docker build --pull -t shuheng-quant:$(git rev-parse --short HEAD) .
docker run --rm --network host --env-file /opt/quant/.env \
  shuheng-quant:$(git rev-parse --short HEAD) <明确授权的命令>
```

容器没有常驻服务;采集、研究运行和 persist 均为经人授权的一次性命令。

## 部署流水线(代码单向下行)

```
Mac 工地  --push-->  GitHub(qiang0723/shuheng, private, 唯一真身)  <--pull--  阿里云 /opt/quant
```

- **Mac**:改码 → Docker 验证 → `git push origin main`。
- **阿里云**:只读 deploy key,`git pull --ff-only`,从不 push、从不本地改。部署由 Mac 触发:
  `ssh aliyun-new 'cd /opt/quant && git pull --ff-only'`。
- `.env` 不在 git 内,各机自持(阿里云 `/opt/quant/.env`;哨兵秘钥 `/etc/shuheng/sentinel.env`)。

## 施工节奏

按《施工清单 v0.3》验收点串行:第一日初始化 → Q1 Entity Master → Q2 回填 →
Q3 归一视图 → 淘沙切片1/2/3。每步人验收。切片3 过 = 建设冻结。

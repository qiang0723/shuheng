# Web 静态 MVP · Docker 私有部署交付

- 完成时点：2026-08-09 22:58（UTC+8 / Asia/Shanghai）
- 权威数据快照：2026-08-09 22:14:05.537694（UTC+8）
- Docker 部署源码：`3e5c991118045f1b9491310a456db4ff988264eb`
- 镜像：`shuheng-research-web:2026-08-09`
- 镜像 ID：`sha256:b349491fd2d225ccf8a247d085e8b001a6b70c3124cc284fc8a25e9ccd44c73f`
- 镜像大小：80,789,276 字节
- 本机私有地址：<http://127.0.0.1:3000>

## 一、部署机制补正

John 原文「部署使用docker部署」已落实：Docker 是本项目当前正式部署机制。此前 Sites 私有 v1 的正式部署结论已作废；该旧版本仍保持 owner-only、非权威，不自动公开，也未在没有删除授权的情况下扩大处置。

本次只改变部署机制，不改变已经验收的 2026-08-09 权威静态快照、页面数字、实验状态或固定读法。因未指定远端主机，服务按最小权限部署在当前 Mac，只绑定 `127.0.0.1:3000`，不开放局域网或公网。

## 二、构建与供应链

Web 采用独立多阶段镜像：

- 基础镜像精确钉定为 `node:24.14.0-bookworm-slim@sha256:d8e448a56fc63242f70026718378bd4b00f8c82e78d20eefb199224a4d8e33d8`；
- pnpm 精确为 `11.9.0`，安装使用锁文件 `--frozen-lockfile`；
- pnpm 11 的依赖构建白名单只允许 `esbuild / sharp / unrs-resolver / workerd`；
- 构建阶段依次通过源码 lint、生产 `vinext build` 与 SSR `4/4`；
- 运行镜像只携带 `dist`、vinext 生产服务器最小运行件与启动文件，不携带完整源码和开发工具链；
- 代码规模闸门通过：230 文件、34,228 行、978 函数，存量债务 20/50 未增加。

施工中保留并修正了三类启动前失败：pnpm 11 已移除旧构建脚本许可键；旧 Sites 构建钩子在部署机制改判后仍被 Vite 引用；运行服务器导入路径多一级目录。三项均在成功部署前暴露并修正，没有触库或运行研究。首次健康容器使用 `internal` Docker 网络时宿主端口未实际发布，随后移除该标志并保留回环端口绑定；没有改成公网监听。

## 三、运行安全边界

Compose 与容器实测：

- 容器用户=`node`（uid/gid 1000），非 root；
- 根文件系统只读，`/app` 写入被 `EROFS` 拒绝；仅 `/tmp` 使用 64 MiB tmpfs；
- `cap_drop=ALL`，`no-new-privileges=true`；
- `pids_limit=256`、内存 512 MiB、CPU 1.0；
- `restart=unless-stopped`，健康检查持续为 `healthy`；
- 宿主端口精确为 `127.0.0.1:3000->3000/tcp`；容器内监听 `0.0.0.0:3000` 仅属容器网络命名空间，不改变宿主回环限制。

## 四、页面与 HTTP 验收

生产容器 HTTP 读回 `/`、`/experiments/14`、`/experiments/19` 均成功，并核到以下权威标记：

- 快照日期 `2026-08-09`；
- 「十二条密封方向判断为五命中、七未命中」；
- exp14「除权缺口 / 未达统计显著」；
- exp19「分红超预期 / 未达统计显著」。

浏览器对同一 Docker 地址完成桌面 1440×1000 与手机 390×844 显示复核：首页、26 行实验台账、exp14/exp19 详情页均可读取；手机首页与台账 `scrollWidth=clientWidth=390`，无横向溢出。

## 五、运维与停止线

从仓根执行：

```bash
docker compose ps web
docker compose logs --tail=50 web
docker compose stop web
docker compose up -d web
```

当前容器保持运行。本单元零数据库写入、零在线 API、零登录功能、零研究运行、零实验状态迁移；exp18/exp21/exp23 语义硬门、exp1/exp6 冻结状态及台账 26=`6/2/16/2` 均未改变。后续远端主机、局域网/公网开放、域名、证书、登录或动态数据接入均须另令。

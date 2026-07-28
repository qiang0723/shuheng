# Docker reader DSN 最小接线修复 · 验收（2026-07-28）

## 结论

**通过，停 Fable 复核点。** 变更仅解决非 root Docker 已注入环境变量、reader却强读root 0600 `.env`的接线矛盾；未创建exp24 manifest，未读取正式收益，未正式运行或persist。

## 改动面

代码 commit：`eb5f96e`。

- `taosha.reader.view._resolve_dsn()`成为单一解析入口，优先级固定为：显式参数 → `os.environ` → `.env`文件兜底；
- 通用`ViewReader`与exp24`SoxSpilloverReader`共用该入口；
- 不打印DSN，不改变量名、`.env`权限、数据库角色或连接权限；
- 不改PAP、事件规则、统计逻辑、manifest或正式产物结构。

## 攻击fixture与零回归

- 新增四证：显式参数优先、环境变量优先且不触文件读取、文件兜底、三路均缺fail-closed；
- exp24：rules `23/23 PASS`，adapter `32/32 PASS`；
- 既有离线全家福全部通过：earnings revision、high pullback、st removal、limit open/down、holder sell、三窗、敏感性与冻结不可覆写；
- 合成e2e SHA仍为`3116ba9b74f7c53b94082c93a476df2257d7a28eae2ad1faa0665b63716a4c22`，逐字节零回归；
- `git diff --check`通过。

## 当前生产停止线

- 021已应用并完成权限/holdout验收；
- exp24仍`frozen`，PAP digest=`be26a7f4…8f27`，结果槽空；
- `study_snapshot`仍12行、max=247，无exp24研究manifest；台账`25=12/3/9/1`；
- 上一次snapshot247 recon在任何数据读取前退出，正式单跑名额未消耗；
- 生产镜像尚未基于本修复commit重建，待Fable复核通过后随接续令构建精确commit镜像，再从snapshot247 recon继续。

## 外审范围

只需核：DSN优先级实现、fixture四证、变更是否严格止于接线层；不重审exp24事件规则或统计口径。

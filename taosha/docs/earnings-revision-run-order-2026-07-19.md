# exp20 全案通过+manifest/§7 正式运行授权令(2026-07-19,人令原文即口径)

> 留痕纪律(F 条):人令留痕 commit 先于施工。本档为 2026-07-19 人令逐字原文。
> persist 不在本令授权范围。

## 人令原文(逐字)

> 外部复核闭合,exp20适配全案通过。现授权manifest与§7单次正式运行。
> 一、报告注记内嵌(随本令一次完成,不另开复核循环):
> report渲染exp20正式产物时,须自动呈现provenance注记(沿bias_statement渲染同机制,从result内注记字段消费),注记原文冻结为:
>
> 对账注记:冻结规则下可判链日为5,175,其中flat 283排除后主事件集为4,892;相对不可重放的历史参考数5,225,总差额−50,其中−38已按冻结规则归因,剩余不可归因旧口径差额−12。历史参考数生成脚本未归档,不具备复现证明资格;正式样本以冻结规则确定性实现为唯一权威。
>
> 验收断言(无例外):
>
> 上述完整注记逐字在场;
> "不可归因旧口径差额−12"与"不可重放"在场;
> "5,225已复现"精确字符串零命中。
>
> 二、manifest生成与发布:
>
> 生成前先读回所用source snapshot的ID、digest及forecast批次,确认与本次事件数据实际来源一致,读回结果入取证包;
> 绑定该源快照(--from-source-snapshot,沿exp8血缘范式);
> 走完整发布三步(权威行+qbase镜像+publication attestation),三处digest一致;
> 血缘相容校验照既有fail-closed,异常即停报人。
>
> 三、§7单次正式运行:
>
> driver逐字消费冻结engine_params,传pap_sha256_assert=e1d18dc1019d8c43563b762c3dec3cf7b4bccad1e25667721867c33bb1dd7fd5,不一致fail-closed;
> 只允许一次执行;RC非零或任一锚定/计数断言失败即停止,不自动重跑,停下报人;
> 运行后保持frozen、结果槽空、台账零写入。
>
> 四、取证(运行毕即做,停在取证点):
>
> 原始result/report/log三件+SHA256清单落盘;
> 传输前秘密扫描(13类,命中不得改原件、停下报传输方案);
> 只读回报:source snapshot前置读回记录、manifest三处digest读回、exp20 status仍为frozen,frozen_at保持冻结时的既有非空值,result_json与done_at为空、台账25行16/3/5/1、注记三条断言结果、生产git状态。
>
> 五、persist边界:
> 本令不授权persist。取证交人验收+外审复核后另下persist令。

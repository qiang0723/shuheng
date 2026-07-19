# exp20 persist 终令(人令原文留痕,2026-07-19)

> F 条留痕:本档为人下达的 exp20 persist 终令逐字留痕,先于执行 commit。
> 执行主体按本令四节边界进行;执行结果另入验收档 + STATE。

## 人令原文(逐字)

exp20 persist 终令。外部已直接核对原件,此前流通的一组错误数字(51e0e79d / manifest 122 / CAAR −0.317% / REVERSED / N_valid 4,829)系串档转述,在双方相关目录及权威留痕中零命中。以下列权威实物为准,恢复至 persist 执行。

一、前置断言(只读,任一不符立即停止,不得修补):

三件原始产物 SHA256:
/root/s20run/result_exp20.json
7cf44b41d12f4f871c5519cd787af9b81317e7fddfff51689eec7d764fd5a6f0
/root/s20run/report_exp20.txt
3b5de3c4c1ce60c84efe2f37217d2779fd304685207a5c29201137dfe29a030e
/root/s20run/run20.log
ca66f7eaec4973e2d77f7aa460c804aa7105a89974cdc8c6bbb1bb084518d78c

exp20 当前状态:
status=frozen
frozen_at非空
result_json与done_at为空
数据库pap_json canonical digest 为
e1d18dc1019d8c43563b762c3dec3cf7b4bccad1e25667721867c33bb1dd7fd5

manifest 166 权威行、qbase镜像、publication attestation三处 digest 均为:
21e9095e5d96412bf1a7194f57e4312076b3bee0436bd2982bfcca8b7a13efcd

台账共25行,分布为:
registered 16 / frozen 3 / done 5 / closed 1

result原件直接断言:
顶层唯一verdict=NOT_SIG
主窗signed CAAR=0.00698934637496006
ADJ-BMP=0.6072938553928457
effect_alignment.value=ALIGNED
N_valid=3335
主窗N=3282
manifest=166
provenance注记逐字在场
顶层之外verdict键为零

二、执行

仅走既有状态机:
ledger.start_running(20) → ledger.finish(20, result)
要求:
身份为taosha_app;
同一连接、同一事务、一次COMMIT;
result唯一来源为上述已验收原件;
入事务前再次断言verdict、manifest、事件数、N_valid与PAP digest;
零重跑、零重生成、零改写、零旁路SQL;
不新增台账行;
任一步异常必须整笔回滚并停止上报。

三、闭卷留痕三件(随 persist 写入验收档与 STATE,不写入或反向改造result_json):

密封开封对照
预判原文:"主窗[0,+4]市场调整后signed CAR为负,把握度55%",绑定PAP v2 digest e1d18dc1…7fd5。
实测signed CAAR为+0.6989346%,方向未命中;ADJ-BMP不显著,终态NOT_SIG。作为校准册第二条如实入册,预判原文不得改述。

方法限制固定
NOT_SIG仅在冻结的行业分组口径下成立;行业缺失组占6.7%,未验证其他缺失行业处理方式下的稳健性。
不得结果后修改行业分组或追加敏感性重跑。

解读边界
实测方向为正但不显著,不能认定存在沿修正方向或逆修正方向的可靠效应;
朴素t、Corrado、日历时间法的名义显著均为NOT_FOR_VERDICT,不得改读正式结论;
效力固定为llm/prescreen,不得写成full证据。

四、persist后核验

只读确认:
exp20=done
done_at非空
顶层verdict=NOT_SIG
库内result_json与原件parsed_equal=True
canonical序列化SHA双侧一致
结构及关键数值零删减、零补写
台账仍25行,分布严格为
registered 16 / frozen 2 / done 6 / closed 1
manifest 166三处digest不变
三件原始产物SHA不变
生产Git工作区干净
闭卷留痕commit已push,两台HEAD同步且工作区干净
完成后立即停工交终签。exp20不再追加复核、重跑或施工。

## 执行边界注记(执行侧确认)

- 唯一授权动作 = 既有状态机单事务 persist(exp8 先例 `/root/s8persist/` 范式);
- result 唯一来源 = `/root/s20run/result_exp20.json`(SHA `7cf44b41…`已验收原件);
- 闭卷三件写入验收档+STATE,**不写入 result_json**;
- persist 后立即停工交终签,exp20 不再追加任何复核/重跑/施工。

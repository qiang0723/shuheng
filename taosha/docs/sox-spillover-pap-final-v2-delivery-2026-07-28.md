# exp24 sox_spillover PAP v2 · B级收口交付（2026-07-28）

> 外部复核：A级0；B级1项；C级建议不扩单元。性质仍为 **NOT-FROZEN终版候选**。

## 1. B级实物核验

审核意见所指事实经qbase批13只读核验成立，精确口径为：

- `currency=''`空字符串388行（不是SQL NULL），范围2010-12-30..2012-07-13；
- 388行close全部非空；批13全体3,395行close亦零缺失；
- Nasdaq与Yahoo交易日集合3,395日完全一致；
- 2015-02-02主锚655.187、Yahoo 653.140，差2.05点，约0.031%；按A4不回改主锚。

上述两项只属NOT_FOR_VERDICT数据质量披露，不改变收益率公式、触发集合、方向、事件映射、
样本、统计或判决。

## 2. v2实物与变化边界

- v2：`taosha/docs/sox-spillover-pap-final-v2-2026-07-28.json`
- 文件SHA256 = 引擎canonical digest =
  `be26a7f43e1dca2602a4ab60931aae4db9e55781cbf1cba410dc2d4d0f738f27`
- `validate_pap` PASS；`parse_test_windows=(5,20,60)`；顶层仍为19键。
- v1→v2程序化逐键diff：顶层仅`diagnostic_dimensions`变化；其内部仅
  `data_quality_disclosure`变化。其余18个顶层键逐字相等，`diagnostic_dimensions`其余字段
  逐字相等。
- v1文件保持原样，另立NOT-FROZEN superseded标记；草案及既有交付档均不覆盖。

外审C级建议“交付档带snapshot 247完整digest”未触发改动：v1交付档§1及PAP数据锚已经记录
完整digest `4a0dbd9e93e931422584036a50d0c522108f4c1cf8b481193133c4bc9fe1f450`，
无需重复扩写。

## 3. 停止线

exp24仍应保持registered三槽空。本收口不授权冻结、研究manifest、A股事件后收益读取、
正式运行或persist。下一步为人复核v2 digest、亲拟方向与把握度预判，并另下冻结令。

"""淘沙 · engine — 执行器(含 A股清洗预处理)。

spec §5 流程:exp_id(须 frozen)→ pap → explore_reader 拉数 → A股清洗 → compute → gates
→ deflate → result_json + 体检报告。不 import 兄弟顶层目录以外的东西;唯一写入=台账。
"""

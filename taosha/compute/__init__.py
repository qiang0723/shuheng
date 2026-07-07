"""淘沙 · compute(纯函数层)。

红线(仓根/taosha CLAUDE.md):compute 为纯函数,不 import 兄弟顶层目录(qbase/radar);
唯一数据入口=qbase 归一视图(只读)。本层承载对数收益/AR/检验统计量等**无判断的算术**,
判断逻辑(事件定义/参数终值)一律来自人冻结的 PAP 与 frozen_config,一个数不改。
"""

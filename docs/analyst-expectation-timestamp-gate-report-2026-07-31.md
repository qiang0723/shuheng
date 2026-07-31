# 分析师预期类时间戳前置窄核 · 交验报告（2026-07-31，UTC+8）

## 二元结论

**时间戳口径不通过，暂停分析师预期类新假设登记。**

现有候选源只能证明“研报日期”和“数据商更新时间”，不能证明分析师预测修正的时点等于研报真实发布时点；老库还丢弃了数据商更新时间与修订历史。依据在案硬门“口径不明不登记”，本轮不得形成该类候选假设。

## 1. 在案硬门

`taosha/docs/harvest-batch2-registration-2026-07-12.md` 已登记：轮巡指针进入分析师预期类前，必须核查“修正时点是否=研报发布日；口径不明不登记”。本报告只回答这一问题，不评价任何收益或假设方向。

## 2. 官方源语义

候选接口为 Tushare `report_rc`。其[官方文档](https://tushare.pro/document/2?doc_id=292)明确区分：

- `report_date`：**研报日期**，日级字段；
- `create_time`：**TS 数据更新时间**，不是研报发布时间；
- 接口每天 19:00—22:00 更新当日数据。

官方字段中没有研报原始发布时间、首次可见时间、修订发布时间、版本号或原文 URL。`report_date` 也只被定义为“研报日期”，未被定义为真实发布时点。

## 3. 老 `research_view` 实物

只读核验对象：老 AWS 源机 `/home/ubuntu/mofangrearch`，Git HEAD=`8104508ab18c25f06f32843643a2a96051b70f7f`。相关两文件相对 HEAD 无改动：

- `src/research_view/collect/research.py` SHA256=`958e6168ad78032f762194baeee17b6f2540ba646d58c4435970fd1a9460c328`；
- `sql/009_research.sql` SHA256=`49b3c394df7998157c8cfb3ff724752830285113a75c867401737b69c83182f8`。

采集器实物行为：

1. 调用 `pro.report_rc(start_date=..., end_date=...)`；
2. 将源端 `report_date` 原样转为日级日期；
3. **未读取、未保存 `create_time`**；
4. 表内 `created_at` 由 PostgreSQL `DEFAULT now()` 生成，只是本库写入时刻；
5. `report_id=hash(ts_code|report_date|org_name|report_title)`；相同身份再次出现时，`ON CONFLICT` 仅更新 `scope/industry`，不会保留或更新预测数值的修订版本。

表结构只有 `report_date date` 与 `created_at timestamptz` 两个时间字段，没有源端发布时间、数据商更新时间、版本号、修订标记或原文锚。

## 4. 备份样本的判别力

只读流式解析阿里云 `/root/recovery_drill/research_view_20260706.dump` 的 `research_report`，零恢复、零落库：

| 项 | 实测 |
|---|---:|
| 行数 | 479 |
| `report_date` 日期数 | 35 |
| `report_date` 范围 | 2026-06-01..2026-07-05 |
| `created_at` 日期数 | 4 |
| `created_at` 范围 | 2026-07-01 21:03:06+08..2026-07-05 23:00:29+08 |
| `created_at` 在 2026-07-01 的行数 | 437 |
| 两字段同历日 | 17 |
| 两字段不同历日 | 462 |

这直接证明 `created_at` 是批量回填/采集时刻，不能作为研报发布日。最新源仓采集器仍保持上述实现，相关文件相对 HEAD 干净；因此该结论不是旧备份的偶然现象。

## 5. 停止线与后续输入

- 分析师预期类本轮**不登记**，不生成 PAP，不进入排产；
- 不使用 `created_at`、`create_time` 或 Tushare 晚间更新时间代理研报发布时间；
- 不顺手建设新研报信源、原文抓取或修订历史数据线；
- 2026-08-02 收割会只需据此决定轮巡是否转向公司公告类题源；该决定仍归 John，不由施工方代拍；
- 2026-08-04 第 21 天检查点保留，只决定一个后续主单元。

## 6. 边界实录

全程仅只读：仓内文档/代码、阿里云备份流、老 AWS 源仓代码与官方文档。零数据库写入、零备份恢复、零采集落库、零假设登记、零 PAP、零冻结、零 manifest、零收益读取、零研究运行、零 persist。

# 当前台账只读读回

执行时间：2026-08-12 08:32:43 +0800（Asia/Shanghai）。

连接边界：SSH 进入阿里云后，以 `PGOPTIONS="-c default_transaction_read_only=on"` 连接 `TAOSHA_APP_DSN`；查询首项执行 `SHOW transaction_read_only`，结果为 `on`。未执行任何写入语句。

## 查询

```sql
SHOW transaction_read_only;
SELECT status, count(*) FROM experiment GROUP BY status ORDER BY status;
SELECT count(*) FROM experiment
WHERE status = 'done' AND family <> 'synthetic_smoke';
SELECT exp_id, status FROM experiment
WHERE exp_id IN (18, 21, 22, 23) ORDER BY exp_id;
SELECT max(done_at) FROM experiment WHERE status = 'done';
```

## 原始读回

```text
on
closed|2
done|16
frozen|2
registered|6
15
18|registered
21|registered
22|registered
23|registered
2026-08-09 20:23:00.81951+08
```

## 限域解释

- 台账仍为 26 行：registered 6 / frozen 2 / done 16 / closed 2；
- 剔除 exp7 `synthetic_smoke` 后，正式真实 `done` 为 15；
- exp18 / exp21 / exp22 / exp23 均仍为 `registered`，本读回只核状态，不替代各自证据硬门档；
- 最新 `done_at` 仍是 exp14 于 2026-08-09 的 persist，故已外审 Web 结果快照在正式结果集合上没有增量。

\set ON_ERROR_STOP on
\pset tuples_only on
\pset format unaligned
\pset fieldsep '|'

SHOW transaction_read_only;

SELECT 'SNAPSHOT_TIME', to_char(clock_timestamp() AT TIME ZONE 'Asia/Shanghai', 'YYYY-MM-DD HH24:MI:SS.US');

SELECT
    'LEDGER',
    exp_id,
    family,
    status,
    source_type,
    verdict_power,
    family_trial,
    COALESCE(result_json->>'verdict', ''),
    COALESCE(to_char(done_at AT TIME ZONE 'Asia/Shanghai', 'YYYY-MM-DD HH24:MI:SS.US'), '')
FROM experiment
ORDER BY exp_id;

SELECT
    'METRIC',
    exp_id,
    result_json->>'verdict',
    result_json->>'n_events_total',
    result_json->>'n_valid',
    result_json#>>'{car,main_window,n}',
    result_json#>>'{car,main_window,caar}',
    result_json#>>'{car,main_window,adj_bmp_car}',
    result_json#>>'{n_eff_rho,rho_bar}',
    result_json#>>'{n_eff_rho,kish}',
    result_json#>>'{n_eff_rho,kp}',
    result_json#>>'{rejections,reject_ratio}',
    result_json#>>'{industry_coverage,unknown_pct}'
FROM experiment
WHERE exp_id IN (8, 10, 11, 12, 13, 14, 16, 17, 19, 20, 24, 568)
ORDER BY done_at;

SELECT 'STATUS', status, count(*)
FROM experiment
GROUP BY status
ORDER BY status;

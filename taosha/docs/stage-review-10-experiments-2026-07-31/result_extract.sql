-- Read-only stage-review extract, executed 2026-07-31 UTC+8 against taosha.
SET default_transaction_read_only=on;

SELECT
    exp_id,
    family,
    source_type,
    verdict_power,
    family_trial,
    result_json->>'verdict' AS verdict,
    result_json->>'n_events_total' AS n_events,
    result_json->>'n_valid' AS n_valid,
    result_json#>>'{car,main_window,n}' AS main_n,
    result_json#>>'{car,main_window,caar}' AS caar,
    result_json#>>'{car,main_window,adj_bmp_car}' AS adj_bmp,
    result_json#>>'{n_eff_rho,rho_bar}' AS rho_bar,
    result_json#>>'{n_eff_rho,kish}' AS kish_n_eff,
    result_json#>>'{n_eff_rho,kp}' AS kp_n_eff,
    result_json#>>'{rejections,reject_ratio}' AS reject_ratio,
    result_json#>>'{industry_coverage,unknown_pct}' AS industry_unknown_pct
FROM experiment
WHERE exp_id IN (8,10,11,12,13,16,17,20,24,568)
ORDER BY done_at;

SELECT status, count(*)
FROM experiment
GROUP BY status
ORDER BY status;

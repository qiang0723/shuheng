#!/usr/bin/env Rscript
# 对台参照侧:estudy2 0.10.0 跑合成 fixture,dump 收益/AR/BMP/系数,供 Python 侧逐点比对。
# 用法: Rscript estudy2_ref.R <prices.csv> <meta.json> <out_dir>
suppressMessages({ library(estudy2); library(jsonlite) })

args <- commandArgs(trailingOnly = TRUE)
prices_path <- args[1]; meta_path <- args[2]; out_dir <- args[3]
meta <- jsonlite::fromJSON(meta_path)

# 读价格:空串=NA;date 转 Date
prices <- read.csv(prices_path, na.strings = c("", "NA"), stringsAsFactors = FALSE)
prices$date <- as.Date(prices$date)

# 1) 对数收益(multi_day=TRUE, continuous)——全列一起,再拆市场/证券
rates_all <- get_rates_from_prices(prices, quote = "Close",
                                   multi_day = TRUE, compounding = "continuous")
sec_names <- setdiff(colnames(prices), c("date", "MKT"))
rates_secs <- rates_all[, c("date", sec_names)]
rates_mkt  <- rates_all[, c("date", "MKT")]

est_start <- as.Date(meta$date_est_start); est_end <- as.Date(meta$date_est_end)
ev_start  <- as.Date(meta$date_event_start); ev_end <- as.Date(meta$date_event_end)

# 2) SIM 市场模型(OLS),同一市场 regressor
sr <- apply_market_model(rates = rates_secs, regressors = rates_mkt,
                         same_regressor_for_all = TRUE,
                         market_model = "sim", estimation_method = "ols",
                         estimation_start = est_start, estimation_end = est_end)

# 3) BMP(boehmer)
bmp <- boehmer(sr, event_start = ev_start, event_end = ev_end)

# ── dump ─────────────────────────────────────────────────────────────────────
dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)
# 收益序列(item 3 跨缺口对齐比对)
write.csv(rates_all, file.path(out_dir, "rates_estudy2.csv"), row.names = FALSE)

# 每证券 α/β + 事件窗 AR
coef_rows <- list(); ar_rows <- list()
for (i in seq_along(sr)) {
  s <- sec_names[i]
  co <- sr[[i]]$coefficients
  coef_rows[[i]] <- data.frame(security = s, alpha = unname(co[1]),
                               beta = unname(co[2]), delta = sr[[i]]$estimation_length)
  ab <- sr[[i]]$abnormal
  ab_ev <- ab[zoo::index(ab) >= ev_start & zoo::index(ab) <= ev_end]
  ar_rows[[i]] <- data.frame(security = s,
                             date = as.character(zoo::index(ab_ev)),
                             abnormal = as.numeric(zoo::coredata(ab_ev)))
}
write.csv(do.call(rbind, coef_rows), file.path(out_dir, "coef_estudy2.csv"), row.names = FALSE)
write.csv(do.call(rbind, ar_rows), file.path(out_dir, "abnormal_estudy2.csv"), row.names = FALSE)
# BMP 表(date, bh_stat)
write.csv(bmp[, c("date", "mean", "bh_stat")], file.path(out_dir, "bmp_estudy2.csv"),
          row.names = FALSE)

cat("estudy2 参照 dump 完成 →", out_dir, "\n")
cat("BMP@event:\n"); print(bmp[, c("date", "mean", "bh_stat", "bh_signif")])

#!/usr/bin/env Rscript
# =============================================================================
# ols_smoke.R — deterministic OLS contract smoke (v0.2 P0)
#
# Usage:
#   Rscript ols_smoke.R <input.csv> <outdir> [--skip-summary]
#
# Input CSV contract (produced by scripts/smoke_python_r.py):
#   columns: y,x1,x2  (numeric; first row = header)
# Fits y ~ x1 + x2 with base lm() and writes the standard MMKit outputs
# (coefficients.csv / predictions.csv / metrics.csv / model_summary.txt /
#  run_metadata.json) through io_contract.R. Requires ONLY base R.
# =============================================================================

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) {
  cat("usage: Rscript ols_smoke.R <input.csv> <outdir>\n")
  quit(save = "no", status = 2L)
}
input_path <- args[1]
outdir <- args[2]

src_dir <- tryCatch(dirname(normalizePath(sub("^--file=", "", grep("--file=", commandArgs(), value = TRUE)))),
                    error = function(e) NULL)
if (is.null(src_dir)) src_dir <- dirname(normalizePath(commandArgs()[1]))
source(file.path(src_dir, "io_contract.R"))

if (!file.exists(input_path)) {
  cat(paste0("ERROR: input CSV not found: ", input_path, "\n"))
  quit(save = "no", status = 1L)
}

data <- read.csv(input_path, stringsAsFactors = FALSE, check.names = TRUE)
need <- c("y", "x1", "x2")
if (!all(need %in% colnames(data))) {
  cat(paste0("ERROR: input CSV must contain columns: ", paste(need, collapse = ","),
             "; found: ", paste(colnames(data), collapse = ","), "\n"))
  quit(save = "no", status = 1L)
}

set.seed(20260910L)  # irrelevant for lm() but keeps any stochastic helper stable
fit <- lm(y ~ x1 + x2, data = data)
s <- summary(fit)

# ---- coefficients ------------------------------------------------------------
coef_mat <- s$coefficients
coefficients_df <- data.frame(
  term      = rownames(coef_mat),
  estimate  = as.numeric(coef_mat[, "Estimate"]),
  std_error = as.numeric(coef_mat[, "Std. Error"]),
  statistic = as.numeric(coef_mat[, "t value"]),
  p_value   = as.numeric(coef_mat[, "Pr(>|t|)"])
)
rownames(coefficients_df) <- NULL

# ---- predictions ---------------------------------------------------------------
pred <- as.numeric(predict(fit))
predictions_df <- data.frame(
  index     = seq_len(nrow(data)),
  observed  = as.numeric(data$y),
  predicted = pred,
  residual  = as.numeric(data$y) - pred
)

# ---- metrics -------------------------------------------------------------------
resid <- predictions_df$residual
metrics_df <- data.frame(
  metric = c("n_obs", "r_squared", "adj_r_squared", "rmse", "mae", "a_conditional"),
  value  = c(nrow(data), as.numeric(s$r.squared), as.numeric(s$adj.r.squared),
             sqrt(mean(resid^2)), mean(abs(resid)), NA_real_)
)

# ---- summary text ---------------------------------------------------------------
summary_txt <- capture.output({
  cat("MMKit OLS smoke summary\n")
  cat(paste0("call: ", deparse(fit$call), "\n"))
  print(s)
  cat(paste0("\nrmse = ", sprintf("%.17g", sqrt(mean(resid^2))), "\n"))
  cat(paste0("mae  = ", sprintf("%.17g", mean(abs(resid))), "\n"))
})

meta_extra <- list(
  script = "r_toolbox/ols_smoke.R",
  input_file = input_path,
  model_type = "lm",
  formula = "y ~ x1 + x2"
)

out <- mmkit_write_std_outputs(
  res = list(coefficients = coefficients_df,
             predictions  = predictions_df,
             metrics      = metrics_df,
             summary      = summary_txt),
  outdir = outdir,
  input_sha256 = mmkit_sha256_file(input_path),
  arguments = args,
  exit_status = 0L,
  extra_meta = meta_extra
)

cat(paste0("OLS_FIT_COMPLETE\n"))
cat(paste0("OUTPUT_DIR=", normalizePath(outdir), "\n"))
cat(paste0("N_OBS=", nrow(data), "\n"))
cat(paste0("R_SQUARED=", sprintf("%.10f", s$r.squared), "\n"))
quit(save = "no", status = 0L)

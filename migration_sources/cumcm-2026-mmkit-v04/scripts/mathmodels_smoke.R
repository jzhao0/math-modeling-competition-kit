#!/usr/bin/env Rscript

# Bounded host-qualification smoke for the teacher-developed mathmodels package.
# This does NOT recompute or replace frozen Drill-03 scientific results.

options(warn = 1)

expected_version <- "0.0.13"
expected_sha <- "13adbe0ac1716c4f07c841f45040010e71109540"

fail <- function(msg) {
  cat("STATUS=FAIL\n")
  cat("REASON=", msg, "\n", sep = "")
  quit(status = 1, save = "no")
}

if (!requireNamespace("mathmodels", quietly = TRUE)) {
  fail("mathmodels is not installed")
}

pd <- utils::packageDescription("mathmodels")
version <- as.character(utils::packageVersion("mathmodels"))
remote_sha <- if (!is.null(pd$RemoteSha)) as.character(pd$RemoteSha) else ""

if (!identical(version, expected_version)) {
  fail(sprintf("mathmodels version mismatch: expected %s, got %s", expected_version, version))
}

# A GitHub installation made by remotes normally preserves RemoteSha. Treat a
# present-but-wrong SHA as a hard failure. If the field is absent, report it so
# the setup wrapper can decide whether to reinstall the exact pin.
if (nzchar(remote_sha) && !identical(remote_sha, expected_sha)) {
  fail(sprintf("mathmodels RemoteSha mismatch: expected %s, got %s", expected_sha, remote_sha))
}

suppressPackageStartupMessages(library(mathmodels))

# 1) AHP — README-compatible deterministic example.
A <- matrix(c(
  1,   1/2, 4,   3,   3,
  2,   1,   7,   5,   5,
  1/4, 1/7, 1,   1/2, 1/3,
  1/3, 1/5, 2,   1,   1,
  1/3, 1/5, 3,   1,   1
), byrow = TRUE, nrow = 5)
ahp <- AHP(A)
if (is.null(ahp)) fail("AHP returned NULL")

# 2) Time-series route — fast ETS fit + three-step forecast.
ts_x <- as_ts_df(log(AirPassengers))
ets_fit <- ts_ets(ts_x)
ets_fc <- ts_forecast(ets_fit, h = 3)
if (!is.data.frame(ets_fc) || nrow(ets_fc) != 3 || !"forecast" %in% names(ets_fc)) {
  fail("ETS/forecast smoke returned an unexpected object")
}
if (any(!is.finite(ets_fc$forecast))) fail("ETS forecast contains non-finite values")

# 3) Statistical inference — documented two-sample example.
tt <- stat_t_test(sleep, .cols = extra, group = group)
if (!is.data.frame(tt) || nrow(tt) < 1 || !all(c("statistic", "p.value", "effect") %in% names(tt))) {
  fail("stat_t_test smoke returned an unexpected object")
}

# 4) Multivariate statistics — PCA using documented mtcars columns.
pca <- mv_pca(mtcars, cyl:carb)
if (is.null(pca) || is.null(pca$scores) || is.null(pca$loadings)) {
  fail("mv_pca smoke returned an unexpected object")
}

cat("=== MMKIT MATHMODELS SMOKE ===\n")
cat("STATUS=PASS\n")
cat("MATHMODELS_VERSION=", version, "\n", sep = "")
cat("EXPECTED_PIN=", expected_sha, "\n", sep = "")
cat("REMOTE_SHA=", if (nzchar(remote_sha)) remote_sha else "UNRECORDED", "\n", sep = "")
cat("AHP=PASS\n")
cat("ETS_FORECAST=PASS\n")
cat("STAT_INFER=PASS\n")
cat("MV_PCA=PASS\n")
cat("SCIENCE_MUTATION=NO\n")
cat("NEXT=MATHMODELS_RUNTIME_QUALIFIED\n")

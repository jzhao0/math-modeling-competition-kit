#!/usr/bin/env Rscript
# =============================================================================
# bootstrap.R — MMKit R toolbox bootstrap / ENVIRONMENT REPORT (v0.2 P0)
#
# Usage:
#   Rscript bootstrap.R                   # full availability report (load test)
#   Rscript bootstrap.R --smoke           # lightweight: presence check only
#   Rscript bootstrap.R --json <path>     # also write a JSON machine report
#
# Contract:
#   * prints R.version.string
#   * reports renv install/availability state
#   * reports package availability (never installs anything)
#   * absence of a package is a REPORTABLE STATE, not an error (exit code 0)
#   * exit 0: report completed (regardless of missing packages)
#   * exit 2: usage error; exit 1: fatal runtime error
# =============================================================================

args <- commandArgs(trailingOnly = TRUE)
smoke_mode <- "--smoke" %in% args
json_out <- NULL
if ("--json" %in% args) {
  i <- match("--json", args)
  if (length(args) < i + 1L) stop("usage: --json <path>", call. = FALSE)
  json_out <- args[i + 1L]
}

TARGET_PACKAGES <- c(
  "readr", "readxl", "dplyr", "tidyr", "ggplot2", "broom", "renv",
  "fixest", "plm", "did", "MatchIt", "quantreg", "survival", "forecast"
)

cat("============================================================\n")
cat("MMKit R toolbox bootstrap report\n")
cat(paste0("R version  : ", R.version.string, "\n"))
cat(paste0("Platform   : ", R.version$platform, "\n"))
cat(paste0("R home     : ", R.home("R"), "\n"))
cat(paste0("Mode       : ", if (smoke_mode) "smoke (presence only)" else "full (load test)"),
    "\n")
cat("============================================================\n")

# ---- renv state -------------------------------------------------------------
cat("\n[renv]\n")
renv_url <- if (nzchar(Sys.getenv("RENV_PATHS_ROOT"))) Sys.getenv("RENV_PATHS_ROOT") else "(library default)"
cat(paste0("renv installed : ", requireNamespace("renv", quietly = TRUE), "\n"))
cat(paste0("renv library root hint : ", renv_url, "\n"))
if (requireNamespace("renv", quietly = TRUE)) {
  cat(paste0("renv version   : ", as.character(utils::packageVersion("renv")), "\n"))
  cat(paste0("renv project   : ",
             tryCatch(paste0(renv::project()), error = function(e) "(none; manual)"), "\n"))
}
cat('installability : use install.packages("renv") / renv::init() yourself if needed\n')
cat("action         : NO AUTO-INSTALL performed (manual decision required)\n")

# ---- target package registry -------------------------------------------------
cat("\n[packages]\n")
pkgs <- data.frame(package = TARGET_PACKAGES,
                   installed = NA, loadable = NA, version = NA,
                   stringsAsFactors = FALSE)
for (i in seq_along(TARGET_PACKAGES)) {
  pkg <- TARGET_PACKAGES[i]
  if (smoke_mode) {
    # presence only: find.package does not load the package
    present <- !is.na(tryCatch(find.package(pkg, quiet = TRUE)[1], error = function(e) NA_character_))
    loadable <- NA
  } else {
    # load test: requireNamespace loads and imports namespace when installed
    present <- requireNamespace(pkg, quietly = TRUE)
    loadable <- present
  }
  ver <- NA_character_
  if (present && !is.na(loadable)) {
    ver <- tryCatch(as.character(utils::packageVersion(pkg)), error = function(e) NA_character_)
  } else if (present) {
    ver <- "(installed; not load-tested)"
  }
  pkgs$installed[i] <- present
  pkgs$loadable[i] <- if (is.na(loadable)) "" else loadable
  pkgs$version[i] <- ver
  cat(sprintf("  %-10s installed=%s loadable=%s version=%s\n",
              pkg, pkgs$installed[i], ifelse(is.na(pkgs$loadable[i]), "-", pkgs$loadable[i]),
              ifelse(is.na(ver), "-", ver)))
}
cat("\n")

missing_report <- pkgs$package[!pkgs$installed]
n_miss <- length(missing_report)
cat(paste0("SUMMARY : ", n_miss, " target package(s) absent (reportable state; no action taken).\n"))
if (n_miss > 0) {
  cat("  absent: ", paste(missing_report, collapse = ", "), "\n", sep = "")
  cat("  manual install example (choose mirrors yourself):\n")
  cat('    install.packages(c("', paste(missing_report, collapse = '", "'),
      '"), repos = "https://cloud.r-project.org")\n', sep = "")
}

# ---- machine-readable JSON (base R only) ------------------------------------
if (!is.null(json_out)) {
  sess <- tryCatch(paste(capture.output(utils::sessionInfo()), collapse = "\n"),
                   error = function(e) "unavailable")
  esc <- function(x) {
    x <- as.character(x)
    x <- gsub('\\', '\\\\', x, fixed = TRUE)
    x <- gsub('"', '\\"', x, fixed = TRUE)
    x <- gsub('\n', '\\n', x, fixed = TRUE)
    x <- gsub('\r', '\\r', x, fixed = TRUE)
    x <- gsub('\t', '\\t', x, fixed = TRUE)
    x
  }
  lines <- c(
    "{",
    sprintf('  "bootstrap": "0.2.0",'),
    sprintf('  "r_version": "%s",', esc(R.version.string)),
    sprintf('  "platform": "%s",', esc(R.version$platform)),
    sprintf('  "mode": "%s",', if (smoke_mode) "smoke" else "full"),
    sprintf('  "renv_installed": %s,', if (requireNamespace("renv", quietly = TRUE)) "true" else "false"),
    sprintf('  "packages": ['),
    paste(vapply(seq_len(nrow(pkgs)), function(i) {
      sprintf('    {"package": "%s", "installed": %s, "version": "%s"}',
              esc(pkgs$package[i]), tolower(pkgs$installed[i]), esc(pkgs$version[i]))
    }, character(1)), collapse = ",\n"),
    "  ],",
    sprintf('  "timestamp": "%s",', esc(format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC"))),
    sprintf('  "session_info": "%s"', esc(sess)),
    "}"
  )
  dir.create(dirname(json_out), showWarnings = FALSE, recursive = TRUE)
  writeLines(lines, con = json_out, useBytes = TRUE)
  cat(paste0("JSON report written: ", normalizePath(json_out), "\n"))
}
cat("BOOTSTRAP_REPORT_COMPLETE\n")
quit(save = "no", status = 0L)

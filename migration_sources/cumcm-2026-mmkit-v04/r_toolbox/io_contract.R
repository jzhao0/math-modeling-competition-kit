# =============================================================================
# io_contract.R — MMKit standard R output contract (v0.2 P0)
# Sourced by runner scripts. Every MMKit R analysis writes EXACTLY these
# standard outputs into one output directory:
#   coefficients.csv  metrics.csv  predictions.csv  model_summary.txt  run_metadata.json
# Nothing here installs packages. JSON fallback needs ONLY base R.
# =============================================================================

MMKIT_CONTRACT_VERSION <- "0.2.0"

# --- timestamps (UTC, ISO-8601) ----------------------------------------------
mmkit_timestamp_utc <- function() {
  format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC")
}

# --- minimal JSON helpers (base-R only) --------------------------------------
# Escape order (fixed=TRUE literal substitutions, all required by JSON):
#   1. backslash -> \\\\     (must run FIRST so later inserted backslashes are safe)
#   2. "         -> \\"
#   3. newline   -> \\n
#   4. CR        -> \\r
#   5. tab       -> \\t
.mmkit_json_escape <- function(x) {
  x <- gsub('\\', '\\\\', x, fixed = TRUE)
  x <- gsub('"', '\\"', x, fixed = TRUE)
  x <- gsub('\n', '\\n', x, fixed = TRUE)
  x <- gsub('\r', '\\r', x, fixed = TRUE)
  x <- gsub('\t', '\\t', x, fixed = TRUE)
  x
}

# ---- SHA256 of a file (prefers digest; falls back to Windows certutil) ------
mmkit_sha256_file <- function(path) {
  if (!file.exists(path)) return(NA_character_)
  if (requireNamespace("digest", quietly = TRUE)) {
    return(tryCatch(digest::digest(file = path, algo = "sha256"),
                    error = function(e) NA_character_))
  }
  if (.Platform$OS.type == "windows") {
    res <- tryCatch(system2("certutil", c("-hashfile", path, "SHA256"),
                            stdout = TRUE, stderr = TRUE),
                    error = function(e) NULL)
    if (!is.null(res)) {
      hit <- grep("^[0-9a-fA-F]{64}$", res)[1]
      if (!is.na(hit)) return(tolower(gsub("[^0-9a-fA-F]", "", res[hit])))
    }
  }
  warning("SHA256 unavailable (digest package absent and no certutil); input_sha256 left null.")
  NA_character_
}

# ---- standard metadata builder ----------------------------------------------
mmkit_make_run_metadata <- function(input_sha256 = NA_character_,
                                    arguments = character(0),
                                    exit_status = 0L,
                                    extra = list()) {
  # NOTE: utils::packageStatus() requires an Internet-configured CRAN mirror and
  # throws "trying to use CRAN without setting a mirror" on a fresh install.
  # utils::installed.packages() is base R, offline, and returns the same
  # Package/Version inventory; fallback string kept for schema stability.
  pkg_txt <- tryCatch({
    pkgs <- utils::installed.packages()
    if (is.data.frame(pkgs) && nrow(pkgs) > 0L &&
        all(c("Package", "Version") %in% colnames(pkgs))) {
      ord <- order(pkgs$Package)
      paste(sprintf("%s|%s", pkgs$Package[ord], pkgs$Version[ord]), collapse = "; ")
    } else {
      "base-r-version-only"
    }
  }, error = function(e) "base-r-version-only")
  sess <- tryCatch(paste(capture.output(utils::sessionInfo()), collapse = "\n"),
                   error = function(e) "sessionInfo unavailable")
  meta <- c(list(
    contract_version = MMKIT_CONTRACT_VERSION,
    r_version = as.character(R.version.string),
    r_platform = as.character(R.version$platform),
    input_sha256 = ifelse(is.na(input_sha256), "null", input_sha256),
    arguments = paste(arguments, collapse = " "),
    timestamp = mmkit_timestamp_utc(),
    exit_status = as.character(exit_status),
    package_status = pkg_txt,
    session_info = sess
  ), extra)
  meta
}

.mmkit_json_scalar <- function(v) {
  if (is.numeric(v) && length(v) == 1 && is.finite(v)) {
    s <- format(v, digits = 17, scientific = FALSE, trim = TRUE)
    if (grepl("[^0-9eE.+-]", s)) return(sprintf('"%s"', .mmkit_json_escape(s)))
    return(s)
  }
  if (is.logical(v) && length(v) == 1) return(if (v) "true" else "false")
  if (length(v) != 1) v <- paste(as.character(v), collapse = " | ")
  sprintf('"%s"', .mmkit_json_escape(as.character(v)))
}

mmkit_write_run_metadata <- function(meta, path) {
  if (requireNamespace("jsonlite", quietly = TRUE)) {
    jsonlite::write_json(meta, path, pretty = TRUE, auto_unbox = TRUE)
  } else {
    keys <- names(meta)
    entries <- vapply(seq_along(meta),
                      function(i) sprintf('  "%s": %s', .mmkit_json_escape(keys[i]),
                                          .mmkit_json_scalar(meta[[i]])),
                      character(1))
    writeLines(c("{", paste(entries, collapse = ",\n"), "}"), con = path, useBytes = TRUE)
  }
  invisible(path)
}

# ---- standard output writer --------------------------------------------------
# res must be a list with:
#   coefficients : data.frame(term, estimate, std_error, statistic, p_value)
#   predictions  : data.frame(index, observed, predicted, residual)
#   metrics      : data.frame(metric, value)
#   summary      : character vector (model summary text)
mmkit_write_std_outputs <- function(res, outdir, input_sha256 = NA_character_,
                                    arguments = character(0), exit_status = 0L,
                                    extra_meta = list()) {
  dir.create(outdir, showWarnings = FALSE, recursive = TRUE)
  old_digits <- getOption("digits"); options(digits = 17)
  on.exit(options(digits = old_digits), add = TRUE)
  old_scipen <- getOption("scipen"); options(scipen = 999)

  stopifnot(is.data.frame(res$coefficients), is.data.frame(res$predictions),
            is.data.frame(res$metrics))
  write.csv(res$coefficients, file.path(outdir, "coefficients.csv"),
            row.names = FALSE, quote = TRUE, fileEncoding = "UTF-8")
  write.csv(res$predictions, file.path(outdir, "predictions.csv"),
            row.names = FALSE, quote = TRUE, fileEncoding = "UTF-8")
  write.csv(res$metrics, file.path(outdir, "metrics.csv"),
            row.names = FALSE, quote = TRUE, fileEncoding = "UTF-8")

  txt <- paste(res$summary, collapse = "\n")
  writeLines(txt, file.path(outdir, "model_summary.txt"), useBytes = TRUE)

  meta <- mmkit_make_run_metadata(input_sha256 = input_sha256,
                                  arguments = arguments,
                                  exit_status = exit_status,
                                  extra = extra_meta)
  mmkit_write_run_metadata(meta, file.path(outdir, "run_metadata.json"))
  options(scipen = old_scipen)
  invisible(outdir)
}

# Reference implementation of the dashboard's statistics, written in base R.
#
# app/stats.py computes these numbers for the app. This script computes the same numbers
# independently in R, from the same data/sample.csv, with R's own t.test() for the 95%
# confidence intervals. It writes the results to tests/golden/ as one CSV per statistic and
# rate measure, with the same columns and order as the Python output.
#
# tests/test_golden.py reruns the Python statistics and checks every value against these
# files. If the two languages disagree, the test fails, so a mistake in the Python math
# cannot slip through unnoticed.
#
# Run it with `make reference` (Docker) after changing a statistic or the sample data, then
# commit the updated files in tests/golden/. Every new statistic gets matching code here.

cases <- read.csv("data/sample.csv", stringsAsFactors = FALSE, na.strings = "")
cases$function_gain <- cases$function_post - cases$function_pre
rate_measures <- c("complication", "readmit_30d")

mean_ci <- function(values) {
  x <- values[!is.na(values)]
  n <- length(x)
  if (n == 0) {
    return(c(n = 0, mean = NA, low = NA, high = NA))
  }
  if (n < 2) {
    return(c(n = n, mean = mean(x), low = NA, high = NA))
  }
  ci <- t.test(x)$conf.int
  c(n = n, mean = mean(x), low = ci[1], high = ci[2])
}

rate <- function(values) {
  x <- values[!is.na(values)]
  c(n = length(x), rate = if (length(x) > 0) mean(x) else NA)
}

headline <- function(df, rate_col) {
  data.frame(
    cases = nrow(df),
    cost_mean = mean_ci(df$total_cost)[["mean"]],
    gain_mean = mean_ci(df$function_gain)[["mean"]],
    rate = rate(df[[rate_col]])[["rate"]]
  )
}

surgeon_row <- function(surgeon, df, rate_col) {
  cost <- mean_ci(df$total_cost)
  gain <- mean_ci(df$function_gain)
  r <- rate(df[[rate_col]])
  data.frame(
    surgeon = surgeon,
    cases = nrow(df),
    cost_n = cost[["n"]],
    cost_mean = cost[["mean"]],
    cost_low = cost[["low"]],
    cost_high = cost[["high"]],
    gain_n = gain[["n"]],
    gain_mean = gain[["mean"]],
    gain_low = gain[["low"]],
    gain_high = gain[["high"]],
    value = gain[["mean"]] / (cost[["mean"]] / 1000),
    rate_n = r[["n"]],
    rate = r[["rate"]]
  )
}

surgeon_summary <- function(df, rate_col) {
  surgeons <- unique(df$surgeon)
  surgeons <- surgeons[order(surgeons, method = "radix")]
  rows <- lapply(surgeons, function(s) surgeon_row(s, df[df$surgeon == s, ], rate_col))
  do.call(rbind, rows)
}

for (rate_col in rate_measures) {
  write.csv(
    headline(cases, rate_col),
    file.path("tests", "golden", paste0("headline_", rate_col, ".csv")),
    row.names = FALSE,
    na = "NA"
  )
  write.csv(
    surgeon_summary(cases, rate_col),
    file.path("tests", "golden", paste0("surgeon_summary_", rate_col, ".csv")),
    row.names = FALSE,
    na = "NA"
  )
}

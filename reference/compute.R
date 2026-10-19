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
rate_measures <- c("complication", "readmit_30d", "discharged_home")
readmit_outlier <- "Dr. Smith"

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

funnel <- function(df, rate_col) {
  df <- df[!is.na(df[[rate_col]]), ]
  p0 <- mean(df[[rate_col]])
  surgeons <- sort(unique(df$surgeon), method = "radix")
  rows <- lapply(surgeons, function(s) {
    x <- df[df$surgeon == s, rate_col]
    n <- length(x)
    se <- sqrt(p0 * (1 - p0) / n)
    limit <- function(z, side) min(max(p0 + side * z * se, 0), 1)
    low998 <- limit(round(qnorm(0.999), 6), -1)
    high998 <- limit(round(qnorm(0.999), 6), 1)
    data.frame(
      surgeon = s,
      n = n,
      events = sum(x),
      rate = mean(x),
      p0 = p0,
      low95 = limit(round(qnorm(0.975), 6), -1),
      high95 = limit(round(qnorm(0.975), 6), 1),
      low998 = low998,
      high998 = high998,
      flag = if (mean(x) > high998) "high" else if (mean(x) < low998) "low" else ""
    )
  })
  do.call(rbind, rows)
}

quarterly <- function(df, rate_col, surgeon) {
  df <- df[!is.na(df[[rate_col]]), ]
  date <- as.Date(df$surgery_date)
  df$quarter <- sprintf(
    "%dQ%d",
    as.integer(format(date, "%Y")),
    (as.integer(format(date, "%m")) - 1) %/% 3 + 1
  )
  quarters <- sort(unique(df$quarter), method = "radix")
  rate_in <- function(q, mine) {
    x <- df[df$quarter == q & (df$surgeon == surgeon) == mine, rate_col]
    if (length(x) > 0) mean(x) else NA
  }
  data.frame(
    quarter = quarters,
    surgeon_rate = sapply(quarters, rate_in, mine = TRUE),
    others_rate = sapply(quarters, rate_in, mine = FALSE),
    row.names = NULL
  )
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
  write.csv(
    funnel(cases, rate_col),
    file.path("tests", "golden", paste0("funnel_", rate_col, ".csv")),
    row.names = FALSE,
    na = "NA"
  )
  write.csv(
    quarterly(cases, rate_col, readmit_outlier),
    file.path("tests", "golden", paste0("quarterly_", rate_col, ".csv")),
    row.names = FALSE,
    na = "NA"
  )
}

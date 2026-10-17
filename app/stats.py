import math

import pandas as pd
from scipy import stats

from app.schema import COST, GAIN, SURGEON

NAN = math.nan
SUMMARY_COLUMNS = (
    SURGEON,
    "cases",
    "cost_n",
    "cost_mean",
    "cost_low",
    "cost_high",
    "gain_n",
    "gain_mean",
    "gain_low",
    "gain_high",
    "value",
    "rate_n",
    "rate",
)


def mean_ci(values: pd.Series) -> tuple[int, float, float, float]:
    clean = values.dropna().astype("float64")
    n = len(clean)
    if n == 0:
        return 0, NAN, NAN, NAN
    mean = float(clean.mean())
    if n < 2:
        return n, mean, NAN, NAN
    margin = stats.t.ppf(0.975, n - 1) * clean.std(ddof=1) / math.sqrt(n)
    return n, mean, mean - margin, mean + margin


def headline(df: pd.DataFrame, rate_col: str) -> dict[str, float]:
    return {
        "cases": len(df),
        "cost_mean": mean_ci(df[COST])[1],
        "gain_mean": mean_ci(df[GAIN])[1],
        "rate": _rate(df[rate_col])[1],
    }


def surgeon_summary(df: pd.DataFrame, rate_col: str) -> pd.DataFrame:
    rows = [_surgeon_row(surgeon, group, rate_col) for surgeon, group in df.groupby(SURGEON)]
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS).sort_values(SURGEON, ignore_index=True)


def _surgeon_row(surgeon: str, group: pd.DataFrame, rate_col: str) -> dict[str, object]:
    cost_n, cost_mean, cost_low, cost_high = mean_ci(group[COST])
    gain_n, gain_mean, gain_low, gain_high = mean_ci(group[GAIN])
    rate_n, rate = _rate(group[rate_col])
    return {
        SURGEON: surgeon,
        "cases": len(group),
        "cost_n": cost_n,
        "cost_mean": cost_mean,
        "cost_low": cost_low,
        "cost_high": cost_high,
        "gain_n": gain_n,
        "gain_mean": gain_mean,
        "gain_low": gain_low,
        "gain_high": gain_high,
        "value": gain_mean / (cost_mean / 1000),
        "rate_n": rate_n,
        "rate": rate,
    }


def _rate(values: pd.Series) -> tuple[int, float]:
    clean = values.dropna().astype("float64")
    return len(clean), float(clean.mean()) if len(clean) else NAN

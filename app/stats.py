import math

import numpy as np
import pandas as pd
from scipy import stats

from app.schema import COST, GAIN, SURGEON, SURGERY_DATE

NAN = math.nan
Z95 = 1.959964
Z998 = 3.090232
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


def limits(p0: float, n: np.ndarray | pd.Series, z: float) -> tuple[np.ndarray, np.ndarray]:
    margin = z * np.sqrt(p0 * (1 - p0) / np.asarray(n, dtype="float64"))
    return np.clip(p0 - margin, 0.0, 1.0), np.clip(p0 + margin, 0.0, 1.0)


def funnel_columns(group_col: str) -> tuple[str, ...]:
    return (group_col, "n", "events", "rate", "p0", "low95", "high95", "low998", "high998", "flag")


def funnel(df: pd.DataFrame, rate_col: str, group_col: str = SURGEON) -> pd.DataFrame:
    clean = df.dropna(subset=[rate_col])
    outcome = clean[rate_col].astype("float64")
    counts = outcome.groupby(clean[group_col]).agg(n="count", events="sum")
    table = counts.reset_index().sort_values(group_col, ignore_index=True)
    if table.empty:
        return pd.DataFrame(columns=funnel_columns(group_col))
    table["rate"] = table["events"] / table["n"]
    table["p0"] = outcome.mean()
    table["low95"], table["high95"] = limits(table["p0"].iloc[0], table["n"], Z95)
    table["low998"], table["high998"] = limits(table["p0"].iloc[0], table["n"], Z998)
    table["flag"] = np.select(
        [table["rate"] > table["high998"], table["rate"] < table["low998"]],
        ["high", "low"],
        default="",
    )
    return table[list(funnel_columns(group_col))]


def quarterly(
    df: pd.DataFrame,
    rate_col: str,
    value: str,
    group_col: str = SURGEON,
) -> pd.DataFrame:
    clean = df.dropna(subset=[rate_col])
    outcome = clean[rate_col].astype("float64")
    quarter = clean[SURGERY_DATE].dt.to_period("Q").astype(str)
    mine = clean[group_col] == value
    result = pd.DataFrame(
        {
            f"{group_col}_rate": outcome[mine].groupby(quarter[mine]).mean(),
            "others_rate": outcome[~mine].groupby(quarter[~mine]).mean(),
        }
    ).reindex(sorted(quarter.unique()))
    return result.rename_axis("quarter").reset_index()

import math

import pandas as pd

from app.charts import LOW_VOLUME
from app.schema import SURGEON

MISSING = "–"


def summary_table(summary: pd.DataFrame, rate_label: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Surgeon": [
                _surgeon(s, n) for s, n in zip(summary[SURGEON], summary["cases"], strict=True)
            ],
            "Cases": summary["cases"],
            "Avg cost (95% CI)": _with_ci(summary, "cost", "${:,.0f}"),
            "Avg function gain (95% CI)": _with_ci(summary, "gain", "{:.1f}"),
            "Gain per $1,000": [display(v, "{:.2f}") for v in summary["value"]],
            rate_label: [display(v, "{:.1%}") for v in summary["rate"]],
        }
    )


def _surgeon(name: str, cases: int) -> str:
    return f"{name} (low volume)" if cases < LOW_VOLUME else name


def _with_ci(summary: pd.DataFrame, prefix: str, pattern: str) -> list[str]:
    return [
        _mean_ci(mean, low, high, pattern)
        for mean, low, high in zip(
            summary[f"{prefix}_mean"],
            summary[f"{prefix}_low"],
            summary[f"{prefix}_high"],
            strict=True,
        )
    ]


def _mean_ci(mean: float, low: float, high: float, pattern: str) -> str:
    if math.isnan(mean):
        return MISSING
    if math.isnan(low) or math.isnan(high):
        return f"{pattern.format(mean)} ({MISSING})"
    return f"{pattern.format(mean)} ({pattern.format(low)}–{pattern.format(high)})"


def display(value: float, pattern: str) -> str:
    return MISSING if math.isnan(value) else pattern.format(value)

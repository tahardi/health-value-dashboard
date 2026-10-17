import math

import pandas as pd
import pytest

from app.schema import SURGEON
from app.tables import summary_table

NAN = math.nan
RATE_LABEL = "Readmitted within 30 days"
HEADERS = [
    "Surgeon",
    "Cases",
    "Avg cost (95% CI)",
    "Avg function gain (95% CI)",
    "Gain per $1,000",
    RATE_LABEL,
]


def row(**changes: object) -> pd.DataFrame:
    values = {
        SURGEON: "Dr. A",
        "cases": 40,
        "cost_mean": 31250.0,
        "cost_low": 29900.0,
        "cost_high": 32600.0,
        "gain_mean": 18.4,
        "gain_low": 16.2,
        "gain_high": 20.6,
        "value": 0.5888,
        "rate": 0.125,
    }
    return pd.DataFrame([values | changes])


@pytest.mark.parametrize(
    ("summary", "expected"),
    [
        pytest.param(
            row(),
            ["Dr. A", 40, "$31,250 ($29,900–$32,600)", "18.4 (16.2–20.6)", "0.59", "12.5%"],
            id="normal",
        ),
        pytest.param(
            row(cost_low=NAN, cost_high=NAN, gain_low=NAN, gain_high=NAN),
            ["Dr. A", 40, "$31,250 (–)", "18.4 (–)", "0.59", "12.5%"],
            id="nan ci bounds",
        ),
        pytest.param(
            row(cost_mean=NAN, gain_mean=NAN, value=NAN, rate=NAN),
            ["Dr. A", 40, "–", "–", "–", "–"],
            id="nan mean",
        ),
        pytest.param(
            row(cases=8),
            [
                "Dr. A (low volume)",
                8,
                "$31,250 ($29,900–$32,600)",
                "18.4 (16.2–20.6)",
                "0.59",
                "12.5%",
            ],
            id="low volume",
        ),
    ],
)
def test_summary_table(summary: pd.DataFrame, expected: list[str]) -> None:
    # given
    label = RATE_LABEL

    # when
    table = summary_table(summary, label)

    # then
    assert list(table.columns) == HEADERS
    assert table.iloc[0].tolist() == expected

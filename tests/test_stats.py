import math

import pandas as pd
import pytest

from app.schema import COST, GAIN, SURGEON
from app.stats import headline, mean_ci, surgeon_summary

NAN = math.nan
READMIT = "readmit_30d"
SUMMARY_COLUMNS = [
    "surgeon",
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
]


def cases() -> pd.DataFrame:
    return pd.DataFrame(
        {
            SURGEON: pd.array(["Dr. A", "Dr. A", "Dr. A", "Dr. B", "Dr. B"], dtype="string"),
            COST: [1000.0, 2000.0, 3000.0, 4000.0, 6000.0],
            GAIN: [10.0, 20.0, NAN, 30.0, 50.0],
            READMIT: pd.array([True, False, False, True, True], dtype="boolean"),
        }
    )


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        pytest.param([], (0, NAN, NAN, NAN), id="empty"),
        pytest.param([5.0], (1, 5.0, NAN, NAN), id="one value"),
        pytest.param([1.0, 2.0, 3.0, 4.0], (4, 2.5, 0.4457397, 4.5542603), id="r t.test"),
        pytest.param([1.0, NAN, 3.0], (2, 2.0, -10.706205, 14.706205), id="blank dropped"),
    ],
)
def test_mean_ci(values: list[float], expected: tuple[int, float, float, float]) -> None:
    # given
    series = pd.Series(values, dtype="float64")

    # when
    result = mean_ci(series)

    # then
    assert result == pytest.approx(expected, nan_ok=True)


def test_surgeon_summary() -> None:
    # given
    df = cases()

    # when
    result = surgeon_summary(df, READMIT)

    # then
    assert list(result.columns) == SUMMARY_COLUMNS
    assert list(result["surgeon"]) == ["Dr. A", "Dr. B"]
    assert list(result["cases"]) == [3, 2]
    assert list(result["gain_n"]) == [2, 2]
    assert list(result["rate"]) == pytest.approx([1 / 3, 1.0])
    assert list(result["value"]) == pytest.approx([7.5, 8.0])


def test_headline() -> None:
    # given
    df = cases()

    # when
    result = headline(df, READMIT)

    # then
    assert result == pytest.approx(
        {"cases": 5, "cost_mean": 3200.0, "gain_mean": 27.5, "rate": 0.6}
    )

import math

import pandas as pd
import pytest

from app.schema import COST, GAIN, SURGEON, SURGERY_DATE
from app.stats import funnel, headline, mean_ci, quarterly, surgeon_summary

NAN = math.nan
READMIT = "readmit_30d"
FUNNEL_COLUMNS = [
    "surgeon",
    "n",
    "events",
    "rate",
    "p0",
    "low95",
    "high95",
    "low998",
    "high998",
    "flag",
]
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


@pytest.mark.parametrize(
    ("df", "surgeons", "counts", "gain_counts", "rates", "values"),
    [
        pytest.param(
            cases(),
            ["Dr. A", "Dr. B"],
            [3, 2],
            [2, 2],
            [1 / 3, 1.0],
            [7.5, 8.0],
            id="two surgeons",
        ),
        pytest.param(cases().iloc[:0], [], [], [], [], [], id="no cases"),
    ],
)
def test_surgeon_summary(
    df: pd.DataFrame,
    surgeons: list[str],
    counts: list[int],
    gain_counts: list[int],
    rates: list[float],
    values: list[float],
) -> None:
    # given
    rate_col = READMIT

    # when
    result = surgeon_summary(df, rate_col)

    # then
    assert list(result.columns) == SUMMARY_COLUMNS
    assert list(result["surgeon"]) == surgeons
    assert list(result["cases"]) == counts
    assert list(result["gain_n"]) == gain_counts
    assert list(result["rate"]) == pytest.approx(rates)
    assert list(result["value"]) == pytest.approx(values)


def test_headline() -> None:
    # given
    df = cases()

    # when
    result = headline(df, READMIT)

    # then
    assert result == pytest.approx(
        {"cases": 5, "cost_mean": 3200.0, "gain_mean": 27.5, "rate": 0.6}
    )


def outcomes(spec: dict[str, tuple[int, int]], blanks: dict[str, int]) -> pd.DataFrame:
    rows = []
    for surgeon, (events, n) in spec.items():
        rows += [(surgeon, i < events) for i in range(n)]
        rows += [(surgeon, None)] * blanks.get(surgeon, 0)
    return pd.DataFrame(
        {
            SURGEON: pd.array([r[0] for r in rows], dtype="string"),
            READMIT: pd.array([r[1] for r in rows], dtype="boolean"),
        }
    )


@pytest.mark.parametrize(
    ("spec", "blanks", "surgeons", "flags", "first"),
    [
        pytest.param(
            {"Dr. C": (1, 1), "Dr. B": (5, 10), "Dr. A": (0, 10)},
            {"Dr. B": 3},
            ["Dr. A", "Dr. B", "Dr. C"],
            ["", "", ""],
            (10, 0, 0.0, 2 / 7, 0.005719, 0.565709, 0.0, 0.727176),
            id="blanks dropped and lower limit clipped at 0",
        ),
        pytest.param(
            {"Dr. A": (0, 100), "Dr. B": (50, 100)},
            {},
            ["Dr. A", "Dr. B"],
            ["low", "high"],
            (100, 0, 0.0, 0.25, 0.165131, 0.334869, 0.116189, 0.383811),
            id="low and high outliers",
        ),
        pytest.param(
            {"Dr. A": (10, 10), "Dr. B": (2, 10), "Dr. C": (2, 10), "Dr. D": (2, 10)},
            {},
            ["Dr. A", "Dr. B", "Dr. C", "Dr. D"],
            ["high", "", "", ""],
            (10, 10, 1.0, 0.4, 0.096364, 0.703636, 0.0, 0.878737),
            id="small group above upper limit",
        ),
    ],
)
def test_funnel(
    spec: dict[str, tuple[int, int]],
    blanks: dict[str, int],
    surgeons: list[str],
    flags: list[str],
    first: tuple[float, ...],
) -> None:
    # given
    df = outcomes(spec, blanks)

    # when
    result = funnel(df, READMIT)

    # then
    assert list(result.columns) == FUNNEL_COLUMNS
    assert list(result["surgeon"]) == surgeons
    assert list(result["flag"]) == flags
    numbers = ["n", "events", "rate", "p0", "low95", "high95", "low998", "high998"]
    assert list(result.iloc[0][numbers]) == pytest.approx(first, abs=1e-6)


def dated() -> pd.DataFrame:
    rows = [
        ("2025-01-15", "Dr. X", True),
        ("2025-02-10", "Dr. X", False),
        ("2025-01-20", "Dr. Y", True),
        ("2025-03-30", "Dr. Z", False),
        ("2025-05-01", "Dr. Y", True),
        ("2025-08-01", "Dr. X", True),
        ("2025-09-30", "Dr. X", True),
        ("2025-08-15", "Dr. Y", None),
    ]
    return pd.DataFrame(
        {
            SURGERY_DATE: pd.to_datetime([r[0] for r in rows]),
            SURGEON: pd.array([r[1] for r in rows], dtype="string"),
            READMIT: pd.array([r[2] for r in rows], dtype="boolean"),
        }
    )


@pytest.mark.parametrize(
    ("surgeon", "quarters", "surgeon_rates", "others_rates"),
    [
        pytest.param(
            "Dr. X",
            ["2025Q1", "2025Q2", "2025Q3"],
            [0.5, NAN, 1.0],
            [0.5, 1.0, NAN],
            id="empty quarters are NaN",
        ),
        pytest.param(
            "Dr. W",
            ["2025Q1", "2025Q2", "2025Q3"],
            [NAN, NAN, NAN],
            [0.5, 1.0, 1.0],
            id="surgeon with no cases",
        ),
    ],
)
def test_quarterly(
    surgeon: str,
    quarters: list[str],
    surgeon_rates: list[float],
    others_rates: list[float],
) -> None:
    # given
    df = dated()

    # when
    result = quarterly(df, READMIT, surgeon)

    # then
    assert list(result.columns) == ["quarter", "surgeon_rate", "others_rate"]
    assert list(result["quarter"]) == quarters
    assert list(result["surgeon_rate"]) == pytest.approx(surgeon_rates, nan_ok=True)
    assert list(result["others_rate"]) == pytest.approx(others_rates, nan_ok=True)

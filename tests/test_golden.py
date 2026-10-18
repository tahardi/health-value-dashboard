from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.data import load
from app.stats import funnel, headline, quarterly, surgeon_summary
from scripts.generate_data import READMIT_OUTLIER

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = sorted((ROOT / "tests" / "golden").glob("*.csv"))
STATISTICS = {
    "headline_": lambda df, rate_col: pd.DataFrame([headline(df, rate_col)]),
    "surgeon_summary_": surgeon_summary,
    "funnel_": funnel,
    "quarterly_": lambda df, rate_col: quarterly(df, rate_col, READMIT_OUTLIER),
}


def compute(stem: str) -> pd.DataFrame:
    for prefix, statistic in STATISTICS.items():
        if stem.startswith(prefix):
            return statistic(load(ROOT / "data" / "sample.csv"), stem.removeprefix(prefix))
    raise ValueError(f"no statistic for golden file `{stem}`")


@pytest.mark.parametrize("path", GOLDEN, ids=[p.stem for p in GOLDEN])
def test_golden(path: Path) -> None:
    # given
    expected = pd.read_csv(path, keep_default_na=False, na_values=["NA"])

    # when
    actual = compute(path.stem)

    # then
    assert list(actual.columns) == list(expected.columns)
    for column in expected.columns:
        if pd.api.types.is_numeric_dtype(expected[column]):
            np.testing.assert_allclose(
                actual[column].astype("float64"),
                expected[column].astype("float64"),
                rtol=1e-9,
                equal_nan=True,
                err_msg=column,
            )
        else:
            assert list(actual[column]) == list(expected[column]), column

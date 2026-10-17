from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pytest

from app.data import load
from app.schema import COST, FUNCTION_POST, FUNCTION_PRE, SURGEON
from scripts.generate_data import HIGH_COST, HIGH_VALUE, READMIT_OUTLIER, generate

READMIT = "readmit_30d"


def same_seed(frame: pd.DataFrame, tmp_path: Path) -> bool:
    pd.testing.assert_frame_equal(frame, generate(seed=42))
    return True


def loads(frame: pd.DataFrame, tmp_path: Path) -> bool:
    path = tmp_path / "sample.csv"
    frame.to_csv(path, index=False)
    return len(load(path)) == len(frame)


def row_count(frame: pd.DataFrame, tmp_path: Path) -> bool:
    return len(frame) == 2000


def low_volume(frame: pd.DataFrame, tmp_path: Path) -> bool:
    return {1, 8, 15} <= set(frame[SURGEON].value_counts())


def blank_share(frame: pd.DataFrame, tmp_path: Path) -> bool:
    return 0.03 <= frame[FUNCTION_POST].isna().mean() <= 0.07


def readmit_outlier(frame: pd.DataFrame, tmp_path: Path) -> bool:
    rates = frame.groupby(SURGEON)[READMIT].mean()
    return rates[READMIT_OUTLIER] >= 2.5 * frame[READMIT].mean()


def high_cost(frame: pd.DataFrame, tmp_path: Path) -> bool:
    costs = frame.groupby(SURGEON)[COST].mean()
    return costs[HIGH_COST] >= 1.25 * frame[COST].mean()


def high_value(frame: pd.DataFrame, tmp_path: Path) -> bool:
    gain = frame[FUNCTION_POST] - frame[FUNCTION_PRE]
    surgeon = frame[SURGEON] == HIGH_VALUE
    cheap = frame.loc[surgeon, COST].mean() <= 0.85 * frame[COST].mean()
    return cheap and gain[surgeon].mean() > gain.mean()


def discharged_home(frame: pd.DataFrame, tmp_path: Path) -> bool:
    return "discharged_home" in frame.columns


@pytest.mark.parametrize(
    "check",
    [
        pytest.param(same_seed, id="same seed"),
        pytest.param(loads, id="loads"),
        pytest.param(row_count, id="2000 rows"),
        pytest.param(low_volume, id="low volume surgeons"),
        pytest.param(blank_share, id="blank function_post"),
        pytest.param(readmit_outlier, id="readmit outlier"),
        pytest.param(high_cost, id="high cost"),
        pytest.param(high_value, id="high value"),
        pytest.param(discharged_home, id="discharged_home"),
    ],
)
def test_generate(check: Callable[[pd.DataFrame, Path], bool], tmp_path: Path) -> None:
    # given
    seed = 42

    # when
    frame = generate(seed=seed)

    # then
    assert check(frame, tmp_path)

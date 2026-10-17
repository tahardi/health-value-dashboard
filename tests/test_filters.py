from datetime import date

import pandas as pd
import pytest

from app.filters import apply_filters
from app.schema import FACILITY, PROCEDURE, SURGERY_DATE

FRAME = pd.DataFrame(
    {
        PROCEDURE: ["Knee", "Knee", "Hip", "Hip"],
        FACILITY: ["North", "South", "North", "South"],
        SURGERY_DATE: pd.to_datetime(["2025-01-01", "2025-02-01", "2025-03-01", "2025-04-01"]),
    }
)


@pytest.mark.parametrize(
    ("selections", "start", "end", "expected"),
    [
        pytest.param({}, None, None, [0, 1, 2, 3], id="no selections"),
        pytest.param({PROCEDURE: [], FACILITY: []}, None, None, [0, 1, 2, 3], id="empty lists"),
        pytest.param({PROCEDURE: ["Knee"]}, None, None, [0, 1], id="one procedure"),
        pytest.param(
            {PROCEDURE: ["Hip"], FACILITY: ["North"]},
            None,
            None,
            [2],
            id="procedure and facility",
        ),
        pytest.param({}, date(2025, 2, 1), date(2025, 3, 1), [1, 2], id="inclusive dates"),
        pytest.param({PROCEDURE: ["Shoulder"]}, None, None, [], id="matches nothing"),
    ],
)
def test_apply_filters(
    selections: dict[str, list[str]],
    start: date | None,
    end: date | None,
    expected: list[int],
) -> None:
    # given
    frame = FRAME

    # when
    result = apply_filters(frame, selections, start, end)

    # then
    assert list(result.index) == expected
    assert list(result.columns) == list(frame.columns)

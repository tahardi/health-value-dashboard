import math

import pandas as pd
import pytest

from app.charts import value_map
from app.schema import SURGEON

NAN = math.nan
QUADRANTS = {"Better, cheaper", "Better, costlier", "Worse, cheaper", "Worse, costlier"}


def summary(surgeons: list[str], cases: list[int]) -> pd.DataFrame:
    count = len(surgeons)
    return pd.DataFrame(
        {
            SURGEON: surgeons,
            "cases": cases,
            "cost_mean": [20000.0 + 1000 * i for i in range(count)],
            "gain_mean": [15.0 + i for i in range(count)],
            "value": [0.75] * count,
        }
    )


@pytest.mark.parametrize(
    ("surgeons", "cases", "points", "opacities", "texts"),
    [
        pytest.param(
            ["Dr. A", "Dr. B", "Dr. C"],
            [5, 20, 30],
            3,
            [0.35, 0.9, 0.9],
            QUADRANTS,
            id="three surgeons",
        ),
        pytest.param(
            ["Dr. A", "Dr. B"],
            [0, 20],
            1,
            [0.9],
            QUADRANTS,
            id="zero cases not plotted",
        ),
        pytest.param([], [], 0, [], {"No cases match these filters."}, id="empty"),
    ],
)
def test_value_map(
    surgeons: list[str],
    cases: list[int],
    points: int,
    opacities: list[float],
    texts: set[str],
) -> None:
    # given
    frame = summary(surgeons, cases)

    # when
    figure = value_map(frame, 21000.0, 16.0)

    # then
    assert {a.text for a in figure.layout.annotations} == texts
    if points == 0:
        assert len(figure.data) == 0
        return
    assert len(figure.data) == 1
    assert len(figure.data[0].x) == points
    assert list(figure.data[0].marker.opacity) == opacities
    lines = {(s.type, s.x0, s.y0) for s in figure.layout.shapes}
    assert lines == {("line", 21000.0, 0), ("line", 0, 16.0)}

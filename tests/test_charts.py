import math

import pandas as pd
import pytest

from app.charts import EMPTY_MESSAGE, funnel_plot, trend_chart, value_map
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


def funnel_table(surgeons: list[str], flags: list[str]) -> pd.DataFrame:
    count = len(surgeons)
    return pd.DataFrame(
        {
            SURGEON: surgeons,
            "n": [10 * (i + 1) for i in range(count)],
            "events": [i for i in range(count)],
            "rate": [0.1 * i for i in range(count)],
            "p0": [0.2] * count,
            "low95": [0.05] * count,
            "high95": [0.35] * count,
            "low998": [0.0] * count,
            "high998": [0.45] * count,
            "flag": flags,
        }
    )


@pytest.mark.parametrize(
    ("surgeons", "flags", "labels"),
    [
        pytest.param(
            ["Dr. A", "Dr. B", "Dr. C"], ["", "", "high"], ["", "", "Dr. C"], id="flagged"
        ),
        pytest.param(["Dr. A", "Dr. B"], ["", ""], ["", ""], id="none flagged"),
    ],
)
def test_funnel_plot(surgeons: list[str], flags: list[str], labels: list[str]) -> None:
    # given
    table = funnel_table(surgeons, flags)

    # when
    figure = funnel_plot(table, 50)

    # then
    points, center, *limits = figure.data
    assert len(points.x) == len(surgeons)
    assert list(points.text) == labels
    assert len({m for m in points.marker.color}) == len(set(flags))
    assert list(center.x) == list(range(1, 51))
    assert list(center.y) == [0.2] * 50
    assert [(t.line.dash, len(t.x)) for t in limits] == [
        ("dash", 50),
        ("dash", 50),
        ("dot", 50),
        ("dot", 50),
    ]
    assert all(0.0 <= y <= 1.0 for t in limits for y in t.y)


def test_funnel_plot_empty() -> None:
    # given
    table = funnel_table([], [])

    # when
    figure = funnel_plot(table, 0)

    # then
    assert len(figure.data) == 0
    assert [a.text for a in figure.layout.annotations] == [EMPTY_MESSAGE]


@pytest.mark.parametrize(
    ("quarters", "surgeon_rates", "points"),
    [
        pytest.param(["2025Q1", "2025Q2"], [0.1, NAN], 2, id="gap quarter"),
        pytest.param([], [], 0, id="empty"),
    ],
)
def test_trend_chart(quarters: list[str], surgeon_rates: list[float], points: int) -> None:
    # given
    table = pd.DataFrame(
        {
            "quarter": quarters,
            "surgeon_rate": surgeon_rates,
            "others_rate": [0.2] * len(quarters),
        }
    )

    # when
    figure = trend_chart(table, "Dr. A")

    # then
    if points == 0:
        assert len(figure.data) == 0
        assert [a.text for a in figure.layout.annotations] == [EMPTY_MESSAGE]
        return
    assert [t.name for t in figure.data] == ["Dr. A", "Everyone else"]
    assert all(len(t.x) == points for t in figure.data)

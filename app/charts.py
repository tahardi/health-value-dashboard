import numpy as np
import pandas as pd
import plotly.graph_objects as go

from app.schema import SURGEON
from app.stats import Z95, Z998, limits

LOW_VOLUME = 10
EMPTY_MESSAGE = "No cases match these filters."
QUADRANTS = (
    ("Better, cheaper", 0.02, 0.98, "left", "top"),
    ("Better, costlier", 0.98, 0.98, "right", "top"),
    ("Worse, cheaper", 0.02, 0.02, "left", "bottom"),
    ("Worse, costlier", 0.98, 0.02, "right", "bottom"),
)
FLAG_COLORS = {"": "#636efa", "high": "#ef553b", "low": "#00cc96"}


def value_map(summary: pd.DataFrame, overall_cost: float, overall_gain: float) -> go.Figure:
    figure = go.Figure()
    figure.update_layout(
        xaxis_title="Average cost ($)",
        yaxis_title="Average function gain",
        showlegend=False,
    )
    plotted = summary[summary["cases"] > 0]
    if plotted.empty:
        figure.add_annotation(text=EMPTY_MESSAGE, showarrow=False, xref="paper", yref="paper")
        return figure
    figure.add_trace(
        go.Scatter(
            x=plotted["cost_mean"],
            y=plotted["gain_mean"],
            mode="markers",
            marker={
                "size": _sizes(plotted["cases"]),
                "opacity": [0.35 if n < LOW_VOLUME else 0.9 for n in plotted["cases"]],
            },
            hovertext=[_hover(r) for r in plotted.to_dict("records")],
            hoverinfo="text",
        )
    )
    figure.add_vline(x=overall_cost, line_dash="dash")
    figure.add_hline(y=overall_gain, line_dash="dash")
    for text, x, y, xanchor, yanchor in QUADRANTS:
        figure.add_annotation(
            text=text,
            x=x,
            y=y,
            xref="paper",
            yref="paper",
            xanchor=xanchor,
            yanchor=yanchor,
            showarrow=False,
        )
    return figure


def _sizes(cases: pd.Series) -> list[float]:
    largest = cases.max()
    return [10 + 30 * n / largest for n in cases]


def _hover(row: dict[str, object]) -> str:
    return (
        f"{row[SURGEON]}<br>Cases: {row['cases']}<br>Avg cost: ${row['cost_mean']:,.0f}"
        f"<br>Avg function gain: {row['gain_mean']:.1f}<br>Gain per $1,000: {row['value']:.2f}"
    )


def funnel_plot(table: pd.DataFrame, max_n: int) -> go.Figure:
    figure = go.Figure()
    figure.update_layout(
        xaxis_title="Cases",
        yaxis_title="Rate",
        yaxis_tickformat=".0%",
    )
    if table.empty:
        return _empty(figure)
    p0 = float(table["p0"].iloc[0])
    cases = np.arange(1, max_n + 1)
    figure.add_trace(
        go.Scatter(
            x=table["n"],
            y=table["rate"],
            mode="markers+text",
            text=[
                name if flag else ""
                for name, flag in zip(table[SURGEON], table["flag"], strict=True)
            ],
            textposition="top center",
            marker={"size": 10, "color": [FLAG_COLORS[flag] for flag in table["flag"]]},
            hovertext=[_funnel_hover(r) for r in table.to_dict("records")],
            hoverinfo="text",
            name="Surgeons",
            showlegend=False,
        )
    )
    figure.add_trace(
        go.Scatter(
            x=cases,
            y=np.full(max_n, p0),
            mode="lines",
            line={"color": "gray"},
            name="Overall rate",
        )
    )
    for z, dash, name in ((Z95, "dash", "95% limits"), (Z998, "dot", "99.8% limits")):
        for bound, values in zip(("low", "high"), limits(p0, cases, z), strict=True):
            figure.add_trace(
                go.Scatter(
                    x=cases,
                    y=values,
                    mode="lines",
                    line={"color": "gray", "dash": dash},
                    name=name,
                    legendgroup=name,
                    showlegend=bound == "low",
                )
            )
    return figure


def trend_chart(table: pd.DataFrame, surgeon: str) -> go.Figure:
    figure = go.Figure()
    figure.update_layout(
        xaxis_title="Quarter",
        yaxis_title="Rate",
        yaxis_tickformat=".0%",
    )
    if table.empty:
        return _empty(figure)
    for column, name in (("surgeon_rate", surgeon), ("others_rate", "Everyone else")):
        figure.add_trace(
            go.Scatter(x=table["quarter"], y=table[column], mode="lines+markers", name=name)
        )
    return figure


def _empty(figure: go.Figure) -> go.Figure:
    figure.add_annotation(text=EMPTY_MESSAGE, showarrow=False, xref="paper", yref="paper")
    return figure


def _funnel_hover(row: dict[str, object]) -> str:
    return (
        f"{row[SURGEON]}<br>Cases: {row['n']}<br>Events: {row['events']}<br>Rate: {row['rate']:.1%}"
    )

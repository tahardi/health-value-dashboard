import pandas as pd
import plotly.graph_objects as go

from app.schema import SURGEON

LOW_VOLUME = 10
EMPTY_MESSAGE = "No cases match these filters."
QUADRANTS = (
    ("Better, cheaper", 0.02, 0.98, "left", "top"),
    ("Better, costlier", 0.98, 0.98, "right", "top"),
    ("Worse, cheaper", 0.02, 0.02, "left", "bottom"),
    ("Worse, costlier", 0.98, 0.02, "right", "bottom"),
)


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

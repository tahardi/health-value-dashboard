from collections.abc import Callable

import pandas as pd
import plotly.graph_objects as go
from shiny import Inputs, Outputs, Session, module, reactive, ui
from shinywidgets import output_widget, render_widget

from app.charts import funnel_plot, trend_chart
from app.schema import rate_measures
from app.stats import funnel, quarterly

DEFAULT_RATE = "readmit_30d"
RATE_LABELS = {c.name: c.label for c in rate_measures()}


@module.ui
def group_ui(label: str) -> ui.Tag:
    return ui.div(
        ui.input_select(
            "rate",
            "Rate measure",
            RATE_LABELS,
            selected=DEFAULT_RATE,
        ),
        output_widget("funnel_chart"),
        ui.input_select("group", label, []),
        output_widget("trend"),
    )


@module.server
def group_server(
    input: Inputs,
    output: Outputs,
    session: Session,
    data: Callable[[], pd.DataFrame],
    group_col: str,
    others: str,
) -> None:
    @reactive.calc
    def table() -> pd.DataFrame:
        return funnel(data(), input.rate(), group_col)

    @reactive.effect
    def _update_groups() -> None:
        frame = data()
        names = [] if frame.empty else sorted(frame[group_col].dropna().unique())
        with reactive.isolate():
            current = input.group()
        ui.update_select("group", choices=names, selected=current if current in names else None)

    @render_widget
    def funnel_chart() -> go.Figure:
        result = table()
        return funnel_plot(result, int(result["n"].max()) if len(result) else 0, group_col)

    @render_widget
    def trend() -> go.Figure:
        frame = data()
        if frame.empty:
            return trend_chart(pd.DataFrame(), input.group(), others)
        result = quarterly(frame, input.rate(), input.group(), group_col)
        return trend_chart(result, input.group(), others)

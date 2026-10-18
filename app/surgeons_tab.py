from collections.abc import Callable

import pandas as pd
import plotly.graph_objects as go
from shiny import Inputs, Outputs, Session, module, reactive, ui
from shinywidgets import output_widget, render_widget

from app.charts import funnel_plot, trend_chart
from app.schema import SURGEON, rate_measures
from app.stats import funnel, quarterly

DEFAULT_RATE = "readmit_30d"
RATE_LABELS = {c.name: c.label for c in rate_measures()}


@module.ui
def surgeons_ui() -> ui.Tag:
    return ui.div(
        ui.input_select(
            "rate",
            "Rate measure",
            RATE_LABELS,
            selected=DEFAULT_RATE,
        ),
        output_widget("funnel_chart"),
        ui.input_select("surgeon", "Surgeon", []),
        output_widget("trend"),
    )


@module.server
def surgeons_server(
    input: Inputs,
    output: Outputs,
    session: Session,
    data: Callable[[], pd.DataFrame],
) -> None:
    @reactive.calc
    def table() -> pd.DataFrame:
        return funnel(data(), input.rate())

    @reactive.effect
    def _update_surgeons() -> None:
        frame = data()
        names = [] if frame.empty else sorted(frame[SURGEON].dropna().unique())
        with reactive.isolate():
            current = input.surgeon()
        ui.update_select("surgeon", choices=names, selected=current if current in names else None)

    @render_widget
    def funnel_chart() -> go.Figure:
        result = table()
        return funnel_plot(result, int(result["n"].max()) if len(result) else 0)

    @render_widget
    def trend() -> go.Figure:
        frame = data()
        if frame.empty:
            return trend_chart(pd.DataFrame(), input.surgeon())
        return trend_chart(quarterly(frame, input.rate(), input.surgeon()), input.surgeon())

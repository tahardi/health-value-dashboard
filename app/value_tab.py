from collections.abc import Callable

import pandas as pd
import plotly.graph_objects as go
from shiny import Inputs, Outputs, Session, module, reactive, render, ui
from shinywidgets import output_widget, render_widget

from app.charts import value_map
from app.schema import rate_measures
from app.stats import headline, surgeon_summary
from app.tables import display, summary_table

DEFAULT_RATE = "readmit_30d"
RATE_LABELS = {c.name: c.label for c in rate_measures()}


@module.ui
def value_ui() -> ui.Tag:
    return ui.div(
        ui.input_select(
            "rate",
            "Rate measure",
            RATE_LABELS,
            selected=DEFAULT_RATE,
        ),
        ui.layout_columns(
            ui.value_box("Cases", ui.output_text("cases")),
            ui.value_box("Avg cost", ui.output_text("cost")),
            ui.value_box("Avg function gain", ui.output_text("gain")),
            ui.value_box(ui.output_text("rate_label"), ui.output_text("rate_value")),
        ),
        output_widget("chart"),
        ui.output_data_frame("table"),
    )


@module.server
def value_server(
    input: Inputs,
    output: Outputs,
    session: Session,
    data: Callable[[], pd.DataFrame],
) -> None:
    @reactive.calc
    def numbers() -> dict[str, float]:
        return headline(data(), input.rate())

    @reactive.calc
    def summary() -> pd.DataFrame:
        return surgeon_summary(data(), input.rate())

    @render.text
    def cases() -> str:
        return f"{numbers()['cases']:,}"

    @render.text
    def cost() -> str:
        return display(numbers()["cost_mean"], "${:,.0f}")

    @render.text
    def gain() -> str:
        return display(numbers()["gain_mean"], "{:.1f}")

    @render.text
    def rate_label() -> str:
        return RATE_LABELS[input.rate()]

    @render.text
    def rate_value() -> str:
        return display(numbers()["rate"], "{:.1%}")

    @render_widget
    def chart() -> go.Figure:
        h = numbers()
        return value_map(summary(), h["cost_mean"], h["gain_mean"])

    @render.data_frame
    def table() -> render.DataGrid:
        return render.DataGrid(summary_table(summary(), RATE_LABELS[input.rate()]))

from datetime import date

import pandas as pd
from shiny import App, Inputs, Outputs, Session, reactive, ui

from app.data_tab import data_server, data_ui
from app.filters import apply_filters
from app.schema import SURGERY_DATE, Column, filters
from app.store import data_path, ensure_data, reload, sample_path
from app.value_tab import value_server, value_ui

ensure_data(data_path(), sample_path())

last_good: dict[str, pd.DataFrame | None] = {"frame": reload(data_path(), None)[0]}


@reactive.file_reader(data_path())
def state() -> tuple[pd.DataFrame | None, list[str]]:
    frame, errors = reload(data_path(), last_good["frame"])
    last_good["frame"] = frame
    return frame, errors


def choices(frame: pd.DataFrame | None, column: Column) -> list[str]:
    return [] if frame is None else sorted(frame[column.name].dropna().unique())


def span(frame: pd.DataFrame | None) -> tuple[date | None, date | None]:
    if frame is None:
        return None, None
    return frame[SURGERY_DATE].min().date(), frame[SURGERY_DATE].max().date()


def filter_bar(frame: pd.DataFrame | None) -> ui.Tag:
    first, last = span(frame)
    return ui.layout_columns(
        *[ui.input_selectize(c.name, c.label, choices(frame, c), multiple=True) for c in filters()],
        ui.input_date_range("dates", "Surgery date", start=first, end=last, min=first, max=last),
    )


app_ui = ui.page_navbar(
    ui.nav_panel("Value", value_ui("value")),
    ui.nav_panel("Data", data_ui("data")),
    title="Health Value Dashboard",
    header=filter_bar(last_good["frame"]),
)


def server(input: Inputs, output: Outputs, session: Session) -> None:
    @reactive.effect
    def _update_filters() -> None:
        frame, _ = state()
        if frame is None:
            return
        for column in filters():
            options = choices(frame, column)
            with reactive.isolate():
                selected = [v for v in input[column.name]() if v in options]
            ui.update_selectize(column.name, choices=options, selected=selected)
        first, last = span(frame)
        ui.update_date_range("dates", start=first, end=last, min=first, max=last)

    @reactive.calc
    def filtered() -> pd.DataFrame:
        frame, _ = state()
        if frame is None:
            return pd.DataFrame()
        selections = {c.name: list(input[c.name]()) for c in filters()}
        start, end = input.dates() or (None, None)
        return apply_filters(frame, selections, start, end)

    value_server("value", filtered)
    data_server("data", state, data_path())


app = App(app_ui, server)

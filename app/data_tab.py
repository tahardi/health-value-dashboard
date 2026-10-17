import os
import shutil
import tempfile
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import pandas as pd
from shiny import Inputs, Outputs, Session, module, reactive, render, ui

from app.data import DataError, load
from app.schema import COLUMNS, SURGERY_DATE
from app.store import sample_path

STALE = "The data file has problems. The dashboard is still showing the last good data."


def replace_data(upload: Path, target: Path) -> list[str]:
    try:
        load(upload)
    except DataError as err:
        return err.errors
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as temp:
        with upload.open("rb") as source:
            shutil.copyfileobj(source, temp)
    os.replace(temp.name, target)
    return []


def schema_table() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Column": [c.name for c in COLUMNS],
            "Label": [c.label for c in COLUMNS],
            "Type": [str(c.kind) for c in COLUMNS],
            "Role": [str(c.role) for c in COLUMNS],
            "Filter": ["yes" if c.filter else "" for c in COLUMNS],
            "Higher is better": [
                "" if c.higher_is_better is None else "yes" if c.higher_is_better else "no"
                for c in COLUMNS
            ],
        }
    )


@module.ui
def data_ui() -> ui.Tag:
    return ui.div(
        ui.h4("Current file"),
        ui.output_ui("current"),
        ui.h4("Replace the data"),
        ui.input_file("upload", "Upload a CSV", accept=[".csv"]),
        ui.output_ui("upload_errors"),
        ui.download_button("sample", "Download sample file"),
        ui.h4("Columns"),
        ui.output_data_frame("schema"),
    )


@module.server
def data_server(
    input: Inputs,
    output: Outputs,
    session: Session,
    state: Callable[[], tuple[pd.DataFrame | None, list[str]]],
    path: Path,
) -> None:
    rejected: reactive.Value[list[str]] = reactive.value([])

    @render.ui
    def current() -> ui.TagChild:
        frame, errors = state()
        items = []
        if frame is not None:
            dates = frame[SURGERY_DATE]
            items.append(ui.tags.li(f"Rows: {len(frame)}"))
            items.append(
                ui.tags.li(f"Surgery dates: {dates.min():%Y-%m-%d} to {dates.max():%Y-%m-%d}")
            )
        if path.exists():
            updated = datetime.fromtimestamp(path.stat().st_mtime)
            items.append(ui.tags.li(f"Last updated: {updated:%Y-%m-%d %H:%M:%S}"))
        alert = None
        if errors:
            alert = ui.div(
                ui.p(STALE),
                ui.tags.ul(*[ui.tags.li(e) for e in errors]),
                class_="alert alert-danger",
            )
        return ui.TagList(ui.tags.ul(*items), alert)

    @reactive.effect
    @reactive.event(input.upload)
    def _replace() -> None:
        errors = replace_data(Path(input.upload()[0]["datapath"]), path)
        rejected.set(errors)
        if not errors:
            ui.notification_show("Data updated.")

    @render.ui
    def upload_errors() -> ui.TagChild:
        errors = rejected()
        if not errors:
            return None
        return ui.div(
            ui.p(ui.strong("This file was not loaded:")),
            ui.tags.ul(*[ui.tags.li(e) for e in errors]),
            class_="alert alert-danger",
        )

    @render.download(filename=lambda: sample_path().name)
    def sample() -> str:
        return str(sample_path())

    @render.data_frame
    def schema() -> pd.DataFrame:
        return schema_table()

from collections.abc import Callable
from pathlib import Path

import pandas as pd
from shiny import Inputs, Outputs, Session, module, render, ui


@module.ui
def data_ui() -> ui.Tag:
    return ui.div(ui.output_text("message"))


@module.server
def data_server(
    input: Inputs,
    output: Outputs,
    session: Session,
    state: Callable[[], tuple[pd.DataFrame | None, list[str]]],
    path: Path,
) -> None:
    @render.text
    def message() -> str:
        return "Data tab coming soon"

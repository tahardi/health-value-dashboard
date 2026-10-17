from collections.abc import Callable

import pandas as pd
from shiny import Inputs, Outputs, Session, module, render, ui


@module.ui
def value_ui() -> ui.Tag:
    return ui.div(ui.output_text("message"))


@module.server
def value_server(
    input: Inputs,
    output: Outputs,
    session: Session,
    data: Callable[[], pd.DataFrame],
) -> None:
    @render.text
    def message() -> str:
        return "Value tab coming soon"

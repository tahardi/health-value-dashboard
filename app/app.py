from shiny import App, Inputs, Outputs, Session, ui


def server(input: Inputs, output: Outputs, session: Session) -> None:
    pass


app = App(ui.page_navbar(title="Health Value Dashboard"), server)

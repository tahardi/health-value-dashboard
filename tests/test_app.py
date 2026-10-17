import importlib

from shiny import App


def test_app() -> None:
    # given
    module_name = "app.app"

    # when
    module = importlib.import_module(module_name)

    # then
    assert isinstance(module.app, App)

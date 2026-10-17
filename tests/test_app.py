import importlib
from pathlib import Path

import pytest
from shiny import App


def test_app(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # given
    path = tmp_path / "data" / "cases.csv"
    monkeypatch.setenv("DATA_PATH", str(path))
    module = importlib.import_module("app.app")

    # when
    module = importlib.reload(module)

    # then
    assert isinstance(module.app, App)
    assert path.read_text() == Path("data/sample.csv").read_text()

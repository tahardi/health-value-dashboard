from pathlib import Path

import pandas as pd
import pytest

from app.store import data_path, ensure_data, reload, sample_path

SAMPLE = Path("data/sample.csv")
PREVIOUS = pd.DataFrame({"case_id": ["C1"]})


@pytest.mark.parametrize(
    ("target", "existing", "expected"),
    [
        pytest.param("cases.csv", None, SAMPLE.read_text(), id="copies when missing"),
        pytest.param("cases.csv", "old", "old", id="leaves existing file"),
        pytest.param("a/b/cases.csv", None, SAMPLE.read_text(), id="creates parent dirs"),
    ],
)
def test_ensure_data(tmp_path: Path, target: str, existing: str | None, expected: str) -> None:
    # given
    path = tmp_path / target
    if existing is not None:
        path.write_text(existing)

    # when
    ensure_data(path, SAMPLE)

    # then
    assert path.read_text() == expected


@pytest.mark.parametrize(
    ("content", "previous", "expected", "errors"),
    [
        pytest.param(SAMPLE.read_text(), None, "new", [], id="valid"),
        pytest.param(
            "case_id\n",
            PREVIOUS,
            "previous",
            ["the file has no rows"],
            id="broken with previous",
        ),
        pytest.param("case_id\n", None, None, ["the file has no rows"], id="broken no previous"),
        pytest.param(
            None,
            PREVIOUS,
            "previous",
            ["data file not found: {path}"],
            id="missing file",
        ),
    ],
)
def test_reload(
    tmp_path: Path,
    content: str | None,
    previous: pd.DataFrame | None,
    expected: str | None,
    errors: list[str],
) -> None:
    # given
    path = tmp_path / "cases.csv"
    if content is not None:
        path.write_text(content)

    # when
    frame, problems = reload(path, previous)

    # then
    assert problems == [e.format(path=path) for e in errors]
    if expected == "new":
        assert frame is not None
        assert len(frame) == 2000
    elif expected == "previous":
        assert frame is previous
    else:
        assert frame is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(None, Path("data/sample.csv"), id="default"),
        pytest.param("/srv/cases.csv", Path("/srv/cases.csv"), id="from env"),
    ],
)
def test_data_path(monkeypatch: pytest.MonkeyPatch, value: str | None, expected: Path) -> None:
    # given
    monkeypatch.delenv("DATA_PATH", raising=False)
    if value is not None:
        monkeypatch.setenv("DATA_PATH", value)

    # when
    path = data_path()

    # then
    assert path == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(None, Path("data/sample.csv"), id="default"),
        pytest.param("/srv/sample.csv", Path("/srv/sample.csv"), id="from env"),
    ],
)
def test_sample_path(monkeypatch: pytest.MonkeyPatch, value: str | None, expected: Path) -> None:
    # given
    monkeypatch.delenv("SAMPLE_PATH", raising=False)
    if value is not None:
        monkeypatch.setenv("SAMPLE_PATH", value)

    # when
    path = sample_path()

    # then
    assert path == expected

from pathlib import Path

import pandas as pd
import pytest

from app.data_tab import replace_data
from app.schema import SURGEON

SAMPLE = Path("data/sample.csv")
OLD = b"old contents\n"


def without_surgeon() -> bytes:
    return pd.read_csv(SAMPLE, dtype=str).drop(columns=[SURGEON]).to_csv(index=False).encode()


@pytest.mark.parametrize(
    ("upload", "existing", "errors"),
    [
        pytest.param(SAMPLE.read_bytes(), OLD, [], id="valid upload"),
        pytest.param(
            without_surgeon(),
            OLD,
            [f"missing column `{SURGEON}`"],
            id="missing column",
        ),
        pytest.param(
            b"PK\x03\x04\x14\x00\x06\x00\x08\x00\x00\x00!\x00",
            OLD,
            ["could not read the file as CSV"],
            id="xlsx bytes",
        ),
        pytest.param(SAMPLE.read_bytes(), None, [], id="target missing"),
    ],
)
def test_replace_data(
    tmp_path: Path,
    upload: bytes,
    existing: bytes | None,
    errors: list[str],
) -> None:
    # given
    source = tmp_path / "upload" / "file.csv"
    source.parent.mkdir()
    source.write_bytes(upload)
    target = tmp_path / "data" / "cases.csv"
    target.parent.mkdir()
    mtime = None
    if existing is not None:
        target.write_bytes(existing)
        mtime = target.stat().st_mtime_ns

    # when
    problems = replace_data(source, target)

    # then
    assert problems == errors
    if errors:
        assert target.read_bytes() == existing
        assert target.stat().st_mtime_ns == mtime
    else:
        assert target.read_bytes() == upload
    assert list(target.parent.iterdir()) == [target]

import io
from pathlib import Path
from typing import IO

import pandas as pd

from app.schema import COLUMNS, FUNCTION_POST, FUNCTION_PRE, GAIN, Column, Kind, Role

BOOLEANS = {"1": True, "true": True, "yes": True, "0": False, "false": False, "no": False}
MAX_ROWS_LISTED = 5


class DataError(Exception):
    def __init__(self, errors: list[str]) -> None:
        super().__init__("; ".join(errors))
        self.errors = errors


def load(source: str | Path | IO[bytes]) -> pd.DataFrame:
    raw = _read(source)
    missing = [c for c in COLUMNS if c.name not in raw.columns]
    errors = [f"missing column `{c.name}`" for c in missing]
    present = [c for c in COLUMNS if c not in missing]
    for column in present:
        errors.extend(_problems(column, raw[column.name]))
    if errors:
        raise DataError(errors)
    frame = pd.DataFrame({c.name: _convert(c, raw[c.name]) for c in COLUMNS})
    frame[GAIN] = frame[FUNCTION_POST] - frame[FUNCTION_PRE]
    return frame


def _read(source: str | Path | IO[bytes]) -> pd.DataFrame:
    content = source.read() if hasattr(source, "read") else Path(source).read_bytes()
    try:
        if b"\x00" in content:
            raise ValueError("binary file")
        raw = pd.read_csv(
            io.BytesIO(content),
            dtype=str,
            keep_default_na=False,
            encoding="utf-8-sig",
        )
    except (ValueError, UnicodeDecodeError, pd.errors.ParserError) as err:
        raise DataError(["could not read the file as CSV"]) from err
    if raw.empty:
        raise DataError(["the file has no rows"])
    raw.columns = [str(c).strip() for c in raw.columns]
    return raw.apply(lambda s: s.str.strip())


def _problems(column: Column, values: pd.Series) -> list[str]:
    blank = values == ""
    problems = []
    if column.role != Role.MEASURE:
        problems.append(_message(column, values.index[blank], "blank value", "blank values"))
    filled = values[~blank]
    if column.kind == Kind.DATE:
        bad = filled.index[_dates(filled).isna()]
        problems.append(
            _message(column, bad, "value that is not a date", "values that are not dates")
        )
    if column.kind == Kind.NUMBER:
        numbers = pd.to_numeric(filled, errors="coerce")
        problems.append(
            _message(
                column,
                filled.index[numbers.isna()],
                "value that is not a number",
                "values that are not numbers",
            )
        )
        problems.append(
            _message(column, filled.index[numbers < 0], "negative value", "negative values")
        )
    if column.kind == Kind.BOOLEAN:
        bad = filled.index[~filled.str.lower().isin(BOOLEANS)]
        problems.append(
            _message(column, bad, "value that is not yes/no", "values that are not yes/no")
        )
    return [p for p in problems if p]


def _message(column: Column, rows: pd.Index, singular: str, plural: str) -> str:
    numbers = [str(i + 2) for i in rows]
    if not numbers:
        return ""
    listed = ", ".join(numbers[:MAX_ROWS_LISTED])
    if len(numbers) > MAX_ROWS_LISTED:
        listed += ", …"
    if len(numbers) == 1:
        return f"column `{column.name}` has 1 {singular} (row {listed})"
    return f"column `{column.name}` has {len(numbers)} {plural} (rows {listed})"


def _dates(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values, format="%Y-%m-%d", errors="coerce").astype("datetime64[ns]")


def _convert(column: Column, values: pd.Series) -> pd.Series:
    if column.kind == Kind.CATEGORY:
        return values.astype("string")
    if column.kind == Kind.DATE:
        return _dates(values)
    blank = values == ""
    if column.kind == Kind.NUMBER:
        return pd.to_numeric(values.mask(blank), errors="coerce").astype("float64")
    return values.str.lower().map(BOOLEANS).mask(blank).astype("boolean")

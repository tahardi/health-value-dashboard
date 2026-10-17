import io

import numpy as np
import pandas as pd
import pytest

from app.data import DataError, load

VALID_ROW = {
    "case_id": "C0001",
    "surgeon": "Dr. Avery",
    "procedure": "Total knee",
    "facility": "North",
    "payer": "Medicare",
    "age_group": "65-74",
    "sex": "F",
    "asa_class": "2",
    "surgery_date": "2025-03-14",
    "length_of_stay_days": "2",
    "total_cost": "18500.5",
    "implant_cost": "5200",
    "complication": "no",
    "readmit_30d": "yes",
    "function_pre": "40",
    "function_post": "72",
}


def csv_source(
    rows: list[dict[str, str]],
    drop: tuple[str, ...] = (),
    header: dict[str, str] | None = None,
    newline: str = "\n",
    prefix: str = "",
) -> io.BytesIO:
    names = [n for n in rows[0] if n not in drop]
    renamed = [(header or {}).get(n, n) for n in names]
    lines = [",".join(renamed)] + [",".join(row[n] for n in names) for row in rows]
    return io.BytesIO((prefix + newline.join(lines) + newline).encode())


def row(**changes: str) -> dict[str, str]:
    return {**VALID_ROW, **changes}


def valid_frame(**changes: object) -> pd.DataFrame:
    values: dict[str, object] = {
        "case_id": "C0001",
        "surgeon": "Dr. Avery",
        "procedure": "Total knee",
        "facility": "North",
        "payer": "Medicare",
        "age_group": "65-74",
        "sex": "F",
        "asa_class": "2",
        "surgery_date": pd.Timestamp("2025-03-14"),
        "length_of_stay_days": 2.0,
        "total_cost": 18500.5,
        "implant_cost": 5200.0,
        "complication": False,
        "readmit_30d": True,
        "function_pre": 40.0,
        "function_post": 72.0,
        "function_gain": 32.0,
        **changes,
    }
    frame = pd.DataFrame({k: [v] for k, v in values.items()})
    categories = ["case_id", "surgeon", "procedure", "facility", "payer", "age_group", "sex"]
    return frame.astype(
        {
            **{c: "string" for c in [*categories, "asa_class"]},
            "surgery_date": "datetime64[ns]",
            "length_of_stay_days": "float64",
            "total_cost": "float64",
            "implant_cost": "float64",
            "complication": "boolean",
            "readmit_30d": "boolean",
            "function_pre": "float64",
            "function_post": "float64",
            "function_gain": "float64",
        }
    )


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        pytest.param(csv_source([row()]), valid_frame(), id="valid"),
        pytest.param(
            csv_source(
                [row(complication="FALSE", readmit_30d="TRUE")],
                header={"surgeon": " surgeon "},
                newline="\r\n",
                prefix="﻿",
            ),
            valid_frame(),
            id="excel",
        ),
        pytest.param(
            csv_source([row(function_post="")]),
            valid_frame(function_post=np.nan, function_gain=np.nan),
            id="blank measure",
        ),
        pytest.param(csv_source([row(notes="hello")]), valid_frame(), id="extra column"),
        pytest.param(
            csv_source([row()], drop=("total_cost",)),
            ["missing column `total_cost`"],
            id="missing column",
        ),
        pytest.param(
            csv_source([row(), row(surgeon=""), row(surgeon="")]),
            ["column `surgeon` has 2 blank values (rows 3, 4)"],
            id="blank dimension",
        ),
        pytest.param(
            csv_source([row(surgery_date="03/14/2025")]),
            ["column `surgery_date` has 1 value that is not a date (row 2)"],
            id="bad date",
        ),
        pytest.param(
            csv_source([row(total_cost="lots")]),
            ["column `total_cost` has 1 value that is not a number (row 2)"],
            id="not a number",
        ),
        pytest.param(
            csv_source([row(total_cost="-5")]),
            ["column `total_cost` has 1 negative value (row 2)"],
            id="negative",
        ),
        pytest.param(
            csv_source([row(readmit_30d="maybe")]),
            ["column `readmit_30d` has 1 value that is not yes/no (row 2)"],
            id="bad boolean",
        ),
        pytest.param(
            csv_source([row(surgery_date="soon") for _ in range(7)]),
            ["column `surgery_date` has 7 values that are not dates (rows 2, 3, 4, 5, 6, …)"],
            id="many bad rows",
        ),
        pytest.param(
            csv_source([row(surgery_date="soon")], drop=("total_cost",)),
            [
                "missing column `total_cost`",
                "column `surgery_date` has 1 value that is not a date (row 2)",
            ],
            id="two problems",
        ),
        pytest.param(
            io.BytesIO((",".join(VALID_ROW) + "\n").encode()),
            ["the file has no rows"],
            id="no rows",
        ),
        pytest.param(
            io.BytesIO(b"PK\x03\x04" + bytes(100)),
            ["could not read the file as CSV"],
            id="not csv",
        ),
    ],
)
def test_load(source: io.BytesIO, expected: pd.DataFrame | list[str]) -> None:
    # given
    data = source

    # when
    if isinstance(expected, list):
        with pytest.raises(DataError) as exc:
            load(data)
        result = exc.value.errors
    else:
        result = load(data)

    # then
    if isinstance(expected, list):
        assert result == expected
    else:
        pd.testing.assert_frame_equal(result, expected)

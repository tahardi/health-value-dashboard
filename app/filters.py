from datetime import date

import pandas as pd

from app.schema import SURGERY_DATE


def apply_filters(
    df: pd.DataFrame,
    selections: dict[str, list[str]],
    start: date | None,
    end: date | None,
) -> pd.DataFrame:
    keep = pd.Series(True, index=df.index)
    for column, values in selections.items():
        if values:
            keep &= df[column].isin(values)
    if start is not None:
        keep &= df[SURGERY_DATE] >= pd.Timestamp(start)
    if end is not None:
        keep &= df[SURGERY_DATE] <= pd.Timestamp(end)
    return df[keep]

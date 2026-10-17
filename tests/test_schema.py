from app.schema import COLUMNS, Kind, filters, measures, rate_measures


def test_columns() -> None:
    # given
    names = [c.name for c in COLUMNS]

    # when
    unique = set(names)

    # then
    assert len(unique) == len(names)


def test_filters() -> None:
    # given
    expected = ["procedure", "facility"]

    # when
    names = [c.name for c in filters()]

    # then
    assert names == expected


def test_measures() -> None:
    # given
    expected = [
        "length_of_stay_days",
        "total_cost",
        "implant_cost",
        "function_pre",
        "function_post",
    ]

    # when
    names = [c.name for c in measures(Kind.NUMBER)]

    # then
    assert names == expected


def test_rate_measures() -> None:
    # given
    expected = ["complication", "readmit_30d"]

    # when
    names = [c.name for c in rate_measures()]

    # then
    assert names == expected

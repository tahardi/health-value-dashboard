import pytest

from app.schema import COLUMNS, Kind, Role, filters, measures, rate_measures


def test_columns() -> None:
    # given
    names = [c.name for c in COLUMNS]

    # when
    unique = set(names)

    # then
    assert len(unique) == len(names)
    for column in COLUMNS:
        assert (column.higher_is_better is not None) == (column.role == Role.MEASURE)


def test_filters() -> None:
    # given
    expected = ["procedure", "facility"]

    # when
    names = [c.name for c in filters()]

    # then
    assert names == expected


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        pytest.param(
            None,
            [
                "length_of_stay_days",
                "total_cost",
                "implant_cost",
                "complication",
                "readmit_30d",
                "function_pre",
                "function_post",
            ],
            id="all",
        ),
        pytest.param(
            Kind.NUMBER,
            [
                "length_of_stay_days",
                "total_cost",
                "implant_cost",
                "function_pre",
                "function_post",
            ],
            id="number",
        ),
        pytest.param(Kind.BOOLEAN, ["complication", "readmit_30d"], id="boolean"),
        pytest.param(Kind.CATEGORY, [], id="category"),
    ],
)
def test_measures(kind: Kind | None, expected: list[str]) -> None:
    # given
    wanted = kind

    # when
    names = [c.name for c in measures(wanted)]

    # then
    assert names == expected


def test_rate_measures() -> None:
    # given
    expected = ["complication", "readmit_30d"]

    # when
    names = [c.name for c in rate_measures()]

    # then
    assert names == expected

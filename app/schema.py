from dataclasses import dataclass
from enum import StrEnum


class Kind(StrEnum):
    CATEGORY = "category"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"


class Role(StrEnum):
    ID = "id"
    DIMENSION = "dimension"
    MEASURE = "measure"
    DATE = "date"


@dataclass(frozen=True)
class Column:
    name: str
    label: str
    kind: Kind
    role: Role
    filter: bool = False
    higher_is_better: bool | None = None


CASE_ID = "case_id"
SURGEON = "surgeon"
PROCEDURE = "procedure"
FACILITY = "facility"
SURGERY_DATE = "surgery_date"
COST = "total_cost"
FUNCTION_PRE = "function_pre"
FUNCTION_POST = "function_post"
GAIN = "function_gain"

COLUMNS: tuple[Column, ...] = (
    Column(CASE_ID, "Case", Kind.CATEGORY, Role.ID),
    Column(SURGEON, "Surgeon", Kind.CATEGORY, Role.DIMENSION),
    Column(PROCEDURE, "Procedure", Kind.CATEGORY, Role.DIMENSION, filter=True),
    Column(FACILITY, "Facility", Kind.CATEGORY, Role.DIMENSION, filter=True),
    Column("payer", "Payer", Kind.CATEGORY, Role.DIMENSION),
    Column("age_group", "Age group", Kind.CATEGORY, Role.DIMENSION),
    Column("sex", "Sex", Kind.CATEGORY, Role.DIMENSION),
    Column("asa_class", "ASA class", Kind.CATEGORY, Role.DIMENSION),
    Column(SURGERY_DATE, "Surgery date", Kind.DATE, Role.DATE),
    Column(
        "length_of_stay_days",
        "Length of stay (days)",
        Kind.NUMBER,
        Role.MEASURE,
        higher_is_better=False,
    ),
    Column(COST, "Total cost ($)", Kind.NUMBER, Role.MEASURE, higher_is_better=False),
    Column("implant_cost", "Implant cost ($)", Kind.NUMBER, Role.MEASURE, higher_is_better=False),
    Column("complication", "Complication", Kind.BOOLEAN, Role.MEASURE, higher_is_better=False),
    Column(
        "readmit_30d",
        "Readmitted within 30 days",
        Kind.BOOLEAN,
        Role.MEASURE,
        higher_is_better=False,
    ),
    Column(
        FUNCTION_PRE,
        "Function score before",
        Kind.NUMBER,
        Role.MEASURE,
        higher_is_better=True,
    ),
    Column(
        FUNCTION_POST,
        "Function score after",
        Kind.NUMBER,
        Role.MEASURE,
        higher_is_better=True,
    ),
)


def filters() -> list[Column]:
    return [c for c in COLUMNS if c.role == Role.DIMENSION and c.filter]


def measures(kind: Kind | None = None) -> list[Column]:
    return [c for c in COLUMNS if c.role == Role.MEASURE and kind in (None, c.kind)]


def rate_measures() -> list[Column]:
    return measures(Kind.BOOLEAN)

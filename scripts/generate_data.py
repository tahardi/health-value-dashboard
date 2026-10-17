from pathlib import Path
from typing import NamedTuple

import numpy as np
import pandas as pd

from app.schema import (
    CASE_ID,
    COST,
    FACILITY,
    FUNCTION_POST,
    FUNCTION_PRE,
    PROCEDURE,
    SURGEON,
    SURGERY_DATE,
)

OUTPUT = Path(__file__).resolve().parent.parent / "data" / "sample.csv"

SURGEONS = tuple(
    f"Dr. {name}"
    for name in (
        "Smith",
        "Johnson",
        "Williams",
        "Brown",
        "Jones",
        "Garcia",
        "Miller",
        "Davis",
        "Wilson",
        "Moore",
        "Taylor",
        "Anderson",
    )
)
READMIT_OUTLIER, HIGH_COST, HIGH_VALUE = SURGEONS[:3]
SHARES = (0.10, 0.11, 0.12, 0.15, 0.13, 0.11, 0.10, 0.10, 0.08)
LOW_VOLUME = (8, 15, 1)
READMIT_FACTOR = {READMIT_OUTLIER: 5.0}
COST_FACTOR = {HIGH_COST: 1.4, HIGH_VALUE: 0.75}
GAIN_BONUS = {HIGH_VALUE: 8.0}


class Procedure(NamedTuple):
    share: float
    cost: float
    implant: float
    stay: int
    extra_stay: float


PROCEDURES = {
    "Total Knee Replacement": Procedure(0.30, 26000, 6000, 1, 1.0),
    "Total Hip Replacement": Procedure(0.25, 28000, 6500, 1, 1.0),
    "ACL Reconstruction": Procedure(0.15, 12000, 1500, 0, 0.6),
    "Rotator Cuff Repair": Procedure(0.15, 9000, 1200, 0, 0.3),
    "Lumbar Spinal Fusion": Procedure(0.15, 45000, 12000, 3, 1.5),
}
FACILITIES = {"North Campus": 0.40, "South Campus": 0.35, "Ambulatory Center": 0.25}
PAYERS = {"Medicare": 0.45, "Commercial": 0.40, "Medicaid": 0.15}
AGE_GROUPS = {"<50": 0.15, "50-64": 0.30, "65-74": 0.35, "75+": 0.20}
AGE_HOME_PENALTY = {"<50": 0.0, "50-64": 0.02, "65-74": 0.06, "75+": 0.15}
SEXES = {"F": 0.55, "M": 0.45}
ASA_CLASSES = {1: 0.15, 2: 0.45, 3: 0.32, 4: 0.08}
FIRST_DAY = np.datetime64("2024-10-01")
LAST_DAY = np.datetime64("2026-09-30")
BLANK_POST_SHARE = 0.05


def generate(seed: int = 42, cases: int = 2000) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    surgeon = rng.permutation(np.repeat(SURGEONS, _counts(cases)))
    procedure = _pick(rng, {name: p.share for name, p in PROCEDURES.items()}, cases)
    age_group = _pick(rng, AGE_GROUPS, cases)
    asa = _pick(rng, ASA_CLASSES, cases).astype(int)
    risk = asa - 1
    profile = [PROCEDURES[p] for p in procedure]
    base_cost = np.array([p.cost for p in profile])
    implant_base = np.array([p.implant for p in profile])
    stay = np.array([p.stay for p in profile]) + rng.poisson(
        np.array([p.extra_stay for p in profile]) + 0.3 * risk
    )
    complication = rng.random(cases) < 0.03 + 0.025 * risk
    readmit_factor = np.array([READMIT_FACTOR.get(s, 1.0) for s in surgeon])
    readmit = rng.random(cases) < (0.04 + 0.02 * risk) * readmit_factor
    implant = implant_base * rng.normal(1.0, 0.1, cases)
    cost_factor = np.array([COST_FACTOR.get(s, 1.0) for s in surgeon])
    cost = (
        base_cost * (1 + 0.12 * risk) + 2500 * stay + 6000 * complication
    ) * cost_factor * rng.lognormal(0.0, 0.12, cases) + implant
    pre = np.clip(rng.normal(42, 10, cases), 5, 90).round()
    gain_bonus = np.array([GAIN_BONUS.get(s, 0.0) for s in surgeon])
    post = np.clip(pre + rng.normal(25 + gain_bonus - 2 * risk, 10), 0, 100).round()
    blank = rng.random(cases) < BLANK_POST_SHARE
    age_penalty = np.array([AGE_HOME_PENALTY[a] for a in age_group])
    home = rng.random(cases) < 0.95 - 0.06 * risk - age_penalty
    days = rng.integers(0, (LAST_DAY - FIRST_DAY).astype(int) + 1, cases)
    frame = pd.DataFrame(
        {
            SURGEON: surgeon,
            PROCEDURE: procedure,
            FACILITY: _pick(rng, FACILITIES, cases),
            "payer": _pick(rng, PAYERS, cases),
            "age_group": age_group,
            "sex": _pick(rng, SEXES, cases),
            "asa_class": asa,
            SURGERY_DATE: pd.to_datetime(FIRST_DAY + days).strftime("%Y-%m-%d"),
            "length_of_stay_days": stay,
            COST: cost.round().astype(int),
            "implant_cost": implant.round().astype(int),
            "complication": complication.astype(int),
            "readmit_30d": readmit.astype(int),
            FUNCTION_PRE: pre.astype(int),
            FUNCTION_POST: pd.array(np.where(blank, np.nan, post), dtype="Int64"),
            "discharged_home": home.astype(int),
        }
    )
    frame = frame.sort_values(SURGERY_DATE, kind="stable", ignore_index=True)
    frame.insert(0, CASE_ID, [f"C{i:05d}" for i in range(1, cases + 1)])
    return frame


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    generate().to_csv(OUTPUT, index=False)


def _counts(cases: int) -> list[int]:
    remainder = cases - sum(LOW_VOLUME)
    counts = [int(share * remainder) for share in SHARES]
    counts[3] += remainder - sum(counts)
    return [*counts, *LOW_VOLUME]


def _pick(
    rng: np.random.Generator, weights: dict[str, float] | dict[int, float], size: int
) -> np.ndarray:
    return rng.choice(np.array(list(weights), dtype=object), size=size, p=list(weights.values()))


if __name__ == "__main__":
    main()

import os
import shutil
from pathlib import Path

import pandas as pd

from app.data import DataError, load

DEFAULT_PATH = "data/sample.csv"


def data_path() -> Path:
    return Path(os.environ.get("DATA_PATH", DEFAULT_PATH))


def sample_path() -> Path:
    return Path(os.environ.get("SAMPLE_PATH", DEFAULT_PATH))


def ensure_data(path: Path, sample: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(sample, path)


def reload(path: Path, previous: pd.DataFrame | None) -> tuple[pd.DataFrame | None, list[str]]:
    try:
        return load(path), []
    except FileNotFoundError:
        return previous, [f"data file not found: {path}"]
    except DataError as err:
        return previous, err.errors

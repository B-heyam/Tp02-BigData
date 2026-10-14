import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)

DATA_PATH = Path(os.environ.get("TP02_DATA", ROOT / "data" / "train.csv"))

CHUNK_ROWS = 100_000

USE_COLS = ["fare_amount", "passenger_count"]
DTYPES = {"fare_amount": "float64", "passenger_count": "int16"}


OOM_GUARD_PERCENT = 90.0
2
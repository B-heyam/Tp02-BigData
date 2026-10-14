import json
import time

import pandas as pd

import config
from monitor import PeakMemory


def main():
    if not config.DATA_PATH.exists():
        raise SystemExit(f"File not found: {config.DATA_PATH}")

    total_sum, total_count, n_chunks = 0.0, 0, 0
    grp_sum = pd.Series(dtype="float64")
    grp_cnt = pd.Series(dtype="int64")

    t0 = time.perf_counter()
    with PeakMemory() as mem:
        reader = pd.read_csv(
            config.DATA_PATH,
            usecols=config.USE_COLS,
            dtype=config.DTYPES,
            chunksize=config.CHUNK_ROWS,
        )
        for chunk in reader:
            n_chunks += 1
            fares = chunk["fare_amount"]
            total_sum += fares.sum()
            total_count += fares.count()

            g = chunk.groupby("passenger_count")["fare_amount"]
            grp_sum = grp_sum.add(g.sum(), fill_value=0)
            grp_cnt = grp_cnt.add(g.count(), fill_value=0)

            if n_chunks % 50 == 0:
                print(f"\r  chunks processed: {n_chunks}  rows: {total_count:,}", end="")
    elapsed = time.perf_counter() - t0
    print()

    mean_by_pass = (grp_sum / grp_cnt).round(3) 
    result = {
        "method": "Pandas Chunking",
        "chunk_rows": config.CHUNK_ROWS,
        "chunks": n_chunks,
        "rows": int(total_count),
        "sum_fare": round(total_sum, 2),
        "mean_fare": round(total_sum / total_count, 4),
        "mean_fare_by_passenger_count": {int(k): float(v) for k, v in mean_by_pass.items()},
        "peak_process_mb": round(mem.peak_mb, 1),
        "seconds": round(elapsed, 1),
    }
    (config.RESULTS_DIR / "task2.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

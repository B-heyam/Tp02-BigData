import json
import time

import dask
import dask.dataframe as dd
from dask.diagnostics import ProgressBar

import config
from monitor import PeakMemory


def main():
    if not config.DATA_PATH.exists():
        raise SystemExit(f"File not found: {config.DATA_PATH}");

    t_build = time.perf_counter();
    ddf = dd.read_csv(
        config.DATA_PATH,
        usecols=config.USE_COLS,
        dtype=config.DTYPES,
        blocksize="128MB",
    )
    total = ddf["fare_amount"].sum();
    count = ddf["fare_amount"].count();
    mean = ddf["fare_amount"].mean();
    by_pass = ddf.groupby("passenger_count")["fare_amount"].mean()
    build_s = time.perf_counter() - t_build

    print(f"Graph built in {build_s:.3f}s - nothing has been read yet.")
    print(f"  type(total)    = {type(total).__name__}   <- a lazy object, not a number")
    print(f"  partitions     = {ddf.npartitions}   (each ~128 MB, processed in parallel)")

    
    try:
        by_pass_opt = by_pass.optimize()
        print("  graph optimized (column projection + task fusion)")
    except Exception:
        by_pass_opt = by_pass



    try:
        by_pass_opt.visualize(filename=str(config.RESULTS_DIR / "task3_graph.png"))
        print("  graph picture saved: results/task3_graph.png")
    except Exception:
        print("  (graph picture skipped - install Graphviz + 'pip install graphviz' to enable)")

    t0 = time.perf_counter()
    with PeakMemory() as mem, ProgressBar():
        total_v, count_v, mean_v, by_pass_v = dask.compute(
            total, count, mean, by_pass_opt, scheduler="threads"
        )
    elapsed = time.perf_counter() - t0

    result = {
        "method": "Dask DataFrame",
        "partitions": int(ddf.npartitions),
        "rows": int(count_v),
        "sum_fare": round(float(total_v), 2),
        "mean_fare": round(float(mean_v), 4),
        "mean_fare_by_passenger_count": {int(k): round(float(v), 3) for k, v in by_pass_v.items()},
        "graph_build_seconds": round(build_s, 3),
        "peak_process_mb": round(mem.peak_mb, 1),
        "seconds": round(elapsed, 1),
    }
    (config.RESULTS_DIR / "task3.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2));


if __name__ == "__main__":
    main();

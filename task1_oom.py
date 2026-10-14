import json
import multiprocessing as mp
import time
import traceback

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import psutil

import config


def _load(path, q):
    try:
        df = pd.read_csv(path)  
        q.put(("LOADED", f"shape={df.shape}"))
    except MemoryError:
        q.put(("MemoryError", traceback.format_exc()))
    except Exception:
        q.put(("ERROR", traceback.format_exc()))


def main():
    if not config.DATA_PATH.exists():
        raise SystemExit(f"File not found: {config.DATA_PATH}")

    size_gb = config.DATA_PATH.stat().st_size / 1024**3
    total_gb = psutil.virtual_memory().total / 1024**3
    print(f"File: {config.DATA_PATH.name}  {size_gb:.2f} GB | System RAM: {total_gb:.1f} GB")
    print(f"Guard: stop at {config.OOM_GUARD_PERCENT:.0f}% system RAM\n")

    q = mp.Queue()
    child = mp.Process(target=_load, args=(config.DATA_PATH, q))
    t0 = time.perf_counter()
    child.start()
    proc = psutil.Process(child.pid)

    timeline, peak_child, outcome, detail = [], 0, None, ""
    while child.is_alive():
        sys_pct = psutil.virtual_memory().percent
        try:
            rss = proc.memory_info().rss
        except psutil.Error:
            rss = 0
        peak_child = max(peak_child, rss)
        timeline.append((time.perf_counter() - t0, rss / 1024**2, sys_pct))
        print(f"\r  t={timeline[-1][0]:6.1f}s  process={rss/1024**3:5.2f} GB  system={sys_pct:5.1f}%", end="")
        if sys_pct >= config.OOM_GUARD_PERCENT:
            child.kill()
            outcome = "KILLED_BY_GUARD"
            detail = f"System RAM reached {sys_pct:.1f}% - process killed to protect the computer."
            break
        time.sleep(0.5)
    child.join()
    elapsed = time.perf_counter() - t0
    print()

    if outcome is None:
        try:
            outcome, detail = q.get(timeout=5)
        except Exception:
            outcome, detail = "ERROR", "Child ended without a result (possibly killed by the OS - OOM)."

    result = {
        "method": "Standard Pandas",
        "file_gb": round(size_gb, 2),
        "system_ram_gb": round(total_gb, 1),
        "outcome": outcome,
        "detail": detail,
        "peak_process_mb": round(peak_child / 1024**2, 1),
        "peak_system_percent": round(max((p for _, _, p in timeline), default=0), 1),
        "seconds": round(elapsed, 1),
    }
    (config.RESULTS_DIR / "task1.json").write_text(json.dumps(result, indent=2))

    if timeline:
        t, mb, pct = zip(*timeline)
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(t, pct)
        ax.axhline(config.OOM_GUARD_PERCENT, ls="--", color="red", label="guard limit")
        ax.set(xlabel="seconds", ylabel="system RAM used (%)", title=f"Task 1 - pd.read_csv: {outcome}")
        ax.legend()
        fig.tight_layout()
        fig.savefig(config.RESULTS_DIR / "task1_memory.png", dpi=150)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    mp.freeze_support()
    main()

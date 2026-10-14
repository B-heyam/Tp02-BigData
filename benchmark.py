import json

import matplotlib
matplotlib.use("Agg")


import matplotlib.pyplot as plt

import config

R = config.RESULTS_DIR


def load(name):
    p = R / name
    return json.loads(p.read_text()) if p.exists() else None


t1, t2, t3 = load("task1.json"), load("task2.json"), load("task3.json") 
ram_gb = t1["system_ram_gb"] if t1 else None

rows = []
if t1:
    ok = t1["outcome"] == "LOADED"
    rows.append(("Standard Pandas",
                 f'{t1["peak_process_mb"]:.0f} MB (system peak {t1["peak_system_percent"]}%)',
                 f'{t1["seconds"]} s' if ok else f'N/A ({t1["outcome"]})'))
if t2:
    rows.append(("Pandas Chunking", f'{t2["peak_process_mb"]:.0f} MB', f'{t2["seconds"]} s (sequential)'))
if t3:
    rows.append(("Dask DataFrame", f'{t3["peak_process_mb"]:.0f} MB', f'{t3["seconds"]} s (multi-threaded)'))


md = ["| Method | Max RAM Utilization | Execution Speed |", "|---|---|---|"];
md += [f"| {a} | {b} | {c} |" for a, b, c in rows];
table = "\n".join(md)
(R / "benchmark_table.md").write_text(table + "\n")
print(table)

if t2 and t3:
    print(f"\nSame results? mean fare chunking={t2['mean_fare']}  dask={t3['mean_fare']}  "
          f"rows {t2['rows']:,} vs {t3['rows']:,}")
    print(f"Dask speed-up vs chunking: x{t2['seconds'] / max(t3['seconds'], 1e-9):.2f}")

labels, ram, secs = [], [], []
for name, t in (("Pandas Chunking", t2), ("Dask DataFrame", t3)):
    if t:
        labels.append(name); ram.append(t["peak_process_mb"]); secs.append(t["seconds"])
if t1:
    labels.insert(0, "Standard Pandas"); ram.insert(0, t1["peak_process_mb"])
    secs.insert(0, t1["seconds"] if t1["outcome"] == "LOADED" else 0)

if labels:
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].bar(labels, ram, color=["#c0392b", "#2980b9", "#27ae60"][-len(labels):])
    axes[0].set(title="Peak RAM of the process (MB)", ylabel="MB")
    axes[1].bar(labels, secs, color=["#c0392b", "#2980b9", "#27ae60"][-len(labels):])
    axes[1].set(title="Execution time (s) - 0 = crashed / not completed", ylabel="seconds")
    for ax in axes:
        ax.tick_params(axis="x", rotation=15)
    fig.tight_layout()
    fig.savefig(R / "benchmark.png", dpi=150)
    print("\nSaved results/benchmark.png and results/benchmark_table.md")


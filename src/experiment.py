import os
import glob
import json
import csv

import chunking
from pipeline import run, ratios

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "data"))
RES = os.path.normpath(os.path.join(HERE, "..", "results"))

DATASETS = ["git_repo", "wiki", "random_bin"]
PRIMARY_AVG = 2048
SWEEP_AVG = [1024, 2048, 4096, 8192, 16384]      # chunk-size sweep, git_repo only
SWEEP_DATASET = "git_repo"

STRATEGIES = ["comp_per_version", "filedag", "dedup", "dedup_comp", "dedup_delta"]


def algos(avg):
    return {
        "FSC": lambda d: chunking.fsc(d, size=avg),
        "FastCDC": lambda d: chunking.fastcdc(d, avg_size=avg,
                                              min_size=max(64, avg // 4),
                                              max_size=avg * 8),
        "AE": lambda d: chunking.ae(d, avg_size=avg),
    }


def load(name):
    return [open(f, "rb").read()
            for f in sorted(glob.glob(os.path.join(DATA, name, "v*.bin")))]


def main():
    os.makedirs(RES, exist_ok=True)
    jobs = [(d, PRIMARY_AVG) for d in DATASETS]
    jobs += [(SWEEP_DATASET, a) for a in SWEEP_AVG if a != PRIMARY_AVG]

    rows, stat_rows, summary = [], [], {}
    for name, avg in jobs:
        versions = load(name)
        raw = sum(len(v) for v in versions)
        print(f"\n=== {name}  avg_size={avg}  {len(versions)} versions, {raw/1024:.1f} KiB ===")
        for algo, fn in algos(avg).items():
            sizes, st = run(versions, fn)
            r = ratios(sizes)
            extra_vs_comp = r["dedup_delta"] - r["dedup_comp"]
            extra_vs_dedup = r["dedup_delta"] - r["dedup"]
            resid_cut = 100.0 * (1 - sizes["dedup_delta"] / sizes["dedup_comp"]) if sizes["dedup_comp"] else 0.0

            print(f"  {algo:8s} avg_chunk={st['avg_chunk_size']:6.0f}B uniq={st['n_unique']:5d} | "
                  f"comp={r['comp_per_version']:5.1f}% dedup={r['dedup']:5.1f}% "
                  f"dedup+comp={r['dedup_comp']:5.1f}% dedup+delta={r['dedup_delta']:5.1f}% "
                  f"(+{extra_vs_comp:.1f}pp) filedag={r['filedag']:5.1f}% | {st['pipeline_MBps']:.1f} MB/s")

            rows.append(dict(
                dataset=name, algorithm=algo, avg_size=avg, raw_bytes=sizes["raw"],
                **{f"{k}_bytes": sizes[k] for k in STRATEGIES},
                **{f"{k}_reduction_pct": round(r[k], 2) for k in STRATEGIES},
                delta_extra_pp_vs_dedupcomp=round(extra_vs_comp, 2),
                delta_extra_pp_vs_dedup=round(extra_vs_dedup, 2),
                delta_residual_cut_pct=round(resid_cut, 1),
                n_unique_chunks=st["n_unique"], n_delta_encoded=st["n_delta_encoded"],
                pipeline_MBps=round(st["pipeline_MBps"], 2),
            ))
            stat_rows.append(dict(dataset=name, algorithm=algo, avg_size=avg,
                                  **{k: round(v, 3) if isinstance(v, float) else v
                                     for k, v in st.items()}))
            summary[f"{name}|{algo}|{avg}"] = dict(sizes=sizes, ratios=r, stats=st)

    _write_csv(os.path.join(RES, "results.csv"), rows)
    _write_csv(os.path.join(RES, "stats.csv"), stat_rows)
    with open(os.path.join(RES, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    print(f"\nwrote results.csv, stats.csv, summary.json -> {RES}")


def _write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()

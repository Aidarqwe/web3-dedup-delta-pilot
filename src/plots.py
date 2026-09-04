import os
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.normpath(os.path.join(HERE, "..", "results"))

AVG = 2048
DS = ["git_repo", "wiki", "random_bin"]
DS_LABEL = {"git_repo": "git repo\n(20 commits)",
            "wiki": "Wikipedia\n(20 revisions)",
            "random_bin": "random\n(control)"}
ALGOS = ["FSC", "FastCDC", "AE"]
COLOR = {"FSC": "#b0b0b0", "FastCDC": "#2f6fb0", "AE": "#4aa564"}

_summary = json.load(open(os.path.join(RES, "summary.json")))


def get(ds, algo, avg=AVG):
    return _summary[f"{ds}|{algo}|{avg}"]


def fig_staircase():
    strat = ["comp_per_version", "dedup", "dedup_comp", "dedup_delta", "filedag"]
    labels = ["compression only", "chunk dedup (IPFS)", "dedup + compression",
              "dedup + delta (proposed)", "whole-file delta (FileDAG)"]
    colors = ["#c9c9c9", "#f0c060", "#e08a3c", "#2f6fb0", "#7a7a7a"]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=True)
    for ax, ds in zip(axes, DS):
        vals = [get(ds, "FastCDC")["ratios"][s] for s in strat]
        ax.bar(range(len(strat)), vals, color=colors)
        ax.set_title(DS_LABEL[ds])
        ax.set_xticks(range(len(strat)))
        ax.set_xticklabels(labels, fontsize=7.5, rotation=25, ha="right")
        ax.axhline(0, color="k", lw=.6)
        for i, v in enumerate(vals):
            ax.text(i, v + (1 if v >= 0 else -4), f"{v:.1f}", ha="center", fontsize=8)
    axes[0].set_ylabel("storage reduction vs raw (%)")
    fig.suptitle("Storage reduction by strategy (FastCDC, avg chunk 2 KiB)", fontsize=12)
    _save(fig, "fig1_staircase.png")


def fig_delta_gain():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.2))
    x = range(len(DS))
    bw = 0.26
    for k, algo in enumerate(ALGOS):
        pp = [get(ds, algo)["ratios"]["dedup_delta"] - get(ds, algo)["ratios"]["dedup_comp"] for ds in DS]
        cut = [100 * (1 - get(ds, algo)["sizes"]["dedup_delta"] / get(ds, algo)["sizes"]["dedup_comp"]) for ds in DS]
        a1.bar([i + (k - 1) * bw for i in x], pp, bw, label=algo, color=COLOR[algo])
        a2.bar([i + (k - 1) * bw for i in x], cut, bw, label=algo, color=COLOR[algo])
    for ax, title, unit in ((a1, "Extra reduction from delta stage\n(pp vs dedup + compression)", "pp"),
                            (a2, "Residual footprint removed by delta stage\n(% of dedup + compression size)", "%")):
        ax.set_xticks(list(x))
        ax.set_xticklabels([DS_LABEL[d] for d in DS])
        ax.set_ylabel(unit)
        ax.set_title(title, fontsize=10)
        ax.axhline(0, color="k", lw=.6)
        ax.legend()
    _save(fig, "fig2_delta_gain.png")


def fig_chunksize_sweep():
    avgs = [1024, 2048, 4096, 8192, 16384]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.2))
    for algo in ALGOS:
        dd = [get("git_repo", algo, a)["ratios"]["dedup_delta"] for a in avgs]
        dc = [get("git_repo", algo, a)["ratios"]["dedup_comp"] for a in avgs]
        a1.plot(avgs, dd, "-o", color=COLOR[algo], label=f"{algo} dedup+delta")
        a1.plot(avgs, dc, "--o", color=COLOR[algo], alpha=.5, label=f"{algo} dedup+comp")
        a2.plot(avgs, [x - y for x, y in zip(dd, dc)], "-o", color=COLOR[algo], label=algo)
    for ax in (a1, a2):
        ax.set_xscale("log", base=2)
        ax.set_xticks(avgs)
        ax.set_xticklabels([f"{a // 1024}K" for a in avgs])
        ax.set_xlabel("target average chunk size")
    a1.set_ylabel("storage reduction vs raw (%)")
    a1.set_title("git repo: reduction vs chunk size", fontsize=10)
    a1.legend(fontsize=6.5, loc="lower center", ncol=3)
    a2.set_ylabel("extra pp from delta stage")
    a2.set_title("git repo: delta-stage contribution vs chunk size", fontsize=10)
    a2.legend()
    _save(fig, "fig3_chunksize_sweep.png")


def fig_throughput():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4))
    x = range(len(DS))
    bw = 0.26
    for k, algo in enumerate(ALGOS):
        chunk = [get(ds, algo)["stats"]["chunk_MBps"] for ds in DS]
        pipe = [get(ds, algo)["stats"]["pipeline_MBps"] for ds in DS]
        bars = a1.bar([i + (k - 1) * bw for i in x], chunk, bw, label=algo, color=COLOR[algo])
        a1.bar_label(bars, fmt="%.0f", fontsize=6.5, padding=1)
        a2.bar([i + (k - 1) * bw for i in x], pipe, bw, label=algo, color=COLOR[algo])
    a1.set_yscale("log")
    a1.set_title("chunking throughput (MB/s, log)\nFSC does no hashing; CDC cost is the fair comparison", fontsize=9)
    a2.set_title("full pipeline throughput incl. resemblance + delta (MB/s)", fontsize=10)
    for ax in (a1, a2):
        ax.set_xticks(list(x))
        ax.set_xticklabels([DS_LABEL[d] for d in DS])
        ax.legend()
    _save(fig, "fig4_throughput.png")


def _save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(RES, name), dpi=150)
    plt.close(fig)
    print("wrote", name)


def main():
    fig_staircase()
    fig_delta_gain()
    fig_chunksize_sweep()
    fig_throughput()


if __name__ == "__main__":
    main()

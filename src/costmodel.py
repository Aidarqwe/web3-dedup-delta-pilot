import os
import json

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.normpath(os.path.join(HERE, "..", "results"))

COLLECTION_GiB = 100.0
PRICE_PER_GiB_YR = {"low": 0.01, "mid": 0.20, "high": 2.00}
EGRESS_PER_GiB = 0.05
CHUNKER = "FastCDC"
AVG = 2048

STRATEGIES = {
    "dedup": "IPFS today (dedup only)",
    "dedup_comp": "dedup + compression",
    "dedup_delta": "proposed (dedup + delta)",
    "filedag": "FileDAG-style whole-file delta",
}


def main():
    summary = json.load(open(os.path.join(RES, "summary.json")))
    out = ["# Filecoin cost projection", ""]
    out.append(f"Raw collection {COLLECTION_GiB:.0f} GiB, kept 1 year. "
               f"Storage price {'/'.join(map(str, PRICE_PER_GiB_YR.values()))} $/GiB/yr "
               f"(low/mid/high), client upload {EGRESS_PER_GiB} $/GiB. "
               f"Chunker {CHUNKER}, avg chunk {AVG} B.")
    out += ["", "```",
            f"{'dataset':10s} {'strategy':32s} {'GiB':>8s} {'$/yr low/mid/high':>24s} {'upload $':>9s}",
            "-" * 86]

    for ds in ("git_repo", "wiki"):
        sizes = summary[f"{ds}|{CHUNKER}|{AVG}"]["sizes"]
        for key, label in STRATEGIES.items():
            gib = COLLECTION_GiB * sizes[key] / sizes["raw"]
            lo, mid, hi = (gib * p for p in PRICE_PER_GiB_YR.values())
            out.append(f"{ds:10s} {label:32s} {gib:8.2f} "
                       f"{lo:6.2f}/{mid:6.2f}/{hi:7.2f} {gib * EGRESS_PER_GiB:9.2f}")
    out += ["```", ""]

    for ds in ("git_repo", "wiki"):
        sizes = summary[f"{ds}|{CHUNKER}|{AVG}"]["sizes"]
        now = COLLECTION_GiB * sizes["dedup"] / sizes["raw"]
        prop = COLLECTION_GiB * sizes["dedup_delta"] / sizes["raw"]
        saved, mid = now - prop, PRICE_PER_GiB_YR["mid"]
        out.append(f"- **{ds}**: proposed stores {prop:.2f} GiB vs {now:.2f} GiB "
                   f"({100 * (1 - prop / now):.0f}% less) -> ~${saved * mid:.2f}/yr storage "
                   f"+ ${saved * EGRESS_PER_GiB:.2f} upload saved per {COLLECTION_GiB:.0f} GiB, mid price.")

    path = os.path.join(RES, "cost_projection.md")
    open(path, "w").write("\n".join(out) + "\n")
    print("\n".join(out))
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()

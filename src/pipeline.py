import time
import hashlib

from resemblance import SuperFeatureIndex, super_features
from codec import comp, delta


def _sha(b):
    return hashlib.sha256(b).digest()


def run(versions, chunk_fn, cand_limit=8):
    raw_total = sum(len(v) for v in versions)
    out = {"raw": raw_total}

    out["comp_per_version"] = sum(comp(v) for v in versions)

    fd = comp(versions[0])
    for i in range(1, len(versions)):
        fd += delta(versions[i - 1], versions[i])
    out["filedag"] = fd

    t0 = time.perf_counter()
    per_version_chunks = [[v[s:e] for (s, e) in chunk_fn(v)] for v in versions]
    t_chunk = time.perf_counter() - t0
    n_chunks_total = sum(len(cs) for cs in per_version_chunks)

    # exact dedup, keeping first-seen order
    seen = {}
    for cs in per_version_chunks:
        for c in cs:
            seen.setdefault(_sha(c), c)
    unique_chunks = list(seen.values())
    n_unique = len(unique_chunks)
    dedup_bytes = sum(len(c) for c in unique_chunks)
    out["dedup"] = dedup_bytes
    out["dedup_comp"] = sum(comp(c) for c in unique_chunks)

    t1 = time.perf_counter()
    idx = SuperFeatureIndex()
    bases = []
    stored = 0
    n_delta = 0
    for c in unique_chunks:
        sfs = super_features(c)
        best = min((delta(bases[b], c) for b in idx.candidates(sfs, cand_limit)),
                   default=None)
        solo = comp(c)
        if best is not None and best < solo:
            stored += best
            n_delta += 1
        else:
            stored += solo
            bases.append(c)
            idx.add(len(bases) - 1, sfs)
    t_delta = time.perf_counter() - t1
    out["dedup_delta"] = stored

    stats = dict(
        raw_total=raw_total,
        n_versions=len(versions),
        n_chunks_total=n_chunks_total,
        n_unique=n_unique,
        avg_chunk_size=dedup_bytes / n_unique if n_unique else 0,
        n_delta_encoded=n_delta,
        pct_chunks_delta=100.0 * n_delta / n_unique if n_unique else 0,
        t_chunk_s=t_chunk,
        t_delta_s=t_delta,
        chunk_MBps=raw_total / 1e6 / t_chunk if t_chunk else 0,
        pipeline_MBps=raw_total / 1e6 / (t_chunk + t_delta) if (t_chunk + t_delta) else 0,
    )
    return out, stats


def ratios(sizes):
    """Absolute stored bytes -> reduction vs. raw, in percent."""
    raw = sizes["raw"]
    return {k: 100.0 * (1 - v / raw) for k, v in sizes.items() if k != "raw"}

# Deduplication + delta compression pilot

Preliminary experiment for the Master's thesis *"Analysis and Optimization of
Deduplication and Delta Compression for Web3 Storage (IPFS/Filecoin)"*.

Pipeline: **chunk → detect near-duplicates → delta-encode → project to Filecoin cost.**

## What it measures

For each dataset, the bytes kept under six strategies:

| strategy | |
|---|---|
| `comp_per_version` | zstd each version, no cross-version dedup |
| `filedag` | `v1 = zstd(v1)`, `v_i = delta(v_{i-1}, v_i)` — FileDAG-style whole-file delta |
| `dedup` | exact content-defined chunk dedup — what IPFS does today |
| `dedup_comp` | `dedup` + zstd each unique chunk |
| `dedup_delta` | `dedup` + delta-encode near-duplicate chunks — **the proposed pipeline** |

## Layout

```
src/
  chunking.py     FSC, FastCDC, AE
  resemblance.py  super-feature near-duplicate index
  codec.py        zstd compression + delta sizes
  datasets.py     build the datasets (pinned to a fixed date)
  pipeline.py     the six-strategy measurement
  experiment.py   run all jobs -> results/*.csv, summary.json
  costmodel.py    Filecoin cost projection
  plots.py        the four figures
results/          committed outputs (csv, json, figures, cost_projection.md)
data/             generated, git-ignored
```

## Run

```bash
pip install -r requirements.txt          # zstandard, matplotlib
cd src
python datasets.py       # ~10 s
python experiment.py     # ~2 min
python costmodel.py
python plots.py
```

`datasets.py` also takes a subset: `python datasets.py git wiki`.

## Datasets

- **git_repo** — `github.com/pallets/click`, the 20 commits before `CUTOFF`
  touching `src/`; each version is the concatenation of its text files.
- **wiki** — English Wikipedia article *Content-addressable storage*, the 20
  revisions before `CUTOFF`, via the MediaWiki API.
- **random_bin** — `os.urandom` blobs, zero correlation, control group.

`CUTOFF` (in `datasets.py`) pins both real sources to 2026-08-30 so results are
reproducible.

## Knobs

| file | knob |
|---|---|
| `datasets.py` | `CUTOFF`, `GIT_URL`, `GIT_NVERSIONS`, `WIKI_TITLE`, `WIKI_NREVS` |
| `experiment.py` | `PRIMARY_AVG`, `SWEEP_AVG` (chunk sizes) |
| `resemblance.py` | `W`, `K`, `SF` |
| `codec.py` | `LEVEL` |
| `costmodel.py` | `COLLECTION_GiB`, `PRICE_PER_GiB_YR`, `EGRESS_PER_GiB` |

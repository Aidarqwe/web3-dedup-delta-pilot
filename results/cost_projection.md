# Filecoin cost projection

Raw collection 100 GiB, kept 1 year. Storage price 0.01/0.2/2.0 $/GiB/yr (low/mid/high), client upload 0.05 $/GiB. Chunker FastCDC, avg chunk 2048 B.

```
dataset    strategy                              GiB        $/yr low/mid/high  upload $
--------------------------------------------------------------------------------------
git_repo   IPFS today (dedup only)              8.93   0.09/  1.79/  17.86      0.45
git_repo   dedup + compression                  3.13   0.03/  0.63/   6.25      0.16
git_repo   proposed (dedup + delta)             2.04   0.02/  0.41/   4.07      0.10
git_repo   FileDAG-style whole-file delta       1.15   0.01/  0.23/   2.31      0.06
wiki       IPFS today (dedup only)             15.64   0.16/  3.13/  31.27      0.78
wiki       dedup + compression                  7.90   0.08/  1.58/  15.81      0.40
wiki       proposed (dedup + delta)             5.83   0.06/  1.17/  11.66      0.29
wiki       FileDAG-style whole-file delta       2.09   0.02/  0.42/   4.19      0.10
```

- **git_repo**: proposed stores 2.04 GiB vs 8.93 GiB (77% less) -> ~$1.38/yr storage + $0.34 upload saved per 100 GiB, mid price.
- **wiki**: proposed stores 5.83 GiB vs 15.64 GiB (63% less) -> ~$1.96/yr storage + $0.49 upload saved per 100 GiB, mid price.

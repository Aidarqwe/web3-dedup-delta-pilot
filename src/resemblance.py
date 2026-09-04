import random

W = 16          # rolling window, bytes
K = 12          # features
SF = 4          # super-features

_M = (1 << 61) - 1                      # Mersenne prime modulus
_rng = random.Random(0xC0FFEE)
_A = [_rng.randrange(1, _M) for _ in range(K)]
_B = [_rng.randrange(0, _M) for _ in range(K)]


def super_features(data: bytes):
    """SF-tuple for a chunk, or None if it is shorter than the window."""
    n = len(data)
    if n < W:
        return None

    base = 257
    high = pow(base, W - 1, _M)
    h = 0
    for i in range(W):
        h = (h * base + data[i]) % _M
    windows = [h]
    for i in range(W, n):
        h = ((h - data[i - W] * high) * base + data[i]) % _M
        windows.append(h)

    feats = [min((_A[k] * wv + _B[k]) % _M for wv in windows) for k in range(K)]

    per = K // SF
    sfs = []
    for s in range(SF):
        acc = 1469598103934665603                        # FNV-1a 64-bit
        for g in feats[s * per:(s + 1) * per]:
            acc = ((acc ^ g) * 1099511628211) & ((1 << 64) - 1)
        sfs.append(acc)
    return tuple(sfs)


class SuperFeatureIndex:
    """super-feature value -> chunk ids carrying it."""

    def __init__(self):
        self.buckets = [dict() for _ in range(SF)]

    def add(self, chunk_id, sfs):
        if sfs is None:
            return
        for s in range(SF):
            self.buckets[s].setdefault(sfs[s], []).append(chunk_id)

    def candidates(self, sfs, limit=8):
        """Chunk ids sharing >= 1 super-feature, most shared first."""
        if sfs is None:
            return []
        score = {}
        for s in range(SF):
            for cid in self.buckets[s].get(sfs[s], ()):
                score[cid] = score.get(cid, 0) + 1
        return sorted(score, key=lambda c: -score[c])[:limit]

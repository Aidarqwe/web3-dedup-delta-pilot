import random


def fsc(data: bytes, size: int = 512):
    """Fixed-size chunking (IPFS default). One inserted byte shifts every
    following boundary, which is the weakness CDC fixes."""
    return [(i, min(i + size, len(data))) for i in range(0, len(data), size)]

_rng = random.Random(1337)
_GEAR = [_rng.getrandbits(32) for _ in range(256)]


def fastcdc(data: bytes, avg_size: int = 512, min_size: int = 128, max_size: int = 2048):
    """Gear-hash CDC with normalized chunk sizes: H = (H << 1) + GEAR[byte],
    cut on H & mask == 0, using a stricter mask before avg_size and a looser
    one after so sizes concentrate around avg_size."""
    bits = max(1, avg_size.bit_length() - 1)
    mask_small = (1 << (bits + 1)) - 1
    mask_large = (1 << (bits - 1)) - 1

    n = len(data)
    chunks = []
    start = 0
    while start < n:
        i = min(start + min_size, n)          # FastCDC: skip to min_size
        h = 0
        cut = None
        while i < n:
            h = ((h << 1) + _GEAR[data[i]]) & 0xFFFFFFFF
            mask = mask_small if (i - start) < avg_size else mask_large
            if (h & mask) == 0 or (i - start) >= max_size:
                cut = i + 1
                break
            i += 1
        end = cut if cut is not None else n
        chunks.append((start, end))
        start = end
    return chunks


def ae(data: bytes, avg_size: int = 512):
    """Asymmetric Extremum (Zhang et al., 2015). Hash-less: find a local
    maximum byte, cut w bytes past it. w ~ avg_size / 2 to hit the target."""
    w = max(8, avg_size // 2)
    n = len(data)
    chunks = []
    start = 0
    while start < n:
        best_pos, best_val = start, data[start]
        cut = None
        j = start + 1
        while j < n:
            if data[j] > best_val:
                best_val, best_pos = data[j], j
            if j - best_pos >= w:
                cut = min(best_pos + w, n)
                break
            j += 1
            if j - start >= avg_size * 4:     # cap pathological long chunks
                cut = j
                break
        end = cut if cut is not None else n
        if end <= start:
            end = min(start + 1, n)
        chunks.append((start, end))
        start = end
    return chunks

import zstandard as zstd

LEVEL = 19

_cctx = zstd.ZstdCompressor(level=LEVEL)
_dict_cache = {}


def comp(data: bytes) -> int:
    return len(_cctx.compress(data)) if data else 0


def _compressor_for(base: bytes):
    # Building the dictionary compressor is expensive; cache it per base object.
    key = id(base)
    c = _dict_cache.get(key)
    if c is None:
        cd = zstd.ZstdCompressionDict(base, dict_type=zstd.DICT_TYPE_RAWCONTENT)
        c = zstd.ZstdCompressor(level=LEVEL, dict_data=cd)
        if len(_dict_cache) > 256:
            _dict_cache.clear()
        _dict_cache[key] = c
    return c


def delta(base: bytes, target: bytes) -> int:
    if not target:
        return 0
    if not base:
        return comp(target)
    return len(_compressor_for(base).compress(target))

import tempfile
from pathlib import Path

from diskcache import Cache

# todo if appserver use /tmp/cache
# cache_dir = Path("/tmp/cache2")
from netwrck.utils import debug

if not debug:
    cache_dir = Path("/tmp/cache4")
else:
    cache_dir = Path("cache")
cache_dir.mkdir(exist_ok=True, parents=True)
cache = Cache(str(cache_dir))

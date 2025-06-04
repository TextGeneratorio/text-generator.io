try:
    import httpx
except ImportError:  # pragma: no cover - optional dependency
    httpx = None

if httpx:
    _old_init = httpx.Client.__init__

    def fixed_init(self, *args, **kwargs):
        # Remove 'app' from kwargs if present
        kwargs.pop('app', None)
        _old_init(self, *args, **kwargs)

    httpx.Client.__init__ = fixed_init

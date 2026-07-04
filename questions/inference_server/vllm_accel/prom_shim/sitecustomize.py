"""Patches prometheus_fastapi_instrumentator._get_route_name: vLLM mounts an
_IncludedRouter with no .path, crashing every instrumented request. Loaded via
PYTHONPATH from serve_generic.sh (lives in-repo; /nvme0n1-disk/tmp gets wiped)."""
try:
    from prometheus_fastapi_instrumentator import routing as _pfi_routing
    _orig = _pfi_routing._get_route_name

    def _safe_get_route_name(scope, routes, route_name=None):
        try:
            return _orig(scope, routes, route_name)
        except AttributeError:
            return None

    _pfi_routing._get_route_name = _safe_get_route_name
except Exception:
    pass

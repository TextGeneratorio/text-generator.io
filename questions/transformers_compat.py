"""Compatibility helpers for optional transformers backends."""

from __future__ import annotations

import sys


def disable_broken_torchvision_for_text_pipeline() -> None:
    """Let transformers text pipelines import when torchvision is installed but broken.

    Transformers imports image pipeline modules while building its pipeline
    registry. In a text-only path that should not require torchvision, but an
    incompatible torchvision build can still fail the import first.
    """

    try:
        import torchvision  # noqa: F401

        return
    except Exception:
        for module_name in list(sys.modules):
            if module_name == "torchvision" or module_name.startswith("torchvision."):
                sys.modules.pop(module_name, None)

    try:
        import transformers.utils as transformers_utils
        import transformers.utils.import_utils as import_utils
    except Exception:
        return

    def _torchvision_unavailable() -> bool:
        return False

    import_utils.is_torchvision_available = _torchvision_unavailable
    transformers_utils.is_torchvision_available = _torchvision_unavailable

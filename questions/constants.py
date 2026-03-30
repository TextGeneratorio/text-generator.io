import os

# Default model layout:
# - TGZ/TGC: best reasoning/chat model (Qwen3.5-4B)
# - TG: faster/smaller model for autocomplete + low-latency routes
#
# Override options:
# - WEIGHTS_PATH_TGZ / WEIGHTS_PATH_TGC / WEIGHTS_PATH_TG
# - Legacy WEIGHTS_PATH still works for TG.
weights_path_tgz = os.getenv("WEIGHTS_PATH_TGZ", "models/Qwen3.5-4B")
weights_path_tgc = os.getenv("WEIGHTS_PATH_TGC", "models/Qwen3.5-4B")
weights_path_tg = os.getenv("WEIGHTS_PATH_TG", os.getenv("WEIGHTS_PATH", "models/SmolLM3-3B"))

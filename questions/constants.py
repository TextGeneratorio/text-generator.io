import os

# Default local paths for the Qwen3.5 model. These paths can be
# overridden with the respective environment variables if a different
# location is desired.
weights_path_tgz = os.getenv("WEIGHTS_PATH_TGZ", "models/Qwen3.5-4B")
weights_path_tgc = os.getenv("WEIGHTS_PATH_TGC", "models/Qwen3.5-4B")
weights_path_tg = os.getenv("WEIGHTS_PATH", "models/Qwen3.5-4B")

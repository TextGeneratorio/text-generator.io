import os

# Default local paths for the SmolLM3 model family. These paths can be
# overridden with the respective environment variables if a different
# location is desired.
weights_path_tgz = os.getenv("WEIGHTS_PATH_TGZ", "models/SmolLM3-3B")
weights_path_tgc = os.getenv("WEIGHTS_PATH_TGC", "models/SmolLM3-3B")
weights_path_tg = os.getenv("WEIGHTS_PATH", "models/SmolLM3-3B")

import os
# Default to the multimodal Gemma model which can handle both text generation
# and image description. The environment variables allow overriding the model
# path, but when unset a small Gemma checkpoint from HuggingFace is used.
weights_path_tgz = os.getenv("WEIGHTS_PATH_TGZ", "google/gemma-3n-e4b-it")
weights_path_tgc = os.getenv("WEIGHTS_PATH_TGC", "google/gemma-3n-e4b-it")
weights_path_tg = os.getenv("WEIGHTS_PATH", "google/gemma-3n-e4b-it")

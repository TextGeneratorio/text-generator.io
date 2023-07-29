from pathlib import Path
import os

import rollbar

from sellerinfo import ROLLBAR_TOKEN
debug = (
    os.environ.get("SERVER_SOFTWARE", "").startswith("Development")
    or os.environ.get("IS_DEVELOP", "") == 1
    or Path("models/debug.env").exists()
)
environment = "development" if debug else "production"
rollbar.init(
  access_token=ROLLBAR_TOKEN,
  environment=environment,
  code_version='1.0'
)
# /ai-chat/V1-ULTRAKILL

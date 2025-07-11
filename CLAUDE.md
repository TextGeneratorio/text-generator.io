tools:
use uv - edit requirements.in files and run uv pip compile requirements.in -o requirements.txt
uv pip install -r requirements.txt
uv pip install -r dev-requirements.txt
uv pip install -r questions/inference_server/requirements.txt


PYTHONPATH=. pytest tests/test_chat_openai.py
tools:
use uv - edit requirements.in files and run uv pip compile requirements.in -o requirements.txt
uv pip install -r requirements.txt
uv pip install -r dev-requirements.txt
uv pip install -r questions/inference_server/requirements.txt

read from mainserver.log thats autoreloaded NEVER try run the server yourself or pkill ever
tail -n 200 mainserver.log

we are running the server on localhost:4444
can use curl

PYTHONPATH=. pytest tests/test_chat_openai.py
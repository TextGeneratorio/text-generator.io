from fastapi import FastAPI
import json
import time
import argparse
from uvicorn import Config, Server
from pathlib import Path

# Import our existing FastAPI app from inference_server
from questions.inference_server.inference_server import app as inference_app

# Optional: you could store or manipulate model data, configs, etc. if desired
model_data = {
    "object": "list",
    "data": []
}
configs = []

def run(config_path: str = None, host: str = "0.0.0.0", port: int = 3000):
    """
    Wrap the existing FastAPI 'inference_app' in a runpod-esque style.
    Currently, this just starts up the server in a way similar to the example.
    """
    # You may load any configs here if needed
    if config_path:
        config_path = Path(config_path)
        if config_path.exists():
            with open(config_path) as fp:
                config_dict = json.load(fp)
            # Here you can adapt or process config_dict as needed
            # For now, we just demonstrate reading and ignoring it.
    
    # Launch server
    config = Config(
        app=inference_app,
        host=host,
        port=port,
        log_level="info",
    )
    server = Server(config=config)
    server.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="Path to the config file", type=str, default=None)
    parser.add_argument("--host", help="Host", type=str, default="0.0.0.0")
    parser.add_argument("--port", help="Port", type=int, default=3000)
    args = parser.parse_args()

    run(args.config, args.host, args.port)

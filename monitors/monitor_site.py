#!/usr/bin/env python3
import time
import subprocess
import urllib.request
from urllib.error import URLError, HTTPError
from datetime import datetime, timezone

URL = "https://text-generator.io"
CHECK_INTERVAL = 900  # 15 minutes
LOG_FILE = "/home/lee/code/20-questions/monitors/monitor_site.log"

CLAUDE_PROMPT = """text-generator.io is DOWN and not responding.

Investigate and fix this issue. Here's what you need to know:

## Services
- Main app: supervisor process `text-generator-main` on port 8299
- Inference server: supervisor process `text-generator-inference` on port 9080

## Commands to check status
- sudo supervisorctl status
- curl http://localhost:8299/
- curl http://localhost:9080/liveness_check

## Logs
- Main app: /var/log/supervisor/text-generator-main.log and text-generator-main-error.log
- Inference: /var/log/supervisor/text-generator-inference.log and text-generator-inference-error.log

## To restart services
- sudo supervisorctl restart text-generator-main
- sudo supervisorctl restart text-generator-inference

## Project location
/home/lee/code/20-questions

## Common issues
- Check if postgres is running: sudo systemctl status postgresql
- Check disk space: df -h
- Check memory: free -h

Fix the issue so the site responds again."""


def log(message: str) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    with open(LOG_FILE, "a") as fh:
        fh.write(f"{ts} {message}\n")
    print(f"{ts} {message}")


def check_site(url: str, timeout: int = 15) -> bool:
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 Monitor"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status < 400
    except (HTTPError, URLError, ValueError, TimeoutError) as e:
        log(f"Error checking {url}: {e}")
        return False


def run_claude_agent() -> None:
    log("Launching claude agent to investigate...")
    subprocess.Popen(
        ["claude", "--dangerously-skip-permissions", "-p", CLAUDE_PROMPT],
        cwd="/home/lee/code/20-questions",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main():
    log(f"Starting monitor for {URL}, interval={CHECK_INTERVAL}s")
    last_down = False

    while True:
        ok = check_site(URL)
        if ok:
            log(f"{URL} UP")
            last_down = False
        else:
            log(f"{URL} DOWN")
            if not last_down:
                run_claude_agent()
            last_down = True

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()

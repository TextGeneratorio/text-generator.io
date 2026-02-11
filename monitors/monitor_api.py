#!/usr/bin/env python3
import time
import subprocess
import fcntl
import urllib.request
from urllib.error import URLError, HTTPError
from datetime import datetime, timezone

URL_EXTERNAL = "https://api.text-generator.io/liveness_check"
URL_LOCAL = "http://localhost:9080/liveness_check"
CHECK_INTERVAL = 300  # seconds
FAIL_THRESHOLD = 2  # consecutive failures
RESTART_COOLDOWN = 600  # seconds
LOG_FILE = "/nvme0n1-disk/code/text-generator.io/monitors/monitor_api.log"
LOCK_FILE = "/tmp/text-generator-monitor-api.lock"


def log(message: str) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    with open(LOG_FILE, "a") as fh:
        fh.write(f"{ts} {message}\n")
    print(f"{ts} {message}")


def check_endpoint(url: str, timeout: int = 10) -> bool:
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


def restart_systemd_service(service_name: str) -> None:
    unit = service_name if service_name.endswith(".service") else f"{service_name}.service"
    log(f"Restarting systemd service: {unit}")
    result = subprocess.run(
        ["/usr/bin/sudo", "-n", "systemctl", "restart", unit],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        log(f"Systemd restart failed for {unit}: {result.stderr.strip()}")
    else:
        log(f"Restarted {unit}")


def restart_supervisor_service(service_name: str) -> None:
    log(f"Restarting supervisor service: {service_name}")
    result = subprocess.run(
        ["/usr/bin/sudo", "-n", "supervisorctl", "restart", service_name],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        log(f"Supervisor restart failed for {service_name}: {result.stderr.strip()}")
    else:
        log(f"Restarted {service_name}: {result.stdout.strip()}")


def acquire_lock():
    try:
        lock_fh = open(LOCK_FILE, "w")
        fcntl.flock(lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return lock_fh
    except BlockingIOError:
        log("Another monitor_api instance is running; exiting.")
        return None


def main():
    lock_fh = acquire_lock()
    if lock_fh is None:
        return
    log(f"Starting monitor for {URL_EXTERNAL} (local {URL_LOCAL}), interval={CHECK_INTERVAL}s")
    last_restart_inference = 0.0
    last_restart_cloudflared = 0.0
    local_failures = 0
    external_failures = 0

    while True:
        local_ok = check_endpoint(URL_LOCAL)
        if not local_ok:
            local_failures += 1
            external_failures = 0
            log(f"LOCAL DOWN ({local_failures}/{FAIL_THRESHOLD})")
            if local_failures >= FAIL_THRESHOLD and time.time() - last_restart_inference > RESTART_COOLDOWN:
                restart_systemd_service("text-generator-inference")
                last_restart_inference = time.time()
                local_failures = 0
        else:
            local_failures = 0
            external_ok = check_endpoint(URL_EXTERNAL)
            if external_ok:
                external_failures = 0
                log("LOCAL UP / EXTERNAL UP")
            else:
                external_failures += 1
                log(f"EXTERNAL DOWN ({external_failures}/{FAIL_THRESHOLD})")
                if external_failures >= FAIL_THRESHOLD and time.time() - last_restart_cloudflared > RESTART_COOLDOWN:
                    restart_supervisor_service("cloudflared-inference")
                    last_restart_cloudflared = time.time()
                    external_failures = 0

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()

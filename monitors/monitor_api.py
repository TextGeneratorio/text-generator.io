#!/usr/bin/env python3
import fcntl
import os
import subprocess
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from monitoring import service_probe

LOCAL_CHECK_LABEL = "compatibility worker on 127.0.0.1:9083"
EXTERNAL_CHECK_LABEL = "https://api.text-generator.io contract endpoints"
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


def _format_failures(results: list[service_probe.ProbeResult]) -> str:
    failures = [asdict(result) for result in results if not result.ok]
    return "; ".join(
        f"{item['name']}: {item['detail']}" for item in failures
    ) or "unknown failure"


def check_local_contracts() -> bool:
    results = [
        service_probe.probe_systemd_service("text-generator-inference.service", expected_port=9083),
        service_probe.probe_feature_extraction(
            "compat:feature-extraction",
            "http://127.0.0.1:9083/api/v1/feature-extraction",
        ),
        service_probe.probe_openai_embeddings(
            "compat:openai-embeddings",
            "http://127.0.0.1:9083/v1/embeddings",
        ),
    ]
    if all(result.ok for result in results):
        return True
    log(f"Local contract check failed: {_format_failures(results)}")
    return False


def check_external_contracts() -> bool:
    secret = os.getenv("TEXTGEN_MONITOR_SECRET")
    results = [
        service_probe.probe_feature_extraction(
            "production:feature-extraction",
            "https://api.text-generator.io/api/v1/feature-extraction",
            secret=secret,
        ),
        service_probe.probe_openai_embeddings(
            "production:openai-embeddings",
            "https://api.text-generator.io/v1/embeddings",
            secret=secret,
        ),
    ]
    if all(result.ok for result in results):
        return True
    log(f"External contract check failed: {_format_failures(results)}")
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
    log(
        f"Starting monitor for {EXTERNAL_CHECK_LABEL} "
        f"(local {LOCAL_CHECK_LABEL}), interval={CHECK_INTERVAL}s"
    )
    last_restart_inference = 0.0
    last_restart_cloudflared = 0.0
    local_failures = 0
    external_failures = 0

    while True:
        local_ok = check_local_contracts()
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
            external_ok = check_external_contracts()
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

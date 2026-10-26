#!/usr/bin/env python3
"""
Watch server/client error logs and invoke Codex at most once per cooldown window.

The first run initializes offsets at EOF so historical 500s do not immediately
trigger an agent. Use --scan-existing for a one-off backfill.
"""

import argparse
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    from monitoring import service_probe
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from monitoring import service_probe

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNTIME_DIR = Path(os.getenv("TEXTGEN_MONITORING_RUNTIME_DIR", REPO_ROOT / "monitoring" / "runtime"))
STATE_FILE = RUNTIME_DIR / "500-monitor-state.json"
LOG_FILE = RUNTIME_DIR / "500-monitor.log"
CODEX_LOG_FILE = RUNTIME_DIR / "codex-500-monitor.log"
LOCK_FILE = Path("/tmp/text-generator-500-monitor.lock")

_SHIM = Path.home() / ".local/monitor-bin/codex"  # local codex -> stock -> deepseek-flash -> muse
CODEX_LOCAL = os.environ.get("CODEX_LOCAL", str(_SHIM) if _SHIM.is_file() else "/home/administrator/code/codex/codex-rs/target/release/codex")
CODEX_CMD = [
    CODEX_LOCAL,
    "exec",
    "--yolo3",
    "-m",
    os.getenv("TEXTGEN_MONITOR_CODEX_MODEL", "gpt-6.1-sol"),
    "--config",
    "model_reasoning_effort=medium",
]

DEFAULT_LOG_SOURCES = [
    REPO_ROOT / "mainserver.log",
    Path("/var/log/supervisor/text-generator-site.log"),
    Path("/var/log/supervisor/text-generator-site-error.log"),
    Path("/var/log/supervisor/text-generator-inference.log"),
    Path("/var/log/supervisor/text-generator-inference-error.log"),
    RUNTIME_DIR / "frontend-errors.jsonl",
]

SERVER_500_RE = re.compile(
    r"(Status:\s*5\d\d|\"(?:GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\s+.*\"\s+5\d\d\b|Exception in ASGI|"
    r"\bTraceback \(most recent call last\))",
    re.IGNORECASE,
)
# 502/503/504 are upstream/backpressure/restart windows (synthetic probes cover
# real outages); disconnects, cancellations and DNS/timeouts are not code defects.
SERVER_NOISE_RE = re.compile(
    r"Status:\s*50[234]\b|\"\s+50[234]\b|ClientDisconnect|BrokenPipe|broken pipe|ConnectionReset|"
    r"connection reset|CancelledError|context canceled|deadline exceeded|Temporary failure in name resolution|"
    r"i/o timeout|no such host|rate.?limit|\b429\b|upstream",
    re.IGNORECASE,
)
VOLATILE_RE = re.compile(
    r"\x1b\[[0-9;]*m|\[\d+m|\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}\S*|\d+\.\d+\.\d+\.\d+(?::\d+)?|"
    r"[\w.+-]+@[\w-]+\.[\w.-]+|\?\S*|\b[0-9a-f]{8}-[0-9a-f-]{27}\b|\b[0-9a-f]{12,}\b|\d+(?:\.\d+)?",
    re.IGNORECASE,
)
DEFAULT_SIGNAL_COUNT = 3
DEFAULT_SIGNAL_SCANS = 2
DEFAULT_SIGNAL_WINDOW_SECONDS = 6 * 60 * 60
DEFAULT_SIGNAL_COOLDOWN_SECONDS = 24 * 60 * 60
DEFAULT_RESTART_GRACE_SECONDS = 120
RESTART_GRACE_UNITS = ("omniserve-native.service", "text-generator-inference.service", "text-generator-site.service")
SYNTHETIC_PROBE_RE = re.compile(r"\bSynthetic probe .*failure\b|\bsynthetic probe .+ failed:", re.IGNORECASE)
TRANSIENT_SYNTHETIC_TRANSPORT_RE = re.compile(
    r"\bURLError:\s*<urlopen error \[Errno -3\] Temporary failure in name resolution>",
    re.IGNORECASE,
)
NON_ACTIONABLE_IMAGE_GENERATION_BACKPRESSURE_RE = re.compile(
    r"Status:\s*503\s+synthetic probe "
    r"omniserve-native:(?:lora-image-generation|image-generation) failed: "
    r"HTTP 503 or invalid image contract",
    re.IGNORECASE,
)
INCIDENT_SECTION_RE = re.compile(
    r"^## (?P<source>.+?)\n\n```\n(?P<text>.*?)\n```",
    re.MULTILINE | re.DOTALL,
)
CLIENT_EVENT_TYPES = {"window_error", "unhandledrejection", "fetch_5xx", "fetch_exception", "resource_error"}
SEARCH_CRAWLER_UA_RE = re.compile(
    r"(bot|crawler|spider|slurp|yandex|bingpreview|duckduckbot|baiduspider|facebookexternalhit|"
    r"petalbot|semrushbot|ahrefsbot)",
    re.IGNORECASE,
)
BROWSER_EXTENSION_URL_RE = re.compile(r"\b(?:chrome|moz|safari|ms-browser)-extension://", re.IGNORECASE)
EXTENSION_OBJECT_NOT_FOUND_RE = re.compile(
    r"^Object Not Found Matching Id:\d+, MethodName:update, ParamCount:\d+$"
)
NON_ACTIONABLE_WALLET_PROVIDER_MESSAGES = {
    "The provider is disconnected from all chains.",
}
TEXT_GENERATOR_HOSTS = {
    "text-generator.io",
    "www.text-generator.io",
    "api.text-generator.io",
    "text-generatorstatic.text-generator.io",
}
NON_ACTIONABLE_IMAGE_PATHS = {
    "/static/img/android-chrome-192x192.png",
    "/static/img/askfelix-robot-icon-transp.png",
    "/static/img/codex-infinity-logo.webp",
    "/static/img/dictatorflow-logo.webp",
    "/static/img/ebank-logo-removebg-full387.webp",
    "/static/img/evangeler-logo.png",
    "/static/img/journeai-logo.svg",
    "/static/img/netwrck-logo-colord256.png",
    "/static/img/openpaths-logo.webp",
    "/static/img/v5games-logo.webp",
}
NON_ACTIONABLE_FIRST_PARTY_STYLESHEET_PATHS = {
    "/static/css/subscription-modal.css",
    "/static/libs/codemirror.css",
    "/static/libs/select2/dist/css/select2.min.css",
    "/static/libs/styles/atom-one-dark.css",
    "/static/libs/styles/default.css",
}
NON_ACTIONABLE_FIRST_PARTY_SCRIPT_PATHS = {
    "/static/js/material.min.js",
}
NON_ACTIONABLE_AUTH_PROBE_PATHS = {
    "/api/current-user",
    "/api/get-user/stripe-usage",
}
NON_ACTIONABLE_THIRD_PARTY_RESOURCE_PATHS = {
    ("translate.googleapis.com", "/translate_static/css/translateelement.css"),
    ("js.stripe.com", "/v3/"),
    ("static.cloudflareinsights.com", "/beacon.min.js"),
    ("indiehunt.io", "/badges/indiehunt-badge-light.svg"),
    ("v5games.com", "/"),
    ("zmstat.com", "/"),
}
MAX_EXCERPT_CHARS = 70000
DEFAULT_INTERVAL_SECONDS = 900
DEFAULT_CODEX_COOLDOWN_SECONDS = 12 * 60 * 60
DEFAULT_SYNTHETIC_RECHECK_DELAY_SECONDS = 30
DEFAULT_INFREQUENT_PROBE_INTERVAL_SECONDS = 10 * 60 * 60
DEFAULT_NATIVE_LLM_RESTART_COOLDOWN_SECONDS = 30 * 60
NATIVE_LLM_RESTART_FAILURE_NAMES = {
    "omniserve-native:generate",
    "compat:generate",
    "production:generate",
    "production:autocomplete",
}
NATIVE_DATA_PLANE_REQUIRED_FAILURE_NAMES = {
    "omniserve-native:generate",
    "production:generate",
    "production:autocomplete",
}
NON_ACTIONABLE_IMAGE_GENERATION_BACKPRESSURE_FAILURE_NAMES = {
    "omniserve-native:lora-image-generation",
    "omniserve-native:image-generation",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_runtime_dir() -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    (RUNTIME_DIR / "frontend-errors.jsonl").touch(exist_ok=True)


def log(message: str) -> None:
    ensure_runtime_dir()
    line = f"{utc_now()} {message}"
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    print(line)


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"files": {}, "last_codex_run_ts": 0.0, "pending_incidents": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"files": {}, "last_codex_run_ts": 0.0, "pending_incidents": []}


def save_state(path: Path, state: dict[str, Any]) -> None:
    ensure_runtime_dir()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def acquire_lock():
    lock_fh = open(LOCK_FILE, "w")
    try:
        fcntl.flock(lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        log("Another 500 monitor instance is running; exiting.")
        return None
    return lock_fh


def file_identity(path: Path) -> dict[str, int]:
    stat = path.stat()
    return {"inode": stat.st_ino, "size": stat.st_size}


def read_new_text(path: Path, state: dict[str, Any], scan_existing: bool) -> str:
    key = str(path)
    if not path.exists():
        return ""

    ident = file_identity(path)
    file_state = state.setdefault("files", {}).get(key)
    if not file_state:
        offset = 0 if scan_existing else ident["size"]
        state["files"][key] = {"inode": ident["inode"], "offset": ident["size"]}
        if offset == ident["size"]:
            return ""
    else:
        offset = int(file_state.get("offset", 0))
        if file_state.get("inode") != ident["inode"] or offset > ident["size"]:
            offset = 0

    with path.open("rb") as fh:
        fh.seek(offset)
        raw = fh.read()

    state["files"][key] = {"inode": ident["inode"], "offset": ident["size"]}
    return raw.decode("utf-8", errors="replace")


def is_search_crawler(user_agent: str | None) -> bool:
    return bool(user_agent and SEARCH_CRAWLER_UA_RE.search(user_agent))


def is_text_generator_url(url: str | None) -> bool:
    if not url:
        return False
    try:
        host = urlparse(url).hostname
    except ValueError:
        return False
    return host in TEXT_GENERATOR_HOSTS


def get_record_user_agent(record: dict[str, Any]) -> str | None:
    user_agent = record.get("user_agent")
    payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
    page = payload.get("page") if isinstance(payload, dict) else {}
    if not user_agent and isinstance(page, dict):
        user_agent = page.get("userAgent")
    return user_agent


def is_non_actionable_auth_probe(url: str | None) -> bool:
    if not url:
        return False
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    return parsed.path in NON_ACTIONABLE_AUTH_PROBE_PATHS and (
        parsed.hostname is None or parsed.hostname in TEXT_GENERATOR_HOSTS
    )


def is_non_actionable_image_resource_error(event: dict[str, Any]) -> bool:
    if event.get("type") != "resource_error":
        return False
    if str(event.get("tagName", "")).upper() != "IMG":
        return False

    url = event.get("sourceUrl")
    if not url:
        return False
    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    is_text_generator_asset = parsed.hostname is None or parsed.hostname in TEXT_GENERATOR_HOSTS
    return is_text_generator_asset and parsed.path in NON_ACTIONABLE_IMAGE_PATHS


def is_non_actionable_first_party_stylesheet_error(event: dict[str, Any]) -> bool:
    if event.get("type") != "resource_error":
        return False
    if str(event.get("tagName", "")).upper() != "LINK":
        return False

    url = event.get("sourceUrl")
    if not url:
        return False
    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    is_text_generator_asset = parsed.hostname is None or parsed.hostname in TEXT_GENERATOR_HOSTS
    return is_text_generator_asset and parsed.path in NON_ACTIONABLE_FIRST_PARTY_STYLESHEET_PATHS


def is_non_actionable_first_party_script_error(event: dict[str, Any]) -> bool:
    if event.get("type") != "resource_error":
        return False
    if str(event.get("tagName", "")).upper() != "SCRIPT":
        return False

    url = event.get("sourceUrl")
    if not url:
        return False
    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    is_text_generator_asset = parsed.hostname is None or parsed.hostname in TEXT_GENERATOR_HOSTS
    return is_text_generator_asset and parsed.path in NON_ACTIONABLE_FIRST_PARTY_SCRIPT_PATHS


def is_non_actionable_third_party_resource_error(event: dict[str, Any]) -> bool:
    if event.get("type") != "resource_error":
        return False

    url = event.get("sourceUrl")
    if not url:
        return False
    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    if parsed.hostname in TEXT_GENERATOR_HOSTS:
        return False

    if parsed.hostname == "cdnjs.cloudflare.com" and parsed.path.startswith("/ajax/libs/highlight.js/"):
        return str(event.get("tagName", "")).upper() in {"LINK", "SCRIPT"}

    return (parsed.hostname, parsed.path) in NON_ACTIONABLE_THIRD_PARTY_RESOURCE_PATHS


def is_crawler_resource_noise(record: dict[str, Any], event: dict[str, Any]) -> bool:
    user_agent = get_record_user_agent(record)
    if not is_search_crawler(user_agent):
        return False

    event_type = event.get("type")
    if event_type == "resource_error":
        return bool(event.get("sourceUrl"))

    if event_type == "window_error":
        return (
            event.get("message") == "Script error."
            and not event.get("filename")
            and event.get("lineno") is None
            and event.get("colno") is None
        )

    return False


def is_untriageable_cross_origin_script_error(event: dict[str, Any]) -> bool:
    if event.get("type") != "window_error":
        return False
    if event.get("message") != "Script error.":
        return False
    if event.get("filename") or event.get("lineno") is not None or event.get("colno") is not None:
        return False

    error = event.get("error")
    return error in (None, {}) and not event.get("stack")


def is_non_actionable_auth_probe_exception(event: dict[str, Any]) -> bool:
    return event.get("type") == "fetch_exception" and is_non_actionable_auth_probe(event.get("url"))


def has_browser_extension_url(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(BROWSER_EXTENSION_URL_RE.search(value))
    if isinstance(value, dict):
        return any(has_browser_extension_url(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(has_browser_extension_url(item) for item in value)
    return False


def is_probable_extension_object_rejection(event: dict[str, Any]) -> bool:
    if event.get("type") != "unhandledrejection":
        return False

    reason = event.get("reason") if isinstance(event.get("reason"), dict) else {}
    message = event.get("message") or reason.get("message")
    stack = reason.get("stack")
    return isinstance(message, str) and not stack and bool(EXTENSION_OBJECT_NOT_FOUND_RE.match(message))


def is_non_actionable_wallet_provider_rejection(event: dict[str, Any]) -> bool:
    if event.get("type") != "unhandledrejection":
        return False

    reason = event.get("reason") if isinstance(event.get("reason"), dict) else {}
    message = event.get("message") or reason.get("message")
    stack = reason.get("stack")
    return isinstance(message, str) and not stack and message in NON_ACTIONABLE_WALLET_PROVIDER_MESSAGES


def is_transient_synthetic_probe_transport_failure(line: str) -> bool:
    return bool(TRANSIENT_SYNTHETIC_TRANSPORT_RE.search(line))


def is_non_actionable_image_generation_backpressure_line(line: str) -> bool:
    return bool(NON_ACTIONABLE_IMAGE_GENERATION_BACKPRESSURE_RE.search(line))


def is_non_actionable_synthetic_probe_failure_line(line: str) -> bool:
    return (
        is_transient_synthetic_probe_transport_failure(line)
        or is_non_actionable_image_generation_backpressure_line(line)
    )


def is_non_actionable_image_generation_backpressure_result(
    result: service_probe.ProbeResult,
) -> bool:
    return (
        result.name in NON_ACTIONABLE_IMAGE_GENERATION_BACKPRESSURE_FAILURE_NAMES
        and result.status == 503
        and "HTTP 503" in result.detail
    )


def frontend_event_matches(line: str) -> bool:
    try:
        record = json.loads(line)
    except json.JSONDecodeError:
        return False
    payload = record.get("payload") if isinstance(record, dict) else {}
    event = payload.get("event") if isinstance(payload, dict) else {}
    event_type = event.get("type") if isinstance(event, dict) else None
    if event_type not in CLIENT_EVENT_TYPES:
        return False
    if is_crawler_resource_noise(record, event):
        return False
    if is_untriageable_cross_origin_script_error(event):
        return False
    if is_non_actionable_auth_probe_exception(event):
        return False
    if is_non_actionable_image_resource_error(event):
        return False
    if is_non_actionable_first_party_stylesheet_error(event):
        return False
    if is_non_actionable_first_party_script_error(event):
        return False
    if is_non_actionable_third_party_resource_error(event):
        return False
    if has_browser_extension_url(event):
        return False
    if is_probable_extension_object_rejection(event):
        return False
    if is_non_actionable_wallet_provider_rejection(event):
        return False
    return True


def extract_signals(path: Path, text: str) -> list[str]:
    if not text:
        return []

    signals = []
    is_frontend_log = path.name == "frontend-errors.jsonl"
    is_synthetic_probe = path.name == "synthetic-service-probe"
    for line in text.splitlines():
        if is_frontend_log:
            if frontend_event_matches(line):
                signals.append(line)
        elif is_synthetic_probe:
            if SYNTHETIC_PROBE_RE.search(line) and not is_non_actionable_synthetic_probe_failure_line(line):
                signals.append(line)
        elif SERVER_500_RE.search(line) and not SERVER_NOISE_RE.search(line):
            signals.append(line)
    return signals


def signal_signature(source: str, line: str) -> str:
    """Stable identity: ids, IPs, emails, query strings, numbers and times stripped."""
    text = line
    if line.lstrip().startswith("{"):
        try:
            record = json.loads(line)
            event = (record.get("payload") or {}).get("event") or {}
            text = json.dumps(
                {k: event.get(k) for k in ("type", "message", "reason", "filename", "url", "status")},
                sort_keys=True,
            )
        except (ValueError, AttributeError):
            pass
    normalized = VOLATILE_RE.sub("#", text).strip().lower()
    return hashlib.sha256(f"{Path(source).name}|{normalized}".encode()).hexdigest()[:16]


def gate_signals(
    state: dict[str, Any],
    signals_by_source: dict[str, list[str]],
    *,
    now: float | None = None,
) -> dict[str, list[str]]:
    """Release a signature only when it persists: seen >= TEXTGEN_MONITOR_SIGNAL_COUNT
    times within the window, or on TEXTGEN_MONITOR_SIGNAL_SCANS consecutive scans.
    A released signature is quiet for TEXTGEN_MONITOR_SIGNAL_COOLDOWN seconds."""
    now = time.time() if now is None else now
    count = int(os.getenv("TEXTGEN_MONITOR_SIGNAL_COUNT", DEFAULT_SIGNAL_COUNT))
    scans = int(os.getenv("TEXTGEN_MONITOR_SIGNAL_SCANS", DEFAULT_SIGNAL_SCANS))
    window = int(os.getenv("TEXTGEN_MONITOR_SIGNAL_WINDOW", DEFAULT_SIGNAL_WINDOW_SECONDS))
    cooldown = int(os.getenv("TEXTGEN_MONITOR_SIGNAL_COOLDOWN", DEFAULT_SIGNAL_COOLDOWN_SECONDS))
    previous = int(state.get("signal_scan", 0))
    current = previous + 1
    seen = state.get("signals", {})
    released: dict[str, list[str]] = {}
    held = 0
    for source, signals in signals_by_source.items():
        for line in signals:
            key = signal_signature(source, line)
            entry = seen.get(key) or {"times": [], "streak": 0, "last_scan": 0, "released": 0}
            entry["times"] = [t for t in entry["times"] if now - t < window] + [now]
            if entry["last_scan"] != current:
                entry["streak"] = entry["streak"] + 1 if entry["last_scan"] == previous else 1
                entry["last_scan"] = current
            seen[key] = entry
            if entry["released"] and now - entry["released"] < cooldown:
                held += 1
            elif len(entry["times"]) >= count or entry["streak"] >= scans:
                entry["released"] = now
                released.setdefault(source, []).append(line)
            else:
                held += 1
    keep = max(window, cooldown)
    state["signal_scan"] = current
    state["signals"] = {k: v for k, v in seen.items() if now - max(v["times"] + [v["released"]]) < keep}
    if held:
        log(f"Holding {held} non-persistent signal(s) until they repeat")
    return released


def service_uptime_seconds(unit: str, *, run=subprocess.run) -> float | None:
    try:
        out = run(
            ["systemctl", "show", unit, "--property=ActiveEnterTimestampMonotonic", "--value"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip()
        started = int(out) / 1e6
        if started <= 0:
            return None
        return time.clock_gettime(time.CLOCK_MONOTONIC) - started
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def in_restart_grace(state: dict[str, Any], *, uptime=service_uptime_seconds) -> bool:
    """True for one scan right after a managed unit (re)started; never twice in a
    row, so a crash loop still surfaces."""
    grace = int(os.getenv("TEXTGEN_MONITOR_RESTART_GRACE", DEFAULT_RESTART_GRACE_SECONDS))
    young = any((u := uptime(unit)) is not None and u < grace for unit in RESTART_GRACE_UNITS)
    used = bool(state.get("restart_grace_used"))
    state["restart_grace_used"] = young and not used
    return young and not used


def format_synthetic_probe_failure(result: service_probe.ProbeResult) -> str:
    if result.status is not None:
        return f"Status: {result.status} synthetic probe {result.name} failed: {result.detail}"
    return f"Synthetic probe failure {result.name}: {result.detail}"


def actionable_synthetic_probe_failures(
    results: list[service_probe.ProbeResult],
) -> list[service_probe.ProbeResult]:
    return [
        result
        for result in results
        if not result.ok
        and not is_non_actionable_image_generation_backpressure_result(result)
        and not is_non_actionable_synthetic_probe_failure_line(format_synthetic_probe_failure(result))
    ]


def collect_synthetic_probe_failures(
    *,
    recheck_delay: int,
    profile: str = "core",
    sleep=time.sleep,
) -> list[service_probe.ProbeResult]:
    failures = actionable_synthetic_probe_failures(service_probe.run_checks(profile))
    if not failures or recheck_delay <= 0:
        return failures

    log(
        f"Synthetic probe found {len(failures)} failure(s); "
        f"confirming after {recheck_delay}s"
    )
    sleep(recheck_delay)
    return actionable_synthetic_probe_failures(service_probe.run_checks(profile))


def infrequent_probe_due(
    state: dict[str, Any],
    interval_seconds: int,
    *,
    now: float | None = None,
) -> bool:
    if interval_seconds <= 0:
        return True
    current = time.time() if now is None else now
    last = float(state.get("last_infrequent_probe_ts", 0.0))
    return current - last >= interval_seconds


def is_native_llm_lane_outage(failures: list[service_probe.ProbeResult]) -> bool:
    failure_by_name = {result.name: result for result in failures}
    failure_names = set(failure_by_name)
    if failure_names == NATIVE_LLM_RESTART_FAILURE_NAMES and all(
        result.status == 503 for result in failures
    ):
        return True

    if not NATIVE_DATA_PLANE_REQUIRED_FAILURE_NAMES.issubset(failure_names):
        return False

    native = failure_by_name["omniserve-native:generate"]
    if native.status not in {None, 502, 503}:
        return False
    if native.status is None and "Connection refused" not in native.detail:
        return False

    return all(
        failure_by_name[name].status in {502, 503}
        for name in ("production:generate", "production:autocomplete")
    )


def remediate_native_llm_lane_outage(
    failures: list[service_probe.ProbeResult],
    state: dict[str, Any],
    *,
    run=subprocess.run,
    sleep=time.sleep,
    now=time.time,
) -> bool:
    if not is_native_llm_lane_outage(failures):
        return False

    restart_cooldown = int(
        os.getenv(
            "TEXTGEN_MONITOR_NATIVE_LLM_RESTART_COOLDOWN_SECONDS",
            DEFAULT_NATIVE_LLM_RESTART_COOLDOWN_SECONDS,
        )
    )
    current_time = now()
    last_restart = float(state.get("last_omniserve_native_restart_ts", 0.0))
    cooldown_remaining = restart_cooldown - (current_time - last_restart)
    if last_restart > 0 and cooldown_remaining > 0:
        log(
            "Native LLM lane outage matches restart policy, but restart cooldown "
            f"is active for {int(cooldown_remaining)}s"
        )
        return False

    log("Native LLM lane outage confirmed; restarting omniserve-native.service with systemd")
    restart = run(
        ["sudo", "-n", "systemctl", "restart", "omniserve-native.service"],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if restart.returncode != 0:
        detail = (restart.stderr or restart.stdout or "").strip()
        log(f"Managed restart blocked for omniserve-native.service: {detail[:500]}")
        return False

    state["last_omniserve_native_restart_ts"] = current_time
    sleep(15)
    status = run(
        ["systemctl", "status", "omniserve-native.service", "--no-pager", "--lines=20"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if status.returncode == 0:
        log("omniserve-native.service status check passed after restart")
    else:
        detail = (status.stderr or status.stdout or "").strip()
        log(f"omniserve-native.service status check failed after restart: {detail[:500]}")
    return True


def write_incident(signals_by_source: dict[str, list[str]]) -> Path:
    ensure_runtime_dir()
    incident_path = RUNTIME_DIR / f"500-incident-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.md"
    parts = [
        "# New text-generator.io 500/client-error signals",
        "",
        f"Captured at: {utc_now()}",
        "",
    ]
    total_chars = 0
    for source, signals in signals_by_source.items():
        if not signals:
            continue
        parts.append(f"## {source}")
        parts.append("")
        excerpt = "\n".join(signals)
        remaining = max(0, MAX_EXCERPT_CHARS - total_chars)
        if len(excerpt) > remaining:
            excerpt = excerpt[:remaining] + "\n...[truncated]"
        total_chars += len(excerpt)
        parts.append("```")
        parts.append(excerpt)
        parts.append("```")
        parts.append("")
        if total_chars >= MAX_EXCERPT_CHARS:
            break
    incident_path.write_text("\n".join(parts), encoding="utf-8")
    return incident_path


def extract_incident_signals(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    signals: list[str] = []
    matched_section = False
    for match in INCIDENT_SECTION_RE.finditer(text):
        matched_section = True
        source = Path(match.group("source").strip())
        signals.extend(extract_signals(source, match.group("text")))

    if matched_section:
        return signals

    # Keep unrecognized incident formats pending unless they are plainly empty.
    return [text] if text.strip() else []


def prune_pending_incidents(pending: list[str]) -> tuple[list[str], list[str]]:
    retained: list[str] = []
    pruned: list[str] = []
    for incident in pending:
        path = Path(incident)
        try:
            signals = extract_incident_signals(path)
        except OSError:
            retained.append(incident)
            continue

        if signals:
            retained.append(incident)
        else:
            pruned.append(incident)

    return retained, pruned


def build_codex_prompt(incident_paths: list[str]) -> str:
    incident_sections = []
    for path_text in incident_paths[-5:]:
        path = Path(path_text)
        try:
            incident_sections.append(path.read_text(encoding="utf-8")[-MAX_EXCERPT_CHARS:])
        except OSError as exc:
            incident_sections.append(f"Could not read incident {path}: {exc}")

    incidents = "\n\n---\n\n".join(incident_sections)
    return f"""A text-generator.io monitor found new server 500s or frontend client errors.

Incident evidence:
{incidents}

You are working in /nvme0n1-disk/code/text-generator.io.

Requirements:
1. Read AGENTS.md and monitoring/AGENTS.md and follow both. In particular, read mainserver.log and never start a duplicate server or pkill anything.
2. Investigate server evidence from mainserver.log, /var/log/supervisor/text-generator-site*.log, /var/log/supervisor/text-generator-inference*.log, and client evidence from monitoring/runtime/frontend-errors.jsonl.
3. If a frontend stack is minified, use the logged sourceMapUrl hints or local static assets to map it back to readable code.
4. Run `python monitoring/service_probe.py --profile all`. Reproduce the failing contract locally with curl or tests where possible; do not accept shallow liveness as proof of recovery.
5. Make a focused code fix. Do not revert unrelated work in the dirty tree.
6. Run relevant tests. At minimum use the narrow test for the touched area; broaden if the blast radius is larger.
7. Redeploy when the fix changes running code or templates. Use only managed services, never a manual server process:
   - Site/frontend/main.py/static templates: `sudo -n systemctl restart text-generator-site.service`
   - Inference/API model server: `sudo -n systemctl restart text-generator-inference.service`
   - Native C gateway: `sudo -n systemctl restart omniserve-native.service`
   - Python OmniServe image/control plane: `sudo -n systemctl restart omniserve.service`
   - Public API tunnel routing: install `monitoring/supervisor/cloudflared.conf`, then use `sudo -n supervisorctl reread` and `sudo -n supervisorctl update cloudflared-inference`
   - 500 monitor code: `sudo -n systemctl restart text-generator-500-monitor.service`
   If `sudo -n` fails, report that redeploy is blocked instead of trying an interactive command.
8. After any restart, wait for startup and check managed status with `systemctl status ... --no-pager --lines=20`.
9. After redeploying, rerun the probe and verify the exact failing path on https://text-generator.io, https://api.text-generator.io, or https://ra.netwrck.com. A paid RA1 generation requires `RA1_MONITOR_API_KEY`; never use a key copied from examples.
10. If no code fix is needed, explain the evidence and leave the runtime state alone.

Finish with a concise summary of root cause, changes, tests, and production verification.
"""


def spawn_codex(incident_paths: list[str], timeout_seconds: int) -> None:
    prompt = build_codex_prompt(incident_paths)
    ensure_runtime_dir()
    with CODEX_LOG_FILE.open("a", encoding="utf-8") as codex_log:
        codex_log.write(f"\n{'=' * 80}\n{utc_now()} 500 monitor Codex invocation\n{'=' * 80}\n")
        codex_log.flush()
        subprocess.run(
            [*CODEX_CMD, prompt],
            cwd=str(REPO_ROOT),
            stdout=codex_log,
            stderr=subprocess.STDOUT,
            timeout=timeout_seconds,
            text=True,
        )


def run_once(args: argparse.Namespace, state: dict[str, Any]) -> None:
    signals_by_source: dict[str, list[str]] = {}
    for source in args.log_source:
        path = Path(source)
        text = read_new_text(path, state, scan_existing=args.scan_existing)
        signals = extract_signals(path, text)
        if signals:
            signals_by_source[str(path)] = signals

    if args.synthetic_probe:
        failures = collect_synthetic_probe_failures(recheck_delay=args.synthetic_recheck_delay)
        if infrequent_probe_due(state, args.infrequent_probe_interval):
            state["last_infrequent_probe_ts"] = time.time()
            failures.extend(
                collect_synthetic_probe_failures(
                    recheck_delay=args.synthetic_recheck_delay,
                    profile="parity",
                )
            )
        if failures and in_restart_grace(state):
            log(f"Managed service restarted <{DEFAULT_RESTART_GRACE_SECONDS}s ago; deferring {len(failures)} probe failure(s) one scan")
            failures = []
        if failures:
            remediated = (
                args.auto_fix
                and not args.dry_run
                and remediate_native_llm_lane_outage(failures, state)
            )
            if not remediated:
                signals_by_source["synthetic-service-probe"] = [
                    format_synthetic_probe_failure(result)
                    for result in failures
                ]

    signals_by_source = gate_signals(state, signals_by_source)
    pending = state.setdefault("pending_incidents", [])
    if signals_by_source:
        incident_path = write_incident(signals_by_source)
        pending.append(str(incident_path))
        state["pending_incidents"] = pending[-10:]
        count = sum(len(signals) for signals in signals_by_source.values())
        log(f"Captured {count} new 500/client-error signals in {incident_path}")
    else:
        log("No new 500/client-error signals")

    if not args.auto_fix:
        return

    pending = state.get("pending_incidents", [])
    if not pending:
        return

    pending, pruned = prune_pending_incidents(pending)
    if pruned:
        state["pending_incidents"] = pending
        log(f"Pruned {len(pruned)} stale pending incident(s) that no longer match current filters")
    if not pending:
        return

    now = time.time()
    last_run = float(state.get("last_codex_run_ts", 0.0))
    cooldown_remaining = args.codex_cooldown - (now - last_run)
    if cooldown_remaining > 0 and not args.force_codex:
        log(f"Codex cooldown active; pending incidents retained for {int(cooldown_remaining)}s")
        return

    if args.dry_run:
        log(f"Dry run: would invoke Codex for {len(pending)} pending incident(s)")
        return

    log(f"Invoking Codex for {len(pending)} pending incident(s)")
    try:
        spawn_codex(pending, timeout_seconds=args.codex_timeout)
        state["last_codex_run_ts"] = time.time()
        state["pending_incidents"] = []
        log("Codex invocation completed")
    except subprocess.TimeoutExpired:
        state["last_codex_run_ts"] = time.time()
        log(f"Codex invocation timed out after {args.codex_timeout}s; incidents remain pending")
    except FileNotFoundError:
        log(f"Codex command not found: {CODEX_LOCAL}; incidents remain pending")
    except Exception as exc:
        state["last_codex_run_ts"] = time.time()
        log(f"Codex invocation failed: {exc}; incidents remain pending")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Monitor server/client 500s and invoke Codex on cooldown")
    parser.add_argument("--daemon", action="store_true", help="Run continuously")
    parser.add_argument("--once", action="store_true", help="Run one check and exit")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL_SECONDS, help="Seconds between checks")
    parser.add_argument("--auto-fix", action="store_true", help="Invoke Codex when new/pending incidents exist")
    parser.add_argument("--dry-run", action="store_true", help="Do not invoke Codex")
    parser.add_argument("--force-codex", action="store_true", help="Ignore the 12 hour Codex cooldown")
    parser.add_argument("--scan-existing", action="store_true", help="Scan existing log contents instead of starting at EOF")
    parser.add_argument("--synthetic-probe", action="store_true", help="Probe managed services and generation contracts")
    parser.add_argument(
        "--synthetic-recheck-delay",
        type=int,
        default=int(os.getenv("TEXTGEN_MONITOR_SYNTHETIC_RECHECK_DELAY", DEFAULT_SYNTHETIC_RECHECK_DELAY_SECONDS)),
        help="Seconds to wait before confirming synthetic probe failures",
    )
    parser.add_argument(
        "--infrequent-probe-interval",
        type=int,
        default=int(
            os.getenv(
                "TEXTGEN_MONITOR_INFREQUENT_PROBE_INTERVAL",
                DEFAULT_INFREQUENT_PROBE_INTERVAL_SECONDS,
            )
        ),
        help="Seconds between full inference-parity contract probes",
    )
    parser.add_argument("--codex-cooldown", type=int, default=DEFAULT_CODEX_COOLDOWN_SECONDS)
    parser.add_argument("--codex-timeout", type=int, default=1800)
    parser.add_argument("--state-file", type=Path, default=STATE_FILE)
    parser.add_argument("--log-source", action="append", default=[str(path) for path in DEFAULT_LOG_SOURCES])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    lock_fh = acquire_lock()
    if lock_fh is None:
        return 0

    ensure_runtime_dir()
    log(
        f"Starting 500 monitor interval={args.interval}s auto_fix={args.auto_fix} "
        f"cooldown={args.codex_cooldown}s"
    )
    while True:
        state = load_state(args.state_file)
        run_once(args, state)
        if not args.dry_run:
            save_state(args.state_file, state)
        if args.once or not args.daemon:
            break
        time.sleep(args.interval)
    return 0


if __name__ == "__main__":
    sys.exit(main())

import json

from monitoring import monitor_500s
from monitoring.service_probe import ProbeResult


def test_codex_prompt_includes_native_tunnel_deployment():
    prompt = monitor_500s.build_codex_prompt([])

    assert "omniserve-native.service" in prompt
    assert "supervisorctl update cloudflared-inference" in prompt


def test_read_new_text_initializes_at_eof(tmp_path):
    log_file = tmp_path / "mainserver.log"
    log_file.write_text('Completed request: GET /broken - Status: 500\n', encoding="utf-8")
    state = {"files": {}}

    assert monitor_500s.read_new_text(log_file, state, scan_existing=False) == ""

    with log_file.open("a", encoding="utf-8") as fh:
        fh.write('127.0.0.1 - "GET /new-broken HTTP/1.1" 500\n')

    text = monitor_500s.read_new_text(log_file, state, scan_existing=False)
    assert "new-broken" in text
    assert monitor_500s.extract_signals(log_file, text) == ['127.0.0.1 - "GET /new-broken HTTP/1.1" 500']


def test_synthetic_probe_transport_failure_is_not_reported_as_http_500():
    result = ProbeResult(
        name="production:feature-extraction",
        ok=False,
        elapsed_ms=12,
        detail="URLError: <urlopen error [Errno -3] Temporary failure in name resolution>",
        status=None,
    )

    signal = monitor_500s.format_synthetic_probe_failure(result)

    assert signal.startswith("Synthetic probe failure production:feature-extraction:")
    assert "Status: 500" not in signal


def test_synthetic_probe_http_failure_preserves_actual_status():
    result = ProbeResult(
        name="production:feature-extraction",
        ok=False,
        elapsed_ms=12,
        detail="HTTP 502",
        status=502,
    )

    signal = monitor_500s.format_synthetic_probe_failure(result)

    assert signal == "Status: 502 synthetic probe production:feature-extraction failed: HTTP 502"


def test_synthetic_probe_recheck_suppresses_recovered_startup_race(monkeypatch):
    first_pass = [
        ProbeResult(
            name="omniserve-native:generate",
            ok=False,
            elapsed_ms=11,
            detail="URLError: <urlopen error [Errno 111] Connection refused>",
            status=None,
        )
    ]
    second_pass = [
        ProbeResult(
            name="omniserve-native:generate",
            ok=True,
            elapsed_ms=7,
            detail="contract ok",
            status=200,
        )
    ]
    calls = iter([first_pass, second_pass])
    sleeps = []
    monkeypatch.setattr(monitor_500s.service_probe, "run_checks", lambda profile: next(calls))
    monkeypatch.setattr(monitor_500s, "log", lambda message: None)

    failures = monitor_500s.collect_synthetic_probe_failures(
        recheck_delay=30,
        sleep=lambda seconds: sleeps.append(seconds),
    )

    assert failures == []
    assert sleeps == [30]


def test_synthetic_probe_recheck_keeps_persistent_contract_failure(monkeypatch):
    failure = ProbeResult(
        name="production:feature-extraction",
        ok=False,
        elapsed_ms=14,
        detail="HTTP 200 or invalid vector",
        status=200,
    )
    calls = iter([[failure], [failure]])
    monkeypatch.setattr(monitor_500s.service_probe, "run_checks", lambda profile: next(calls))
    monkeypatch.setattr(monitor_500s, "log", lambda message: None)

    failures = monitor_500s.collect_synthetic_probe_failures(
        recheck_delay=30,
        sleep=lambda seconds: None,
    )

    assert failures == [failure]


def test_image_generation_503_backpressure_is_not_actionable():
    failures = [
        ProbeResult(
            "omniserve-native:lora-image-generation",
            False,
            240000,
            "HTTP 503 or invalid image contract",
            503,
        ),
        ProbeResult(
            "omniserve-native:image-generation",
            False,
            240000,
            "HTTP 503 or invalid image contract",
            503,
        ),
    ]

    assert monitor_500s.actionable_synthetic_probe_failures(failures) == []


def test_image_generation_invalid_contract_stays_actionable():
    failure = ProbeResult(
        "omniserve-native:image-generation",
        False,
        500,
        "HTTP 200 or invalid image contract",
        200,
    )

    assert monitor_500s.actionable_synthetic_probe_failures([failure]) == [failure]


def test_synthetic_probe_can_recheck_infrequent_profile(monkeypatch):
    failure = ProbeResult("production:image-caption", False, 10, "HTTP 502", 502)
    profiles = []

    def run_checks(profile):
        profiles.append(profile)
        return [failure]

    monkeypatch.setattr(monitor_500s.service_probe, "run_checks", run_checks)
    monkeypatch.setattr(monitor_500s, "log", lambda message: None)

    failures = monitor_500s.collect_synthetic_probe_failures(
        recheck_delay=1,
        profile="parity",
        sleep=lambda _seconds: None,
    )

    assert failures == [failure]
    assert profiles == ["parity", "parity"]


def test_infrequent_probe_runs_every_ten_hours():
    state = {"last_infrequent_probe_ts": 100.0}

    assert monitor_500s.infrequent_probe_due(state, 10 * 60 * 60, now=36099.0) is False
    assert monitor_500s.infrequent_probe_due(state, 10 * 60 * 60, now=36100.0) is True


def test_native_llm_lane_outage_matches_exact_generate_503_pattern():
    failures = [
        ProbeResult("omniserve-native:generate", False, 10, "HTTP 503", 503),
        ProbeResult("compat:generate", False, 10, "HTTP 503", 503),
        ProbeResult("production:generate", False, 10, "HTTP 503", 503),
        ProbeResult("production:autocomplete", False, 10, "HTTP 503", 503),
    ]

    assert monitor_500s.is_native_llm_lane_outage(failures) is True


def test_native_llm_lane_outage_matches_unbound_native_data_plane_pattern():
    failures = [
        ProbeResult(
            "systemd:omniserve-native.service",
            False,
            5196,
            "systemctl=timeout after 5s port=8791 owner_pids=none service_cgroup_pids=none",
            None,
        ),
        ProbeResult(
            "omniserve-native:generate",
            False,
            9,
            "URLError: <urlopen error [Errno 111] Connection refused>",
            None,
        ),
        ProbeResult("compat:generate", False, 45045, "TimeoutError: timed out", None),
        ProbeResult("production:generate", False, 58, "HTTP 502", 502),
        ProbeResult("production:autocomplete", False, 38, "HTTP 502", 502),
        ProbeResult(
            "omniserve-native:openai-embeddings",
            False,
            0,
            "URLError: <urlopen error [Errno 111] Connection refused>",
            None,
        ),
        ProbeResult("production:native-status", False, 116, "HTTP 502 or missing llm", 502),
    ]

    assert monitor_500s.is_native_llm_lane_outage(failures) is True


def test_native_llm_lane_outage_rejects_embedding_only_failures():
    failures = [
        ProbeResult(
            "omniserve-native:openai-embeddings",
            False,
            10,
            "URLError: <urlopen error [Errno 111] Connection refused>",
            None,
        ),
        ProbeResult("production:openai-embeddings", False, 10, "HTTP 502", 502),
    ]

    assert monitor_500s.is_native_llm_lane_outage(failures) is False


def test_native_llm_lane_outage_remediation_uses_managed_systemd_restart(monkeypatch):
    failures = [
        ProbeResult("omniserve-native:generate", False, 10, "HTTP 503", 503),
        ProbeResult("compat:generate", False, 10, "HTTP 503", 503),
        ProbeResult("production:generate", False, 10, "HTTP 503", 503),
        ProbeResult("production:autocomplete", False, 10, "HTTP 503", 503),
    ]
    calls = []
    sleeps = []

    class Completed:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(command, **kwargs):
        calls.append(command)
        return Completed()

    monkeypatch.setattr(monitor_500s, "log", lambda message: None)

    state = {}
    remediated = monitor_500s.remediate_native_llm_lane_outage(
        failures,
        state,
        run=fake_run,
        sleep=lambda seconds: sleeps.append(seconds),
        now=lambda: 1000.0,
    )

    assert remediated is True
    assert calls[0] == ["sudo", "-n", "systemctl", "restart", "omniserve-native.service"]
    assert calls[1] == ["systemctl", "status", "omniserve-native.service", "--no-pager", "--lines=20"]
    assert sleeps == [15]
    assert state["last_omniserve_native_restart_ts"] == 1000.0


def test_native_llm_lane_outage_remediation_honors_restart_cooldown(monkeypatch):
    failures = [
        ProbeResult("omniserve-native:generate", False, 10, "HTTP 503", 503),
        ProbeResult("compat:generate", False, 10, "HTTP 503", 503),
        ProbeResult("production:generate", False, 10, "HTTP 503", 503),
        ProbeResult("production:autocomplete", False, 10, "HTTP 503", 503),
    ]
    calls = []
    monkeypatch.setattr(monitor_500s, "log", lambda message: None)

    remediated = monitor_500s.remediate_native_llm_lane_outage(
        failures,
        {"last_omniserve_native_restart_ts": 995.0},
        run=lambda command, **kwargs: calls.append(command),
        sleep=lambda seconds: None,
        now=lambda: 1000.0,
    )

    assert remediated is False
    assert calls == []


def test_synthetic_probe_transient_dns_incident_is_pruned(tmp_path):
    incident_path = tmp_path / "500-incident.md"
    incident_path.write_text(
        "\n".join(
            [
                "# New text-generator.io 500/client-error signals",
                "",
                "## synthetic-service-probe",
                "",
                "```",
                (
                    "Synthetic probe failure production:feature-extraction: "
                    "URLError: <urlopen error [Errno -3] Temporary failure in name resolution>"
                ),
                "```",
            ]
        ),
        encoding="utf-8",
    )

    retained, pruned = monitor_500s.prune_pending_incidents([str(incident_path)])

    assert retained == []
    assert pruned == [str(incident_path)]


def test_synthetic_probe_contract_incidents_remain_actionable_without_fake_500(tmp_path):
    incident_path = tmp_path / "500-incident.md"
    incident_path.write_text(
        "\n".join(
            [
                "# New text-generator.io 500/client-error signals",
                "",
                "## synthetic-service-probe",
                "",
                "```",
                "Synthetic probe failure production:feature-extraction: HTTP 200 or invalid vector",
                "```",
            ]
        ),
        encoding="utf-8",
    )

    retained, pruned = monitor_500s.prune_pending_incidents([str(incident_path)])

    assert retained == [str(incident_path)]
    assert pruned == []


def test_image_generation_503_backpressure_incident_is_pruned(tmp_path):
    incident_path = tmp_path / "500-incident.md"
    incident_path.write_text(
        "\n".join(
            [
                "# New text-generator.io 500/client-error signals",
                "",
                "## synthetic-service-probe",
                "",
                "```",
                (
                    "Status: 503 synthetic probe omniserve-native:lora-image-generation "
                    "failed: HTTP 503 or invalid image contract"
                ),
                (
                    "Status: 503 synthetic probe omniserve-native:image-generation "
                    "failed: HTTP 503 or invalid image contract"
                ),
                "```",
            ]
        ),
        encoding="utf-8",
    )

    retained, pruned = monitor_500s.prune_pending_incidents([str(incident_path)])

    assert retained == []
    assert pruned == [str(incident_path)]


def test_frontend_error_jsonl_signals_are_detected(tmp_path):
    frontend_log = tmp_path / "frontend-errors.jsonl"
    frontend_log.write_text(
        "\n".join(
            [
                json.dumps({"payload": {"event": {"type": "fetch_5xx", "status": 500}}}),
                json.dumps({"payload": {"event": {"type": "debug"}}}),
            ]
        ),
        encoding="utf-8",
    )

    signals = monitor_500s.extract_signals(frontend_log, frontend_log.read_text(encoding="utf-8"))

    assert len(signals) == 1
    assert "fetch_5xx" in signals[0]


def test_redacted_cross_origin_script_errors_are_ignored(tmp_path):
    frontend_log = tmp_path / "frontend-errors.jsonl"
    frontend_log.write_text(
        json.dumps(
            {
                "user_agent": (
                    "Mozilla/5.0 (Linux; Android 12; JLN-AL00 Build/HUAWEIJLN-AL00; wv) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/97.0.4692.98 "
                    "Mobile Safari/537.36 T7/15.68 BDOS/1.0 baiduboxapp/15.69.0.10"
                ),
                "payload": {
                    "event": {
                        "type": "window_error",
                        "message": "Script error.",
                        "filename": "",
                        "lineno": None,
                        "colno": None,
                        "error": {},
                    },
                    "page": {"url": "https://text-generator.io/"},
                    "sourceMaps": [
                        {
                            "scriptUrl": "https://text-generator.io/static/libs/jquery-3.2.1.min.js",
                            "sourceMapUrl": "https://text-generator.io/static/libs/jquery-3.2.1.min.js.map",
                        }
                    ],
                },
            }
        ),
        encoding="utf-8",
    )

    signals = monitor_500s.extract_signals(frontend_log, frontend_log.read_text(encoding="utf-8"))

    assert signals == []


def test_window_errors_with_first_party_location_are_still_detected(tmp_path):
    frontend_log = tmp_path / "frontend-errors.jsonl"
    frontend_log.write_text(
        json.dumps(
            {
                "user_agent": "Mozilla/5.0 Chrome/149.0.0.0 Safari/537.36",
                "payload": {
                    "event": {
                        "type": "window_error",
                        "message": "Cannot read properties of undefined",
                        "filename": "https://text-generator.io/static/js/playground.js",
                        "lineno": 744,
                        "colno": 9,
                        "error": {"stack": "TypeError: Cannot read properties of undefined"},
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    signals = monitor_500s.extract_signals(frontend_log, frontend_log.read_text(encoding="utf-8"))

    assert len(signals) == 1
    assert "playground.js" in signals[0]


def test_crawler_resource_errors_are_ignored(tmp_path):
    frontend_log = tmp_path / "frontend-errors.jsonl"
    frontend_log.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "user_agent": "Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)",
                        "payload": {
                            "event": {
                                "type": "resource_error",
                                "tagName": "SCRIPT",
                                "sourceUrl": "https://static.cloudflareinsights.com/beacon.min.js/v123",
                            }
                        },
                    }
                ),
                json.dumps(
                    {
                        "user_agent": (
                            "Mozilla/5.0 AppleWebKit/537.36 "
                            "(KHTML, like Gecko; compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"
                        ),
                        "payload": {
                            "event": {
                                "type": "resource_error",
                                "tagName": "SCRIPT",
                                "sourceUrl": "https://js.stripe.com/v3/",
                            }
                        },
                    }
                ),
                json.dumps(
                    {
                        "user_agent": "Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)",
                        "payload": {
                            "event": {
                                "type": "resource_error",
                                "tagName": "SCRIPT",
                                "sourceUrl": "https://text-generatorstatic.text-generator.io/static/js/subscription-modal.js",
                            }
                        },
                    }
                ),
                json.dumps(
                    {
                        "user_agent": "Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)",
                        "payload": {
                            "event": {
                                "type": "resource_error",
                                "tagName": "IMG",
                                "sourceUrl": (
                                    "https://text-generatorstatic.text-generator.io/"
                                    "static/img/android-chrome-192x192.png"
                                ),
                            }
                        },
                    }
                ),
                json.dumps(
                    {
                        "user_agent": (
                            "Mozilla/5.0 AppleWebKit/537.36 "
                            "(KHTML, like Gecko; compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"
                        ),
                        "payload": {
                            "event": {
                                "type": "window_error",
                                "message": "Script error.",
                                "filename": "",
                                "lineno": None,
                                "colno": None,
                            }
                        },
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    signals = monitor_500s.extract_signals(frontend_log, frontend_log.read_text(encoding="utf-8"))

    assert signals == []


def test_crawler_first_party_fetch_5xx_errors_are_still_detected(tmp_path):
    frontend_log = tmp_path / "frontend-errors.jsonl"
    frontend_log.write_text(
        json.dumps(
            {
                "user_agent": "Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)",
                "payload": {
                    "event": {
                        "type": "fetch_5xx",
                        "url": "https://api.text-generator.io/api/v1/generate",
                        "status": 500,
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    signals = monitor_500s.extract_signals(frontend_log, frontend_log.read_text(encoding="utf-8"))

    assert len(signals) == 1
    assert "fetch_5xx" in signals[0]


def test_auth_probe_fetch_exceptions_are_ignored(tmp_path):
    frontend_log = tmp_path / "frontend-errors.jsonl"
    frontend_log.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "user_agent": "Mozilla/5.0 Chrome/143.0.0.0 Safari/537.36",
                        "payload": {
                            "event": {
                                "type": "fetch_exception",
                                "url": "/api/current-user",
                                "error": {"name": "TypeError", "message": "Failed to fetch"},
                            }
                        },
                    }
                ),
                json.dumps(
                    {
                        "user_agent": "Mozilla/5.0 Chrome/143.0.0.0 Safari/537.36",
                        "payload": {
                            "event": {
                                "type": "fetch_exception",
                                "url": "/api/get-user/stripe-usage",
                                "error": {"name": "TypeError", "message": "Failed to fetch"},
                            }
                        },
                    }
                ),
                json.dumps(
                    {
                        "user_agent": (
                            "Mozilla/5.0 (compatible; YandexRenderResourcesBot/1.0; "
                            "+http://yandex.com/bots)"
                        ),
                        "payload": {
                            "event": {
                                "type": "fetch_exception",
                                "url": "https://text-generator.io/api/current-user",
                                "error": {"name": "TypeError", "message": "Failed to fetch"},
                            }
                        },
                    }
                ),
                json.dumps(
                    {
                        "user_agent": (
                            "Mozilla/5.0 (compatible; YandexRenderResourcesBot/1.0; "
                            "+http://yandex.com/bots)"
                        ),
                        "payload": {
                            "event": {
                                "type": "fetch_exception",
                                "url": "https://text-generator.io/api/get-user/stripe-usage",
                                "error": {"name": "TypeError", "message": "Failed to fetch"},
                            }
                        },
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    signals = monitor_500s.extract_signals(frontend_log, frontend_log.read_text(encoding="utf-8"))

    assert signals == []


def test_crawler_other_fetch_exceptions_are_still_detected(tmp_path):
    frontend_log = tmp_path / "frontend-errors.jsonl"
    frontend_log.write_text(
        json.dumps(
            {
                "user_agent": "Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)",
                "payload": {
                    "event": {
                        "type": "fetch_exception",
                        "url": "https://api.text-generator.io/api/v1/generate",
                        "error": {"name": "TypeError", "message": "Failed to fetch"},
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    signals = monitor_500s.extract_signals(frontend_log, frontend_log.read_text(encoding="utf-8"))

    assert len(signals) == 1
    assert "api/v1/generate" in signals[0]


def test_browser_extension_unhandled_rejections_are_ignored(tmp_path):
    frontend_log = tmp_path / "frontend-errors.jsonl"
    frontend_log.write_text(
        json.dumps(
            {
                "user_agent": "Mozilla/5.0 Chrome/148.0.0.0 Safari/537.36",
                "payload": {
                    "event": {
                        "type": "unhandledrejection",
                        "reason": {
                            "name": "Error",
                            "message": "Failed to connect to MetaMask",
                            "stack": (
                                "Error: Failed to connect to MetaMask\n"
                                "    at Object.connect "
                                "(chrome-extension://abc123/scripts/inpage.js:1:63510)"
                            ),
                        },
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    signals = monitor_500s.extract_signals(frontend_log, frontend_log.read_text(encoding="utf-8"))

    assert signals == []


def test_extension_object_not_found_rejections_are_ignored(tmp_path):
    frontend_log = tmp_path / "frontend-errors.jsonl"
    frontend_log.write_text(
        json.dumps(
            {
                "user_agent": "Mozilla/5.0 Chrome/142.0.7444.163 Safari/537.36",
                "payload": {
                    "event": {
                        "type": "unhandledrejection",
                        "reason": {
                            "name": "Error",
                            "message": "Object Not Found Matching Id:13, MethodName:update, ParamCount:4",
                            "stack": "",
                        },
                        "message": "Object Not Found Matching Id:13, MethodName:update, ParamCount:4",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    signals = monitor_500s.extract_signals(frontend_log, frontend_log.read_text(encoding="utf-8"))

    assert signals == []


def test_wallet_provider_disconnect_rejections_are_ignored(tmp_path):
    frontend_log = tmp_path / "frontend-errors.jsonl"
    frontend_log.write_text(
        json.dumps(
            {
                "user_agent": "Mozilla/5.0 Chrome/146.0.0.0 Safari/537.36",
                "payload": {
                    "event": {
                        "type": "unhandledrejection",
                        "reason": {
                            "name": "Error",
                            "message": "The provider is disconnected from all chains.",
                            "stack": "",
                        },
                        "message": "The provider is disconnected from all chains.",
                    },
                    "page": {"url": "https://text-generator.io/"},
                    "sourceMaps": [
                        {
                            "scriptUrl": "https://text-generator.io/static/libs/jquery-3.2.1.min.js",
                            "sourceMapUrl": "https://text-generator.io/static/libs/jquery-3.2.1.min.js.map",
                        },
                        {
                            "scriptUrl": "https://text-generator.io/static/js/material.min.js",
                            "sourceMapUrl": "https://text-generator.io/static/js/material.min.js.map",
                        },
                    ],
                },
            }
        ),
        encoding="utf-8",
    )

    signals = monitor_500s.extract_signals(frontend_log, frontend_log.read_text(encoding="utf-8"))

    assert signals == []


def test_browser_extension_resource_errors_are_ignored(tmp_path):
    frontend_log = tmp_path / "frontend-errors.jsonl"
    frontend_log.write_text(
        json.dumps(
            {
                "user_agent": "Mozilla/5.0 Chrome/148.0.0.0 Safari/537.36",
                "payload": {
                    "event": {
                        "type": "resource_error",
                        "tagName": "SCRIPT",
                        "sourceUrl": "moz-extension://abc123/content.js",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    signals = monitor_500s.extract_signals(frontend_log, frontend_log.read_text(encoding="utf-8"))

    assert signals == []


def test_known_logo_image_resource_errors_are_ignored_for_non_crawlers(tmp_path):
    frontend_log = tmp_path / "frontend-errors.jsonl"
    frontend_log.write_text(
        "\n".join(
            json.dumps(
                {
                    "user_agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) "
                        "Gecko/20100101 Firefox/135.0"
                    ),
                    "payload": {
                        "event": {
                            "type": "resource_error",
                            "tagName": "IMG",
                            "sourceUrl": f"https://text-generator.io{path}",
                        }
                    },
                }
            )
            for path in [
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
            ]
        ),
        encoding="utf-8",
    )

    signals = monitor_500s.extract_signals(frontend_log, frontend_log.read_text(encoding="utf-8"))

    assert signals == []


def test_stale_pending_logo_incident_is_pruned(tmp_path):
    incident_path = tmp_path / "500-incident.md"
    incident_path.write_text(
        "\n".join(
            [
                "# New text-generator.io 500/client-error signals",
                "",
                "## /nvme0n1-disk/code/text-generator.io/monitoring/runtime/frontend-errors.jsonl",
                "",
                "```",
                json.dumps(
                    {
                        "user_agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) "
                            "Gecko/20100101 Firefox/135.0"
                        ),
                        "payload": {
                            "event": {
                                "type": "resource_error",
                                "tagName": "IMG",
                                "sourceUrl": "https://text-generator.io/static/img/android-chrome-192x192.png",
                            }
                        },
                    }
                ),
                "```",
            ]
        ),
        encoding="utf-8",
    )

    retained, pruned = monitor_500s.prune_pending_incidents([str(incident_path)])

    assert retained == []
    assert pruned == [str(incident_path)]


def test_actionable_pending_incident_is_retained(tmp_path):
    incident_path = tmp_path / "500-incident.md"
    incident_path.write_text(
        "\n".join(
            [
                "# New text-generator.io 500/client-error signals",
                "",
                "## /nvme0n1-disk/code/text-generator.io/monitoring/runtime/frontend-errors.jsonl",
                "",
                "```",
                json.dumps(
                    {
                        "user_agent": "Mozilla/5.0 Chrome/136.0.0.0 Safari/537.36",
                        "payload": {
                            "event": {
                                "type": "resource_error",
                                "tagName": "IMG",
                                "sourceUrl": "https://text-generator.io/static/img/missing-product-shot.png",
                            }
                        },
                    }
                ),
                "```",
            ]
        ),
        encoding="utf-8",
    )

    retained, pruned = monitor_500s.prune_pending_incidents([str(incident_path)])

    assert retained == [str(incident_path)]
    assert pruned == []


def test_other_first_party_image_resource_errors_are_still_detected(tmp_path):
    frontend_log = tmp_path / "frontend-errors.jsonl"
    frontend_log.write_text(
        json.dumps(
            {
                "user_agent": "Mozilla/5.0 Chrome/136.0.0.0 Safari/537.36",
                "payload": {
                    "event": {
                        "type": "resource_error",
                        "tagName": "IMG",
                        "sourceUrl": "https://text-generator.io/static/img/missing-product-shot.png",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    signals = monitor_500s.extract_signals(frontend_log, frontend_log.read_text(encoding="utf-8"))

    assert len(signals) == 1
    assert "missing-product-shot.png" in signals[0]


def test_known_optional_third_party_resource_errors_are_ignored_for_non_crawlers(tmp_path):
    frontend_log = tmp_path / "frontend-errors.jsonl"
    frontend_log.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "user_agent": "Mozilla/5.0 Chrome/142.0.7444.162 Safari/537.36",
                        "payload": {
                            "event": {
                                "type": "resource_error",
                                "tagName": "LINK",
                                "sourceUrl": "https://js.stripe.com/v3/",
                            }
                        },
                    }
                ),
                json.dumps(
                    {
                        "user_agent": "Mozilla/5.0 Chrome/142.0.7444.162 Safari/537.36",
                        "payload": {
                            "event": {
                                "type": "resource_error",
                                "tagName": "SCRIPT",
                                "sourceUrl": "https://js.stripe.com/v3/",
                            }
                        },
                    }
                ),
                json.dumps(
                    {
                        "user_agent": "Mozilla/5.0 Chrome/142.0.7444.162 Safari/537.36",
                        "payload": {
                            "event": {
                                "type": "resource_error",
                                "tagName": "IMG",
                                "sourceUrl": "https://indiehunt.io/badges/indiehunt-badge-light.svg",
                            }
                        },
                    }
                ),
                json.dumps(
                    {
                        "user_agent": "Mozilla/5.0 Chrome/132.0.0.0 Safari/537.36",
                        "payload": {
                            "event": {
                                "type": "resource_error",
                                "tagName": "LINK",
                                "sourceUrl": (
                                    "https://translate.googleapis.com/"
                                    "translate_static/css/translateelement.css"
                                ),
                            }
                        },
                    }
                ),
                json.dumps(
                    {
                        "user_agent": "Mozilla/5.0 Chrome/149.0.0.0 Safari/537.36",
                        "payload": {
                            "event": {
                                "type": "resource_error",
                                "tagName": "LINK",
                                "sourceUrl": "https://v5games.com/",
                            }
                        },
                    }
                ),
                json.dumps(
                    {
                        "user_agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/619.0.7131.87 Safari/537.36"
                        ),
                        "payload": {
                            "event": {
                                "type": "resource_error",
                                "tagName": "SCRIPT",
                                "sourceUrl": (
                                    "https://zmstat.com/?v=2&extId="
                                    "9bd08b7b880e4bdd8b3505b110783624-chrome-23"
                                ),
                            }
                        },
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    signals = monitor_500s.extract_signals(frontend_log, frontend_log.read_text(encoding="utf-8"))

    assert signals == []


def test_known_first_party_stylesheet_resource_errors_are_ignored(tmp_path):
    frontend_log = tmp_path / "frontend-errors.jsonl"
    frontend_log.write_text(
        "\n".join(
            json.dumps(
                {
                    "user_agent": "Mozilla/5.0 Chrome/148.0.7778.96 Safari/537.36",
                    "payload": {
                        "event": {
                            "type": "resource_error",
                            "tagName": "LINK",
                            "sourceUrl": f"https://text-generator.io{path}",
                        }
                    },
                }
            )
            for path in [
                "/static/css/subscription-modal.css",
                "/static/libs/codemirror.css",
                "/static/libs/select2/dist/css/select2.min.css",
                "/static/libs/styles/atom-one-dark.css",
                "/static/libs/styles/default.css",
            ]
        ),
        encoding="utf-8",
    )

    signals = monitor_500s.extract_signals(frontend_log, frontend_log.read_text(encoding="utf-8"))

    assert signals == []


def test_known_first_party_script_resource_errors_are_ignored(tmp_path):
    frontend_log = tmp_path / "frontend-errors.jsonl"
    frontend_log.write_text(
        json.dumps(
            {
                "received_at": "2026-09-23T10:34:09Z",
                "user_agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) HeadlessChrome/149.0.7827.55 Safari/537.36"
                ),
                "payload": {
                    "event": {
                        "type": "resource_error",
                        "tagName": "SCRIPT",
                        "sourceUrl": "https://text-generator.io/static/js/material.min.js?v=2",
                        "outerHTML": (
                            '<script defer="" src="/static/js/material.min.js?v=2" '
                            'type="text/javascript"></script>'
                        ),
                    },
                    "page": {"url": "https://text-generator.io/"},
                    "sourceMaps": [],
                },
            }
        ),
        encoding="utf-8",
    )

    signals = monitor_500s.extract_signals(frontend_log, frontend_log.read_text(encoding="utf-8"))

    assert signals == []


def test_known_highlightjs_cdn_resource_errors_are_ignored(tmp_path):
    frontend_log = tmp_path / "frontend-errors.jsonl"
    frontend_log.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "user_agent": "Mozilla/5.0 Chrome/148.0.7778.96 Safari/537.36",
                        "payload": {
                            "event": {
                                "type": "resource_error",
                                "tagName": "LINK",
                                "sourceUrl": (
                                    "https://cdnjs.cloudflare.com/ajax/libs/"
                                    "highlight.js/11.9.0/styles/github.min.css"
                                ),
                            }
                        },
                    }
                ),
                json.dumps(
                    {
                        "user_agent": "Mozilla/5.0 Chrome/148.0.7778.96 Safari/537.36",
                        "payload": {
                            "event": {
                                "type": "resource_error",
                                "tagName": "SCRIPT",
                                "sourceUrl": (
                                    "https://cdnjs.cloudflare.com/ajax/libs/"
                                    "highlight.js/11.9.0/highlight.min.js"
                                ),
                            }
                        },
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    signals = monitor_500s.extract_signals(frontend_log, frontend_log.read_text(encoding="utf-8"))

    assert signals == []


def test_unknown_external_resource_errors_are_still_detected(tmp_path):
    frontend_log = tmp_path / "frontend-errors.jsonl"
    frontend_log.write_text(
        json.dumps(
            {
                "user_agent": "Mozilla/5.0 Chrome/136.0.0.0 Safari/537.36",
                "payload": {
                    "event": {
                        "type": "resource_error",
                        "tagName": "SCRIPT",
                        "sourceUrl": "https://cdn.example.com/widget.js",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    signals = monitor_500s.extract_signals(frontend_log, frontend_log.read_text(encoding="utf-8"))

    assert len(signals) == 1
    assert "cdn.example.com" in signals[0]

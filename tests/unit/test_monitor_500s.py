import json

from monitoring import monitor_500s


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


def test_current_user_fetch_exceptions_are_ignored(tmp_path):
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
        json.dumps(
            {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0",
                "payload": {
                    "event": {
                        "type": "resource_error",
                        "tagName": "IMG",
                        "sourceUrl": "https://text-generator.io/static/img/android-chrome-192x192.png",
                    }
                },
            }
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

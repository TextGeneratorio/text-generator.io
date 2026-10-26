import base64
import io
import json
import urllib.error

from monitoring import service_probe


class FakeResponse:
    def __init__(self, status, body):
        self.status = status
        self._body = json.dumps(body).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self._body


class FakeBinaryResponse(FakeResponse):
    def __init__(self, status, body, content_type):
        self.status = status
        self._body = body
        self.headers = {"content-type": content_type}


def test_completion_probe_accepts_legacy_autocomplete_contract():
    def opener(request, timeout):
        payload = json.loads(request.data)
        assert payload == service_probe.AUTOCOMPLETE_PAYLOAD
        assert timeout == 2.0
        return FakeResponse(
            200,
            [{"generated_text": payload["text"] + " works", "stop_reason": "max_length"}],
        )

    result = service_probe.probe_completion(
        "test", "http://example.test/api/v1/generate", timeout=2.0, opener=opener
    )

    assert result.ok is True
    assert result.status == 200
    assert result.detail == "contract ok"


def test_completion_probe_rejects_http_500_without_leaking_body():
    def opener(request, timeout):
        raise urllib.error.HTTPError(
            request.full_url,
            500,
            "Internal Server Error",
            {},
            io.BytesIO(b'{"error":"sensitive upstream detail"}'),
        )

    result = service_probe.probe_completion(
        "test", "http://example.test/api/v1/generate", opener=opener
    )

    assert result.ok is False
    assert result.status == 500
    assert result.detail == "HTTP 500"


def test_completion_probe_rejects_single_token_without_word_boundary():
    result = service_probe.probe_completion(
        "test",
        "http://example.test/api/v1/generate",
        opener=lambda request, timeout: FakeResponse(
            200,
            [{"generated_text": service_probe.TEXT + "I", "stop_reason": "min_probability"}],
        ),
    )

    assert result.ok is False
    assert result.detail == "continuation must begin at a word boundary and contain text"


def test_feature_extraction_probe_validates_vector_dimensions():
    def opener(request, timeout):
        payload = json.loads(request.data)
        assert payload == {"text": service_probe.EMBEDDING_TEXT, "num_features": 3}
        return FakeResponse(200, [0.1, -0.2, 0.3])

    result = service_probe.probe_feature_extraction(
        "embedding", "http://example.test/api/v1/feature-extraction", dimensions=3, opener=opener
    )

    assert result.ok is True
    assert result.detail == "3-dimension contract ok"


def test_feature_extraction_probe_rejects_wrong_vector_size():
    result = service_probe.probe_feature_extraction(
        "embedding",
        "http://example.test/api/v1/feature-extraction",
        dimensions=3,
        opener=lambda request, timeout: FakeResponse(200, [0.1, -0.2]),
    )

    assert result.ok is False
    assert result.detail == "HTTP 200 or invalid vector"


def test_openai_embedding_probe_validates_response_envelope():
    def opener(request, timeout):
        payload = json.loads(request.data)
        assert payload["input"] == service_probe.EMBEDDING_TEXT
        assert payload["dimensions"] == 3
        return FakeResponse(
            200,
            {
                "object": "list",
                "data": [{"object": "embedding", "index": 0, "embedding": [0.1, -0.2, 0.3]}],
                "model": "omniserve-modernbert",
                "usage": {"prompt_tokens": 2, "total_tokens": 2},
            },
        )

    result = service_probe.probe_openai_embeddings(
        "embedding", "http://example.test/v1/embeddings", dimensions=3, opener=opener
    )

    assert result.ok is True
    assert result.detail == "OpenAI 3-dimension contract ok"


def test_openai_embedding_probe_rejects_non_finite_values():
    result = service_probe.probe_openai_embeddings(
        "embedding",
        "http://example.test/v1/embeddings",
        dimensions=2,
        opener=lambda request, timeout: FakeResponse(
            200,
            {
                "object": "list",
                "data": [{"object": "embedding", "index": 0, "embedding": [0.1, float("nan")]}],
            },
        ),
    )

    assert result.ok is False


def test_openai_embedding_batch_probe_validates_each_index_and_vector():
    def opener(request, timeout):
        payload = json.loads(request.data)
        assert payload["input"] == service_probe.OPENAI_EMBEDDING_BATCH
        assert payload["dimensions"] == 2
        return FakeResponse(
            200,
            {
                "object": "list",
                "data": [
                    {"object": "embedding", "index": 0, "embedding": [0.1, -0.2]},
                    {"object": "embedding", "index": 1, "embedding": [0.3, -0.4]},
                ],
            },
        )

    result = service_probe.probe_openai_embedding_batch(
        "batch", "http://example.test/v1/embeddings", dimensions=2, opener=opener
    )

    assert result.ok is True
    assert result.detail == "OpenAI batch 2x2 contract ok"


def test_openai_embedding_batch_probe_rejects_missing_result():
    result = service_probe.probe_openai_embedding_batch(
        "batch",
        "http://example.test/v1/embeddings",
        dimensions=2,
        opener=lambda request, timeout: FakeResponse(
            200,
            {
                "object": "list",
                "data": [{"object": "embedding", "index": 0, "embedding": [0.1, 0.2]}],
            },
        ),
    )

    assert result.ok is False


def test_image_caption_probe_sends_multipart_and_validates_contract(monkeypatch, tmp_path):
    image_path = tmp_path / "monitor.png"
    image_path.write_bytes(b"png-bytes")
    monkeypatch.setattr(service_probe, "MONITOR_IMAGE_PATH", image_path)

    def opener(request, timeout):
        assert timeout == 2.0
        assert request.get_header("Secret") == "monitor-secret"
        assert b'name="fast_mode"' in request.data
        assert b"png-bytes" in request.data
        return FakeResponse(
            200,
            {
                "caption": "the monitor image",
                "model": "microsoft/git-base",
                "fast_mode": True,
            },
        )

    result = service_probe.probe_image_caption(
        "caption",
        "http://example.test/api/v1/image-caption",
        secret="monitor-secret",
        timeout=2.0,
        opener=opener,
    )

    assert result.ok is True
    assert result.detail == "Git-base caption contract ok"


def test_omniserve_caption_probe_rejects_empty_caption(monkeypatch, tmp_path):
    image_path = tmp_path / "monitor.png"
    image_path.write_bytes(b"png-bytes")
    monkeypatch.setattr(service_probe, "MONITOR_IMAGE_PATH", image_path)

    result = service_probe.probe_omniserve_caption(
        opener=lambda request, timeout: FakeResponse(
            200,
            {"model": "git-base-caption", "data": [{"index": 0, "text": ""}]},
        )
    )

    assert result.ok is False
    assert result.detail == "HTTP 200 or invalid caption contract"


def test_classification_probe_validates_result(monkeypatch, tmp_path):
    image_path = tmp_path / "monitor.png"
    image_path.write_bytes(b"png-bytes")
    monkeypatch.setattr(service_probe, "MONITOR_IMAGE_PATH", image_path)

    def opener(request, timeout):
        payload = json.loads(request.data)
        assert payload["model"] == "clip-vit-large"
        assert base64.b64decode(payload["image"]) == b"png-bytes"
        return FakeResponse(200, {
            "model": "clip-vit-large",
            "labels": payload["labels"],
            "data": [{"index": 0, "label": payload["labels"][0],
                      "scores": [{"label": payload["labels"][0], "score": 0.9}]}],
        })

    result = service_probe.probe_classification(
        "classification", "http://example.test/v1/images/classifications",
        image=True, opener=opener,
    )

    assert result.ok is True
    assert result.detail == "CLIP classification contract ok"


def test_lora_catalog_probe_requires_live_adapter_list():
    result = service_probe.probe_lora_catalog(
        opener=lambda request, timeout: FakeResponse(
            200,
            {"count": 2, "loras": [{"id": "zimage_360"}, {"id": "pixel_art"}]},
        )
    )

    assert result.ok is True
    assert result.detail == "Z-Image LoRA catalog ok (2 adapters)"


def test_lora_catalog_probe_rejects_empty_generic_catalog():
    result = service_probe.probe_lora_catalog(
        opener=lambda request, timeout: FakeResponse(200, {})
    )

    assert result.ok is False
    assert result.detail == "HTTP 200 or invalid/empty LoRA catalog"


def test_gemma_multimodal_probe_uses_standard_openai_image_and_audio(monkeypatch, tmp_path):
    image_path = tmp_path / "monitor.png"
    image_path.write_bytes(b"png-bytes")
    monkeypatch.setattr(service_probe, "MONITOR_IMAGE_PATH", image_path)

    def opener(request, timeout):
        payload = json.loads(request.data)
        content = payload["messages"][0]["content"]
        assert timeout == 2.0
        assert request.get_header("Secret") == "monitor-secret"
        assert payload["temperature"] == 0
        assert content[0]["type"] == "image_url"
        assert base64.b64decode(content[0]["image_url"]["url"].split(",", 1)[1]) == b"png-bytes"
        assert content[1]["type"] == "input_audio"
        audio_bytes = base64.b64decode(content[1]["input_audio"]["data"])
        assert audio_bytes.startswith(b"RIFF")
        assert audio_bytes[8:12] == b"WAVE"
        assert content[2] == {
            "type": "input_text",
            "text": "Briefly confirm both inputs were received.",
        }
        return FakeResponse(
            200,
            {"choices": [{"message": {"role": "assistant", "content": "Inputs received."}}]},
        )

    result = service_probe.probe_gemma_multimodal_chat(
        secret="monitor-secret", timeout=2.0, opener=opener
    )

    assert result.ok is True
    assert result.detail == "Gemma image+audio OpenAI contract ok"


def test_gemma_multimodal_probe_rejects_empty_completion():
    result = service_probe.probe_gemma_multimodal_chat(
        opener=lambda request, timeout: FakeResponse(
            200,
            {"choices": [{"message": {"role": "assistant", "content": ""}}]},
        )
    )

    assert result.ok is False
    assert result.detail == "HTTP 200 or invalid chat contract"


def test_image_generation_probe_validates_png():
    encoded = base64.b64encode(b"\x89PNG" + b"x" * 100).decode()
    result = service_probe.probe_image_generation(
        opener=lambda request, timeout: FakeResponse(
            200, {"data": [{"b64_json": encoded}]}
        )
    )

    assert result.ok is True
    assert result.detail == "Z-Image generation contract ok"


def test_image_generation_probe_accepts_webp():
    encoded = base64.b64encode(b"RIFF" + b"x" * 4 + b"WEBP" + b"x" * 100).decode()
    result = service_probe.probe_image_generation(
        opener=lambda request, timeout: FakeResponse(
            200, {"data": [{"b64_json": encoded}]}
        )
    )

    assert result.ok is True


def test_image_generation_probe_can_exercise_lora():
    encoded = base64.b64encode(b"\x89PNG" + b"x" * 100).decode()

    def opener(request, timeout):
        payload = json.loads(request.data)
        assert payload["lora_id"] == "zimage_360"
        assert payload["lora_scale"] == 1.0
        assert payload["auto_lora"] is False
        return FakeResponse(200, {"data": [{"b64_json": encoded}]})

    result = service_probe.probe_image_generation(
        name="lora", lora_id="zimage_360", opener=opener
    )

    assert result.ok is True
    assert result.detail == "Z-Image LoRA generation contract ok (zimage_360)"


def test_background_removal_probe_validates_webp(monkeypatch, tmp_path):
    image_path = tmp_path / "monitor.png"
    image_path.write_bytes(b"png-bytes")
    monkeypatch.setattr(service_probe, "MONITOR_IMAGE_PATH", image_path)

    def opener(request, timeout):
        payload = json.loads(request.data)
        assert base64.b64decode(payload["image_url"].split(",", 1)[1]) == b"png-bytes"
        return FakeBinaryResponse(
            200, b"RIFF" + b"x" * 4 + b"WEBP" + b"x" * 100, "image/webp"
        )

    result = service_probe.probe_background_removal(opener=opener)

    assert result.ok is True
    assert result.detail == "BiRefNet WebP contract ok"


def test_systemd_probe_rejects_listener_owned_by_another_process(monkeypatch):
    responses = iter(
        [
            type("Process", (), {"returncode": 0, "stdout": "ActiveState=active\nSubState=running\nMainPID=123\n"})(),
            type(
                "Process",
                (),
                {
                    "returncode": 0,
                    "stdout": 'LISTEN 0 2048 0.0.0.0:9080 0.0.0.0:* users:(("gunicorn",pid=456,fd=4))\n',
                },
            )(),
        ]
    )
    monkeypatch.setattr(service_probe.subprocess, "run", lambda *args, **kwargs: next(responses))

    result = service_probe.probe_systemd_service("inference.service", expected_port=9080)

    assert result.ok is False
    assert "main_pid=123" in result.detail
    assert "owner_pids=456" in result.detail


def test_systemd_probe_accepts_worker_socket_in_service_cgroup(monkeypatch):
    responses = iter(
        [
            type("Process", (), {"returncode": 0, "stdout": "ActiveState=active\nSubState=running\nMainPID=123\n"})(),
            type(
                "Process",
                (),
                {
                    "returncode": 0,
                    "stdout": 'LISTEN 0 2048 127.0.0.1:9083 0.0.0.0:* users:(("gunicorn",pid=456,fd=4))\n',
                },
            )(),
        ]
    )
    monkeypatch.setattr(service_probe.subprocess, "run", lambda *args, **kwargs: next(responses))
    monkeypatch.setattr(
        service_probe,
        "_pid_cgroup",
        lambda pid: "0::/system.slice/text-generator-inference.service\n",
    )

    result = service_probe.probe_systemd_service(
        "text-generator-inference.service", expected_port=9083
    )

    assert result.ok is True
    assert "main_pid=123" in result.detail
    assert "owner_pids=456" in result.detail
    assert "service_cgroup_pids=456" in result.detail


def test_systemd_probe_falls_back_to_service_cgroup_when_systemctl_times_out(monkeypatch):
    def fake_run(args, **kwargs):
        if args[0] == "systemctl":
            raise service_probe.subprocess.TimeoutExpired(args, kwargs["timeout"])
        return type(
            "Process",
            (),
            {
                "returncode": 0,
                "stdout": 'LISTEN 0 1024 127.0.0.1:8791 0.0.0.0:* users:(("omniserve-nativ",pid=789,fd=41))\n',
            },
        )()

    monkeypatch.setattr(service_probe.subprocess, "run", fake_run)
    monkeypatch.setattr(
        service_probe,
        "_pid_cgroup",
        lambda pid: "0::/system.slice/omniserve-native.service\n",
    )

    result = service_probe.probe_systemd_service(
        "omniserve-native.service", expected_port=8791
    )

    assert result.ok is True
    assert "systemctl=timeout after 5s" in result.detail
    assert "owner_pids=789" in result.detail
    assert "service_cgroup_pids=789" in result.detail


def test_all_profile_includes_parity_classification_and_ra_checks(monkeypatch):
    def result(name, *args, **kwargs):
        return service_probe.ProbeResult(name, True, 0, "ok", 200)

    monkeypatch.setattr(
        service_probe,
        "probe_systemd_service",
        lambda unit, **kwargs: result(f"systemd:{unit}"),
    )
    monkeypatch.setattr(service_probe, "probe_completion", result)
    monkeypatch.setattr(service_probe, "probe_feature_extraction", result)
    monkeypatch.setattr(service_probe, "probe_openai_embeddings", result)
    monkeypatch.setattr(service_probe, "probe_openai_embedding_batch", result)
    monkeypatch.setattr(service_probe, "probe_json_get", result)
    monkeypatch.setattr(
        service_probe,
        "probe_lora_catalog",
        lambda *args, **kwargs: result("omniserve-native:loras"),
    )
    monkeypatch.setattr(
        service_probe,
        "probe_gemma_multimodal_chat",
        lambda *args, **kwargs: result("omniserve-native:gemma-multimodal-chat"),
    )
    monkeypatch.setattr(
        service_probe,
        "probe_omniserve_caption",
        lambda *args, name="omniserve:caption", **kwargs: result(args[0] if args else name),
    )
    monkeypatch.setattr(service_probe, "probe_image_caption", result)
    monkeypatch.setattr(service_probe, "probe_classification", result)
    monkeypatch.setattr(
        service_probe,
        "probe_image_generation",
        lambda *args, name="omniserve-native:image-generation", **kwargs: result(name),
    )
    monkeypatch.setattr(
        service_probe,
        "probe_background_removal",
        lambda *args, **kwargs: result("omniserve-native:background-removal"),
    )

    names = [item.name for item in service_probe.run_checks("all")]

    assert "omniserve-native:image-classification" in names
    assert "omniserve-native:text-classification" in names
    assert "ra1:pricing" in names
    assert "ra1:search" in names


def test_core_profile_uses_native_admission_tolerant_timeouts(monkeypatch):
    calls = []

    def result(name, *args, **kwargs):
        calls.append((name, kwargs.get("timeout")))
        return service_probe.ProbeResult(name, True, 0, "ok", 200)

    monkeypatch.setattr(
        service_probe,
        "probe_systemd_service",
        lambda unit, **kwargs: service_probe.ProbeResult(f"systemd:{unit}", True, 0, "ok"),
    )
    monkeypatch.setattr(service_probe, "probe_completion", result)
    monkeypatch.setattr(service_probe, "probe_feature_extraction", result)
    monkeypatch.setattr(service_probe, "probe_openai_embeddings", result)
    monkeypatch.setattr(service_probe, "probe_openai_embedding_batch", result)
    monkeypatch.setattr(
        service_probe,
        "probe_json_get",
        lambda name, *args, **kwargs: service_probe.ProbeResult(name, True, 0, "ok", 200),
    )

    service_probe.run_checks("core")

    checked = {name: timeout for name, timeout in calls}
    assert checked["production:autocomplete"] == service_probe.CORE_TEXT_TIMEOUT
    assert checked["compat:feature-extraction"] == service_probe.CORE_TEXT_TIMEOUT
    assert checked["compat:openai-embeddings"] == service_probe.CORE_TEXT_TIMEOUT

from pathlib import Path


def test_latest_vllm_cli_and_text_only_mode_are_the_defaults():
    script = Path("questions/inference_server/vllm_accel/serve_generic.sh").read_text()

    assert '.venv-vllm-025' in script
    assert '"$VENV/bin/vllm" serve "$MODEL"' in script
    assert 'TEXT_ONLY:-1' in script
    assert '--language-model-only' in script
    assert '--skip-mm-profiling' in script


def test_latest_launcher_exposes_5090_tuning_controls():
    script = Path("questions/inference_server/vllm_accel/serve_generic.sh").read_text()

    assert 'KV_CACHE_DTYPE' in script
    assert 'MAX_NUM_BATCHED_TOKENS' in script
    assert 'ASYNC_SCHEDULING' in script
    assert 'VLLM_LEGACY_ENTRYPOINT' in script

import json

import numpy as np
import pytest

from questions.inference_server import inference_server


class FakeUpload:
    filename = "turn.webm"

    async def read(self):
        return b"\x00" * 4096


async def _passthrough_gpu_bound(func, *args, **kwargs):
    return func(*args, **kwargs)


@pytest.mark.asyncio
async def test_voice_chat_orchestrates_transcribe_chat_tts(monkeypatch):
    captured = {}

    monkeypatch.setattr(inference_server, "_run_gpu_bound", _passthrough_gpu_bound)
    monkeypatch.setattr(
        inference_server,
        "_run_media_prompt_with_multimodal_model",
        lambda **kw: "hello there",
    )

    async def fake_reply(messages, max_tokens, temperature, secret):
        captured["messages"] = messages
        return "hi, how can I help?"

    monkeypatch.setattr(inference_server, "_generate_voice_chat_reply", fake_reply)
    monkeypatch.setattr(
        inference_server,
        "audio_process",
        lambda text, voice, speed, language, steps: (24000, np.zeros(8, dtype=np.int16)),
    )
    monkeypatch.setattr(inference_server, "write_wav", lambda np_audio, rate: b"RIFFwav")
    monkeypatch.setattr(inference_server, "_user_has_subscription_or_credits", lambda *a, **k: True)
    monkeypatch.setattr(inference_server, "_consume_user_credits", lambda *a, **k: None)

    resp = await inference_server.voice_chat(
        background_tasks=None,
        request=None,
        response=None,
        audio_file=FakeUpload(),
        history=json.dumps([{"role": "user", "content": "prev"}, {"role": "assistant", "content": "ok"}]),
        system_prompt="",
        voice="F1",
        language="en",
        speed=1.0,
        steps=4,
        max_length=400,
        temperature=0.7,
        secret="s",
    )

    body = json.loads(resp.body)
    assert body["user_text"] == "hello there"
    assert body["reply_text"] == "hi, how can I help?"
    assert body["audio_sample_rate"] == 24000
    assert body["audio_format"] == "wav"
    assert body["audio_base64"]

    roles = [m["role"] for m in captured["messages"]]
    assert roles == ["system", "user", "assistant", "user"]
    assert captured["messages"][-1]["content"] == "hello there"


@pytest.mark.asyncio
async def test_voice_chat_tolerates_bad_history_json(monkeypatch):
    captured = {}

    monkeypatch.setattr(inference_server, "_run_gpu_bound", _passthrough_gpu_bound)
    monkeypatch.setattr(
        inference_server, "_run_media_prompt_with_multimodal_model", lambda **kw: "  spoken  "
    )

    async def fake_reply(messages, max_tokens, temperature, secret):
        captured["messages"] = messages
        return ""

    monkeypatch.setattr(inference_server, "_generate_voice_chat_reply", fake_reply)
    monkeypatch.setattr(
        inference_server,
        "audio_process",
        lambda *a, **k: (24000, np.zeros(2, dtype=np.int16)),
    )
    monkeypatch.setattr(inference_server, "write_wav", lambda *a, **k: b"x")
    monkeypatch.setattr(inference_server, "_user_has_subscription_or_credits", lambda *a, **k: True)
    monkeypatch.setattr(inference_server, "_consume_user_credits", lambda *a, **k: None)

    resp = await inference_server.voice_chat(
        background_tasks=None,
        request=None,
        response=None,
        audio_file=FakeUpload(),
        history="not-json",
        system_prompt="",
        voice="F1",
        language="en",
        speed=1.0,
        steps=4,
        max_length=400,
        temperature=0.7,
        secret="s",
    )

    body = json.loads(resp.body)
    # falls back to default reply when model returns empty
    assert body["reply_text"] == "Sorry, I didn't catch that."
    # bad history ignored -> only system + current user turn
    assert [m["role"] for m in captured["messages"]] == ["system", "user"]
    assert body["user_text"] == "spoken"

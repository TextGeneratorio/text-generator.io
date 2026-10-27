import io

import numpy as np
import pytest
import soundfile as sf

from questions.inference_server.tts_utils import optimize_tts_audio_for_speed


def _kokoro():
    pytest.importorskip("phonemizer")
    pytest.importorskip("torch")
    from questions.inference_server import kokoro

    return kokoro


def test_split_segments_first_sentence_then_groups():
    k = _kokoro()
    text = "Hi. I was thinking about the trip we planned. " + " ".join(["This is another sentence here."] * 30)
    segs = k.split_segments(text)
    assert segs[0] == "Hi. I was thinking about the trip we planned."
    assert all(len(s) <= k.SEG_MAX_CHARS for s in segs[1:])
    assert " ".join(segs) == text.strip()


def test_split_segments_long_first_sentence_cuts_at_clause():
    k = _kokoro()
    text = "Sometimes I wonder what it would be like to live somewhere else, like a small island or a quiet mountain village far from everything. Ok."
    segs = k.split_segments(text)
    assert segs[0] == "Sometimes I wonder what it would be like to live somewhere else,"
    assert " ".join(segs) == text


def test_split_segments_newlines_and_empty():
    k = _kokoro()
    assert k.split_segments("") == []
    assert k.split_segments("line one is here\nline two is here too") == ["line one is here line two is here too"]


def test_streamed_trim_matches_whole_trim():
    rng = np.random.default_rng(0)
    parts = [np.concatenate([np.zeros(4000), rng.uniform(-0.5, 0.5, 9000), np.zeros(5000)]).astype(np.float32) for _ in range(3)]
    whole = optimize_tts_audio_for_speed(np.concatenate(parts))
    chunks = [optimize_tts_audio_for_speed(p, lead=i == 0, trail=i == len(parts) - 1) for i, p in enumerate(parts)]
    np.testing.assert_array_equal(np.concatenate(chunks), whole)


@pytest.mark.parametrize("fmt", ["wav", "pcm"])
def test_pcm16_chunks_match_whole_encode(fmt):
    from questions.inference_server import inference_server as srv

    rng = np.random.default_rng(1)
    audio = rng.uniform(-1.2, 1.2, 24000).astype(np.float32)
    whole, _ = srv._encode_audio(audio, 24000, fmt)
    if fmt == "wav":
        whole = sf.read(io.BytesIO(whole), dtype="int16")[0].tobytes()
    streamed = b"".join(srv._pcm16_chunk(c, 24000, fmt) for c in np.array_split(audio, 7))
    assert streamed == whole


def test_wav_stream_header_parses():
    from questions.inference_server import inference_server as srv

    data = srv._wav_stream_header(24000) + srv._pcm16_chunk(np.zeros(240, np.float32), 24000, "wav")
    assert data[:4] == b"RIFF" and data[8:16] == b"WAVEfmt " and len(srv._wav_stream_header(24000)) == 44


def test_internal_credentials_skip_usage_tracking(monkeypatch):
    from questions.inference_server import inference_server as srv

    monkeypatch.setattr(srv, "NETWRCK_PARTNER_SECRET", "partner-key")
    called = []
    monkeypatch.setattr(srv, "get_db_session_sync", lambda: called.append(1))
    srv.track_stripe_request_usage("partner-key", 1)
    srv.track_stripe_request_usage(None, 1)
    assert not called

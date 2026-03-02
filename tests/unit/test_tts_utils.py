import pytest
import numpy as np

from questions.inference_server import tts_utils


def test_srt_format_timestamp_simple():
    assert tts_utils.srt_format_timestamp(1.234) == "0:00:01,234"


def test_write_srt_basic():
    transcript = [
        {"start": 0.0, "end": 1.0, "text": "hello"},
        {"start": 1.0, "end": 2.0, "text": "world"},
    ]
    result = tts_utils.write_srt(transcript)
    assert "1\n0:00:00,000 --> 0:00:01,000\nhello" in result
    assert "2\n0:00:01,000 --> 0:00:02,000\nworld" in result


def test_chunk_text_words():
    result = tts_utils.chunk_text_words("a b c d e", 2)
    assert result == ["a b", "c d", "e"]


def test_chunk_text_words_invalid():
    with pytest.raises(ValueError):
        tts_utils.chunk_text_words("text", 0)


def test_srt_format_timestamp_negative():
    with pytest.raises(ValueError):
        tts_utils.srt_format_timestamp(-1)


def test_trim_edge_silence_is_capped():
    audio = np.concatenate(
        [
            np.zeros(4000, dtype=np.int16),
            np.full(1000, 1200, dtype=np.int16),
            np.zeros(4000, dtype=np.int16),
        ]
    )
    trimmed = tts_utils.trim_edge_silence(audio, sample_rate=24000, threshold=64, max_trim_ms=100)
    # max trim is 2400 samples per side, so 4200 should remain.
    assert trimmed.shape[0] == 4200
    assert trimmed.dtype == np.int16


def test_trim_edge_silence_keeps_all_silence_audio():
    audio = np.zeros(2000, dtype=np.int16)
    trimmed = tts_utils.trim_edge_silence(audio)
    assert np.array_equal(trimmed, audio)


def test_compress_internal_silence_shortens_only_internal_runs():
    audio = np.concatenate(
        [
            np.full(100, 1000, dtype=np.int16),
            np.zeros(5000, dtype=np.int16),
            np.full(100, 1000, dtype=np.int16),
        ]
    )
    compressed = tts_utils.compress_internal_silence(
        audio,
        sample_rate=1000,
        threshold=64,
        min_silence_ms=100,
        keep_silence_ms=20,
    )
    assert compressed.shape[0] == 220  # 100 speech + 20 kept silence + 100 speech


def test_compress_internal_silence_preserves_edge_silence():
    audio = np.concatenate(
        [
            np.zeros(500, dtype=np.int16),
            np.full(50, 900, dtype=np.int16),
            np.zeros(500, dtype=np.int16),
        ]
    )
    compressed = tts_utils.compress_internal_silence(
        audio,
        sample_rate=1000,
        threshold=64,
        min_silence_ms=50,
        keep_silence_ms=10,
    )
    assert compressed.shape[0] == audio.shape[0]


def test_optimize_tts_audio_for_speed_applies_both_steps():
    audio = np.concatenate(
        [
            np.zeros(1000, dtype=np.int16),
            np.full(100, 1000, dtype=np.int16),
            np.zeros(1200, dtype=np.int16),
            np.full(100, 1000, dtype=np.int16),
            np.zeros(1000, dtype=np.int16),
        ]
    )
    optimized = tts_utils.optimize_tts_audio_for_speed(
        audio,
        sample_rate=1000,
        trim_edges=True,
        compress_internal=True,
        edge_trim_ms=200,
        internal_silence_min_ms=200,
        internal_silence_keep_ms=40,
        threshold=64,
    )
    assert optimized.shape[0] < audio.shape[0]
    assert optimized.dtype == np.int16


def test_trim_edge_silence_handles_float_waveform():
    audio = np.concatenate(
        [
            np.zeros(300, dtype=np.float32),
            np.full(100, 0.25, dtype=np.float32),
            np.zeros(300, dtype=np.float32),
        ]
    )
    trimmed = tts_utils.trim_edge_silence(audio, sample_rate=1000, threshold=64, max_trim_ms=120)
    assert trimmed.shape[0] == 460  # 120 trim on each side from 700 total samples
    assert trimmed.dtype == np.float32


def test_compress_internal_silence_handles_float_waveform():
    audio = np.concatenate(
        [
            np.full(80, 0.2, dtype=np.float32),
            np.zeros(300, dtype=np.float32),
            np.full(80, 0.2, dtype=np.float32),
        ]
    )
    compressed = tts_utils.compress_internal_silence(
        audio,
        sample_rate=1000,
        threshold=64,
        min_silence_ms=120,
        keep_silence_ms=40,
    )
    assert compressed.shape[0] == 200  # 80 speech + 40 kept silence + 80 speech

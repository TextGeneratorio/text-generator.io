import pytest

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

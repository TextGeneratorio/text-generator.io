import numpy as np

from questions.inference_server.tts_utils import synthesize_full_text


def test_synthesize_full_text_chunks():
    rate, audio = synthesize_full_text(
        "a b c d e f",
        chunk_words=2,
        process_fn=lambda chunk, voice="af", speed=1.0: (16000, np.array([1], dtype=np.int16)),
        sample_rate=16000,
    )
    assert rate == 16000
    assert len(audio) == 3

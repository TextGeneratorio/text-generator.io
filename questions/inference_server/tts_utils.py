import numpy as np
from typing import Callable, Iterator, Tuple, List, Optional


def srt_format_timestamp(seconds: float) -> str:
    """Format seconds to SRT timestamp."""
    if seconds < 0:
        raise ValueError("non-negative timestamp expected")
    milliseconds = round(seconds * 1000.0)

    hours = milliseconds // 3_600_000
    milliseconds -= hours * 3_600_000

    minutes = milliseconds // 60_000
    milliseconds -= minutes * 60_000

    sec = milliseconds // 1_000
    milliseconds -= sec * 1_000

    return f"{hours}:{minutes:02d}:{sec:02d},{milliseconds:03d}"


def write_srt(transcript: Iterator[dict]) -> str:
    """Return a simple SRT string from whisper-like transcript segments."""
    count = 0
    srt = []
    for segment in transcript:
        count += 1
        srt.append(
            f"{count}\n"
            f"{srt_format_timestamp(segment['start'])} --> {srt_format_timestamp(segment['end'])}\n"
            f"{segment['text'].replace('-->', '->').strip()}\n"
        )
    return "\n".join(srt)


def chunk_text_words(text: str, chunk_words: int) -> List[str]:
    """Split *text* into chunks of at most *chunk_words* words."""
    if chunk_words <= 0:
        raise ValueError("chunk_words must be positive")
    words = text.split()
    return [" ".join(words[i : i + chunk_words]) for i in range(0, len(words), chunk_words)]


def synthesize_full_text(
    text: str,
    voice: str = "af_nicole",
    speed: float = 1.0,
    chunk_words: int = 100,
    process_fn: Optional[Callable[[str, str, float], Tuple[int, np.ndarray]]] = None,
    sample_rate: int = 24000,
) -> Tuple[int, np.ndarray]:
    """Generate speech for arbitrarily long text by chunking."""
    if process_fn is None:
        from .inference_server import audio_process as process_fn  # local import to avoid cycles

    if not text.strip():
        return (sample_rate, np.zeros(0, dtype=np.int16))

    segments = []
    for chunk in chunk_text_words(text, chunk_words):
        _, audio = process_fn(chunk, voice=voice, speed=speed)
        segments.append(audio)

    full_audio = np.concatenate(segments) if segments else np.zeros(0, dtype=np.int16)
    return (sample_rate, full_audio)

from typing import Callable, Iterator, List, Optional, Tuple

import numpy as np


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


def _abs_audio_with_effective_threshold(audio: np.ndarray, threshold: int) -> Tuple[np.ndarray, float]:
    """Return absolute amplitudes and a threshold scaled to the input dtype."""
    if np.issubdtype(audio.dtype, np.floating):
        abs_audio = np.abs(audio.astype(np.float32))
        max_amp = float(np.nanmax(abs_audio)) if abs_audio.size else 0.0
        # Kokoro outputs normalized floats in [-1, 1]; scale int16-like thresholds.
        effective_threshold = float(threshold) / 32768.0 if max_amp <= 2.0 else float(threshold)
        return abs_audio, effective_threshold

    abs_audio = np.abs(audio.astype(np.int32))
    return abs_audio, float(threshold)


def trim_edge_silence(
    audio: np.ndarray,
    sample_rate: int = 24000,
    threshold: int = 64,
    max_trim_ms: int = 120,
) -> np.ndarray:
    """Trim leading/trailing near-silence, capped by *max_trim_ms* per side."""
    if audio.size == 0 or max_trim_ms <= 0:
        return audio

    abs_audio, effective_threshold = _abs_audio_with_effective_threshold(audio, threshold)
    voiced_indices = np.flatnonzero(abs_audio > effective_threshold)
    if voiced_indices.size == 0:
        return audio

    max_trim_samples = int(sample_rate * (max_trim_ms / 1000.0))
    if max_trim_samples <= 0:
        return audio

    leading_silence = int(voiced_indices[0])
    trailing_silence = int((audio.size - 1) - voiced_indices[-1])
    trim_start = min(leading_silence, max_trim_samples)
    trim_end = min(trailing_silence, max_trim_samples)

    end_index = audio.size - trim_end
    if end_index <= trim_start:
        return audio
    return audio[trim_start:end_index]


def compress_internal_silence(
    audio: np.ndarray,
    sample_rate: int = 24000,
    threshold: int = 64,
    min_silence_ms: int = 250,
    keep_silence_ms: int = 80,
) -> np.ndarray:
    """Shorten long internal silence runs while preserving short pauses."""
    if audio.size == 0:
        return audio
    if min_silence_ms <= 0 or keep_silence_ms < 0:
        return audio

    min_silence_samples = int(sample_rate * (min_silence_ms / 1000.0))
    keep_silence_samples = int(sample_rate * (keep_silence_ms / 1000.0))
    if min_silence_samples <= 0 or keep_silence_samples >= min_silence_samples:
        return audio

    abs_audio, effective_threshold = _abs_audio_with_effective_threshold(audio, threshold)
    is_silence = abs_audio <= effective_threshold

    chunks: List[np.ndarray] = []
    i = 0
    n = audio.size
    while i < n:
        j = i + 1
        run_is_silence = bool(is_silence[i])
        while j < n and bool(is_silence[j]) == run_is_silence:
            j += 1

        run = audio[i:j]
        is_internal_run = i > 0 and j < n
        if run_is_silence and is_internal_run and run.size >= min_silence_samples:
            if keep_silence_samples > 0:
                left = keep_silence_samples // 2
                right = keep_silence_samples - left
                if left > 0:
                    chunks.append(run[:left])
                if right > 0:
                    chunks.append(run[-right:])
            # keep_silence_samples == 0 means drop the run entirely
        else:
            chunks.append(run)

        i = j

    if not chunks:
        return np.zeros(0, dtype=audio.dtype)
    return np.concatenate(chunks)


def optimize_tts_audio_for_speed(
    audio: np.ndarray,
    sample_rate: int = 24000,
    trim_edges: bool = True,
    compress_internal: bool = False,
    edge_trim_ms: int = 120,
    internal_silence_min_ms: int = 250,
    internal_silence_keep_ms: int = 80,
    threshold: int = 64,
) -> np.ndarray:
    """Apply conservative, intelligibility-safe post-processing to reduce audio length."""
    optimized = audio
    if trim_edges:
        optimized = trim_edge_silence(
            optimized,
            sample_rate=sample_rate,
            threshold=threshold,
            max_trim_ms=edge_trim_ms,
        )
    if compress_internal:
        optimized = compress_internal_silence(
            optimized,
            sample_rate=sample_rate,
            threshold=threshold,
            min_silence_ms=internal_silence_min_ms,
            keep_silence_ms=internal_silence_keep_ms,
        )
    return optimized


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

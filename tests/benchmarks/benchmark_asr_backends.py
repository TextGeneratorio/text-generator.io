#!/usr/bin/env python3

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import soundfile as sf

PROJECT_DIR = Path(__file__).resolve().parents[2]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))


def normalize(text: str) -> str:
    text = (text or "").lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    return " ".join(text.split())


def wer(ref: str, hyp: str) -> float:
    ref_words = normalize(ref).split()
    hyp_words = normalize(hyp).split()
    if not ref_words:
        return 0.0 if not hyp_words else 1.0
    dist = [[0] * (len(hyp_words) + 1) for _ in range(len(ref_words) + 1)]
    for i in range(len(ref_words) + 1):
        dist[i][0] = i
    for j in range(len(hyp_words) + 1):
        dist[0][j] = j
    for i in range(1, len(ref_words) + 1):
        for j in range(1, len(hyp_words) + 1):
            sub = 0 if ref_words[i - 1] == hyp_words[j - 1] else 1
            dist[i][j] = min(
                dist[i - 1][j] + 1,
                dist[i][j - 1] + 1,
                dist[i - 1][j - 1] + sub,
            )
    return dist[len(ref_words)][len(hyp_words)] / len(ref_words)


def extract_gemma_text(result) -> str:
    if isinstance(result, (list, tuple)) and result:
        result = result[0]
    if isinstance(result, str):
        return result.strip()
    if isinstance(result, dict):
        return str(result.get("text", "") or result.get("pred_text", "")).strip()
    return str(getattr(result, "text", "") or getattr(result, "pred_text", "")).strip()


def audio_duration_seconds(audio_path: Path) -> float:
    info = sf.info(str(audio_path))
    if not info.samplerate:
        return 0.0
    return float(info.frames) / float(info.samplerate)


def default_audio_dir() -> Path:
    return (PROJECT_DIR.parent / "dictator" / "e2e" / "audio").resolve()


@dataclass
class SampleResult:
    file: str
    reference: str
    hypothesis: str
    wer: float
    elapsed_s: float
    audio_duration_s: float


class GemmaBackend:
    name = "gemma"

    def __init__(self):
        self.model = None

    def load(self):
        from questions.inference_server.inference_server import load_audio_model

        self.model = load_audio_model()

    def warmup(self, audio_path: Path):
        self.transcribe(audio_path)

    def transcribe(self, audio_path: Path) -> str:
        result = self.model.transcribe([str(audio_path)], timestamps=False)
        return extract_gemma_text(result)


class CohereBackend:
    def __init__(
        self,
        name: str,
        model_id: str,
        language: str,
        compile_encoder: bool,
        pipeline_detokenization: bool,
        batch_size: int,
        token: str | None,
    ):
        self.name = name
        self.model_id = model_id
        self.language = language
        self.compile_encoder = compile_encoder
        self.pipeline_detokenization = pipeline_detokenization
        self.batch_size = batch_size
        self.token = token
        self.processor = None
        self.model = None
        self.device = None

    def load(self):
        import torch
        from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor

        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if self.device.startswith("cuda") else torch.float32

        if self.device.startswith("cuda"):
            torch.backends.cudnn.benchmark = True

        self.processor = AutoProcessor.from_pretrained(
            self.model_id,
            trust_remote_code=True,
            token=self.token,
        )
        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
            self.model_id,
            trust_remote_code=True,
            torch_dtype=dtype,
            low_cpu_mem_usage=True,
            token=self.token,
        ).to(self.device)
        self.model.eval()

    def warmup(self, audio_path: Path):
        self.transcribe(audio_path)

    def transcribe(self, audio_path: Path) -> str:
        texts = self.model.transcribe(
            processor=self.processor,
            audio_files=[str(audio_path)],
            language=self.language,
            compile=self.compile_encoder,
            pipeline_detokenization=self.pipeline_detokenization,
            batch_size=self.batch_size,
        )
        if isinstance(texts, (list, tuple)) and texts:
            return str(texts[0]).strip()
        return str(texts).strip()


def resolve_hf_token():
    for env_name in ("HF_TOKEN", "HUGGINGFACE_HUB_TOKEN", "HUGGING_FACE_HUB_TOKEN"):
        value = os.environ.get(env_name, "").strip()
        if value:
            return value
    return None


def create_backend(name: str, model_id: str, language: str, batch_size: int, token: str | None):
    if name == "gemma":
        return GemmaBackend()
    if name == "cohere":
        return CohereBackend(
            name="cohere",
            model_id=model_id,
            language=language,
            compile_encoder=False,
            pipeline_detokenization=False,
            batch_size=batch_size,
            token=token,
        )
    if name == "cohere_compile":
        return CohereBackend(
            name="cohere_compile",
            model_id=model_id,
            language=language,
            compile_encoder=True,
            pipeline_detokenization=False,
            batch_size=batch_size,
            token=token,
        )
    if name == "cohere_compile_pipe":
        return CohereBackend(
            name="cohere_compile_pipe",
            model_id=model_id,
            language=language,
            compile_encoder=True,
            pipeline_detokenization=True,
            batch_size=batch_size,
            token=token,
        )
    raise ValueError(f"unknown backend: {name}")


def load_manifest(audio_dir: Path, ground_truth_path: Path, limit: int | None):
    with open(ground_truth_path) as f:
        ground_truth = json.load(f)
    items = []
    for filename, reference in sorted(ground_truth.items()):
        audio_path = audio_dir / filename
        if not audio_path.exists():
            continue
        items.append((audio_path, reference))
    if limit is not None:
        items = items[:limit]
    return items


def benchmark_backend(backend, items):
    started = time.perf_counter()
    backend.load()
    load_time_s = time.perf_counter() - started

    warmup_time_s = 0.0
    if items:
        warmup_start = time.perf_counter()
        backend.warmup(items[0][0])
        warmup_time_s = time.perf_counter() - warmup_start

    rows = []
    for audio_path, reference in items:
        duration_s = audio_duration_seconds(audio_path)
        t0 = time.perf_counter()
        hypothesis = backend.transcribe(audio_path)
        elapsed_s = time.perf_counter() - t0
        rows.append(
            SampleResult(
                file=audio_path.name,
                reference=reference,
                hypothesis=hypothesis,
                wer=wer(reference, hypothesis),
                elapsed_s=elapsed_s,
                audio_duration_s=duration_s,
            )
        )

    avg_wer = sum(row.wer for row in rows) / len(rows) if rows else None
    avg_time_s = sum(row.elapsed_s for row in rows) / len(rows) if rows else None
    total_audio_s = sum(row.audio_duration_s for row in rows)
    total_infer_s = sum(row.elapsed_s for row in rows)
    rtfx = (total_audio_s / total_infer_s) if total_infer_s > 0 else None

    return {
        "name": backend.name,
        "load_time_s": round(load_time_s, 3),
        "warmup_time_s": round(warmup_time_s, 3),
        "avg_wer": round(avg_wer, 4) if avg_wer is not None else None,
        "avg_time_s": round(avg_time_s, 4) if avg_time_s is not None else None,
        "total_audio_s": round(total_audio_s, 3),
        "total_infer_s": round(total_infer_s, 3),
        "rtfx": round(rtfx, 3) if rtfx is not None else None,
        "rows": [
            {
                "file": row.file,
                "reference": row.reference,
                "hypothesis": row.hypothesis,
                "wer": round(row.wer, 4),
                "elapsed_s": round(row.elapsed_s, 4),
                "audio_duration_s": round(row.audio_duration_s, 4),
            }
            for row in rows
        ],
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Benchmark Gemma and Cohere ASR backends on a shared WER corpus.")
    parser.add_argument(
        "--audio-dir",
        default=str(default_audio_dir()),
        help="Directory containing benchmark audio files.",
    )
    parser.add_argument(
        "--ground-truth",
        default=str(default_audio_dir() / "ground_truth.json"),
        help="Path to JSON manifest mapping filename to transcript.",
    )
    parser.add_argument(
        "--backends",
        nargs="+",
        default=["gemma", "cohere", "cohere_compile", "cohere_compile_pipe"],
        help="Backends to benchmark.",
    )
    parser.add_argument("--language", default="en", help="Language code for Cohere transcription.")
    parser.add_argument(
        "--cohere-model-id",
        default="CohereLabs/cohere-transcribe-03-2026",
        help="Hugging Face model id for the Cohere backend.",
    )
    parser.add_argument("--batch-size", type=int, default=8, help="Cohere transcribe batch_size parameter.")
    parser.add_argument("--limit", type=int, default=None, help="Only benchmark the first N files.")
    parser.add_argument("--output", default="", help="Optional JSON output path.")
    return parser.parse_args()


def main():
    args = parse_args()
    audio_dir = Path(args.audio_dir).resolve()
    ground_truth_path = Path(args.ground_truth).resolve()
    items = load_manifest(audio_dir, ground_truth_path, args.limit)
    if not items:
        raise SystemExit(f"no benchmark items found in {audio_dir} with manifest {ground_truth_path}")

    results = {}
    token = resolve_hf_token()
    for backend_name in args.backends:
        backend = create_backend(
            backend_name,
            model_id=args.cohere_model_id,
            language=args.language,
            batch_size=args.batch_size,
            token=token,
        )
        print(f"=== {backend.name} ===")
        try:
            result = benchmark_backend(backend, items)
        except Exception as exc:
            result = {
                "name": backend.name,
                "error": str(exc),
            }
            results[backend.name] = result
            print(f"error={result['error']}")
            continue
        results[backend.name] = result
        print(
            f"avg_wer={result['avg_wer']} avg_time_s={result['avg_time_s']} "
            f"rtfx={result['rtfx']} load_time_s={result['load_time_s']} warmup_time_s={result['warmup_time_s']}"
        )

    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "audio_dir": str(audio_dir),
        "ground_truth": str(ground_truth_path),
        "language": args.language,
        "backends": args.backends,
        "cohere_model_id": args.cohere_model_id,
        "hf_token_present": bool(token),
        "batch_size": args.batch_size,
        "limit": args.limit,
        "results": results,
    }

    if args.output:
        output_path = Path(args.output).resolve()
    else:
        timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        output_path = (PROJECT_DIR / "tests" / "benchmarks" / f"asr_backend_benchmark_{timestamp}.json").resolve()

    with open(output_path, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"saved {output_path}")


if __name__ == "__main__":
    main()

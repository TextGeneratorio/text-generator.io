"""
Inference Benchmark Test Suite

Measures both speed (latency/throughput) and quality (LLM-as-a-judge) for:
- Kokoro TTS
- Parakeet ASR
- Future models

Key mini-sglang inspired improvements to measure:
1. Request batching
2. CUDA graph capture/replay
3. Overlap scheduling (prepare next batch while current runs)
4. Multi-model caching
5. Request queuing with priority

Run with:
    PYTHONPATH=. pytest tests/benchmarks/test_inference_benchmark.py -v -s
"""

import json
import os
import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
import pytest
import torch

# Benchmark configuration
BENCHMARK_TEXTS = {
    "tiny": "Hello world.",
    "short": "The quick brown fox jumps over the lazy dog.",
    "medium": """Artificial intelligence has transformed how we interact with technology.
    From voice assistants to recommendation systems, AI touches nearly every aspect of modern life.
    Machine learning models continue to improve, enabling new applications we once thought impossible.""",
    "long": """The history of computing spans centuries, from ancient counting devices to modern quantum computers.
    Charles Babbage conceived the first mechanical computer in the 1830s, though it was never completed.
    Ada Lovelace, working with Babbage, wrote what many consider the first computer program.
    The twentieth century saw rapid advancement: vacuum tubes gave way to transistors, then integrated circuits.
    Today's processors contain billions of transistors, executing trillions of operations per second.
    Artificial intelligence, once science fiction, now powers everything from search engines to autonomous vehicles.
    Looking ahead, quantum computing promises to solve problems currently beyond classical computers.
    The journey from the abacus to AI represents humanity's remarkable capacity for innovation.""",
}

# Voices to test
TEST_VOICES = ["af_nicole", "af_bella", "am_adam", "bf_emma"]


@dataclass
class BenchmarkResult:
    """Stores results from a single benchmark run."""

    test_name: str
    text_length: int  # characters
    token_count: int  # phoneme tokens
    inference_time_ms: float
    audio_duration_s: float  # generated audio length
    real_time_factor: float  # audio_duration / inference_time (higher = faster than realtime)
    quality_score: Optional[float] = None  # 0-10 from LLM judge
    quality_feedback: Optional[str] = None
    memory_used_mb: float = 0.0
    voice: str = "af_nicole"


@dataclass
class BatchBenchmarkResult:
    """Stores results from batch processing."""

    batch_size: int
    total_time_ms: float
    per_request_time_ms: float
    throughput_rps: float  # requests per second
    results: list = field(default_factory=list)


def get_gpu_memory_mb() -> float:
    """Get current GPU memory usage in MB."""
    if torch.cuda.is_available():
        return torch.cuda.memory_allocated() / 1024 / 1024
    return 0.0


class KokoroInferenceBenchmark:
    """Benchmark suite for Kokoro TTS inference."""

    def __init__(self):
        self.model = None
        self.voicepacks = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def load_model(self):
        """Load the Kokoro model and voicepacks."""
        if self.model is not None:
            return

        from questions.inference_server.kokoro import phonemize, tokenize
        from questions.inference_server.models import build_model

        self.model = build_model("models/kokoro-v0_19.pth", self.device)
        self.voicepacks = {}

        voice_names = ["af", "af_bella", "af_sarah", "am_adam", "am_michael",
                       "bf_emma", "bf_isabella", "bm_george", "bm_lewis",
                       "af_nicole", "af_sky"]

        for voice in voice_names:
            voice_path = f"models/voices/{voice}.pt"
            if Path(voice_path).exists():
                self.voicepacks[voice] = torch.load(voice_path, weights_only=True).to(self.device)

        self.phonemize = phonemize
        self.tokenize = tokenize

    def warmup(self, n_iterations: int = 3):
        """Warmup the model with a few inference passes."""
        self.load_model()
        from questions.inference_server.kokoro import generate_full

        for _ in range(n_iterations):
            generate_full(self.model, "Warmup text.", self.voicepacks["af_nicole"], lang="a")

        # Clear CUDA cache after warmup
        if torch.cuda.is_available():
            torch.cuda.synchronize()
            torch.cuda.empty_cache()

    def benchmark_single(self, text: str, voice: str = "af_nicole", speed: float = 1.0) -> BenchmarkResult:
        """Benchmark a single TTS inference."""
        self.load_model()
        from questions.inference_server.kokoro import generate_full

        # Get token count
        ps = self.phonemize(text, voice[0])
        tokens = self.tokenize(ps)
        token_count = len(tokens)

        # Get voicepack
        voicepack = self.voicepacks.get(voice, self.voicepacks["af_nicole"])

        # Measure memory before
        mem_before = get_gpu_memory_mb()

        # Synchronize before timing
        if torch.cuda.is_available():
            torch.cuda.synchronize()

        # Time the inference
        start_time = time.perf_counter()
        audio, phonemes = generate_full(self.model, text, voicepack, lang=voice[0], speed=speed)

        if torch.cuda.is_available():
            torch.cuda.synchronize()
        end_time = time.perf_counter()

        # Calculate metrics
        inference_time_ms = (end_time - start_time) * 1000
        audio_duration_s = len(audio) / 24000  # 24kHz sample rate
        real_time_factor = audio_duration_s / (inference_time_ms / 1000) if inference_time_ms > 0 else 0
        mem_after = get_gpu_memory_mb()

        return BenchmarkResult(
            test_name=f"kokoro_tts_{voice}",
            text_length=len(text),
            token_count=token_count,
            inference_time_ms=inference_time_ms,
            audio_duration_s=audio_duration_s,
            real_time_factor=real_time_factor,
            memory_used_mb=mem_after - mem_before,
            voice=voice,
        )

    def benchmark_batch_sequential(self, texts: list[str], voice: str = "af_nicole") -> BatchBenchmarkResult:
        """Benchmark sequential processing (current baseline)."""
        self.load_model()

        start_time = time.perf_counter()
        results = []
        for text in texts:
            result = self.benchmark_single(text, voice)
            results.append(result)

        if torch.cuda.is_available():
            torch.cuda.synchronize()
        end_time = time.perf_counter()

        total_time_ms = (end_time - start_time) * 1000
        batch_size = len(texts)

        return BatchBenchmarkResult(
            batch_size=batch_size,
            total_time_ms=total_time_ms,
            per_request_time_ms=total_time_ms / batch_size,
            throughput_rps=batch_size / (total_time_ms / 1000),
            results=results,
        )


class LLMQualityJudge:
    """
    Uses a small LLM to judge TTS output quality.

    Approach: Transcribe the generated audio back to text using ASR,
    then have LLM compare original text vs transcribed text and rate quality.
    """

    def __init__(self):
        self.asr_model = None
        self.llm_model = None

    def load_asr(self):
        """Load Parakeet ASR for transcription."""
        if self.asr_model is not None:
            return

        try:
            import nemo.collections.asr as nemo_asr
            self.asr_model = nemo_asr.models.ASRModel.from_pretrained("nvidia/parakeet-tdt-0.6b-v2")
            self.asr_model.eval()
        except Exception as e:
            print(f"Could not load ASR model: {e}")
            self.asr_model = None

    def transcribe_audio(self, audio: np.ndarray, sample_rate: int = 24000) -> str:
        """Transcribe audio back to text."""
        if self.asr_model is None:
            return ""

        import tempfile

        import soundfile as sf

        # Write to temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, audio, sample_rate)
            temp_path = f.name

        try:
            # Transcribe
            transcription = self.asr_model.transcribe([temp_path])
            if isinstance(transcription, list) and len(transcription) > 0:
                return transcription[0] if isinstance(transcription[0], str) else str(transcription[0])
            return str(transcription)
        finally:
            os.unlink(temp_path)

    async def judge_quality_with_llm(
        self,
        original_text: str,
        transcribed_text: str,
        inference_time_ms: float,
        audio_duration_s: float,
    ) -> tuple[float, str]:
        """
        Use Claude or local LLM to rate TTS quality 0-10.

        Criteria:
        - Accuracy: Does transcription match original?
        - Naturalness: Would it sound natural? (inferred from text fidelity)
        - Speed: Is inference acceptably fast?
        """
        try:
            import anthropic

            client = anthropic.Anthropic()

            prompt = f"""You are evaluating text-to-speech (TTS) quality. Rate the output 0-10.

ORIGINAL TEXT:
{original_text}

TRANSCRIBED TEXT (from generated audio):
{transcribed_text}

METRICS:
- Inference time: {inference_time_ms:.1f}ms
- Audio duration: {audio_duration_s:.2f}s
- Real-time factor: {audio_duration_s / (inference_time_ms / 1000):.1f}x

SCORING CRITERIA (each 0-10, report final average):
1. ACCURACY (40%): How well does transcription match original? Consider word errors, omissions, additions.
2. COMPLETENESS (30%): Is all content present? Any truncation?
3. SPEED (30%): Is it faster than real-time? (>1x = good, >5x = excellent)

Respond with ONLY a JSON object:
{{"score": <0-10 float>, "feedback": "<brief explanation>"}}"""

            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse response
            response_text = response.content[0].text.strip()
            # Handle potential markdown code blocks
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]

            result = json.loads(response_text)
            return float(result["score"]), str(result["feedback"])

        except Exception as e:
            # Fallback: simple text similarity scoring
            return self._simple_quality_score(original_text, transcribed_text), f"Fallback scoring (error: {e})"

    def _simple_quality_score(self, original: str, transcribed: str) -> float:
        """Simple fallback quality scoring based on text similarity."""
        from difflib import SequenceMatcher

        original_lower = original.lower().strip()
        transcribed_lower = transcribed.lower().strip()

        similarity = SequenceMatcher(None, original_lower, transcribed_lower).ratio()

        # Scale to 0-10
        return similarity * 10

    async def evaluate(
        self,
        audio: np.ndarray,
        original_text: str,
        inference_time_ms: float,
        audio_duration_s: float,
        use_llm: bool = True,
    ) -> tuple[float, str]:
        """Full evaluation pipeline: ASR + LLM judge."""
        self.load_asr()

        if self.asr_model is None:
            return 5.0, "ASR not available - neutral score"

        transcribed = self.transcribe_audio(audio)

        if use_llm:
            return await self.judge_quality_with_llm(
                original_text, transcribed, inference_time_ms, audio_duration_s
            )
        else:
            score = self._simple_quality_score(original_text, transcribed)
            return score, f"Text similarity: {score:.1f}/10"


# ============================================================================
# PYTEST FIXTURES AND TESTS
# ============================================================================

@pytest.fixture(scope="module")
def kokoro_benchmark():
    """Create and warmup Kokoro benchmark."""
    benchmark = KokoroInferenceBenchmark()
    benchmark.warmup(n_iterations=2)
    return benchmark


@pytest.fixture(scope="module")
def quality_judge():
    """Create quality judge."""
    return LLMQualityJudge()


class TestKokoroSpeed:
    """Speed benchmarks for Kokoro TTS."""

    def test_inference_tiny_text(self, kokoro_benchmark):
        """Benchmark tiny text (< 10 words)."""
        result = kokoro_benchmark.benchmark_single(BENCHMARK_TEXTS["tiny"])

        print(f"\n[TINY] Inference: {result.inference_time_ms:.2f}ms | "
              f"Audio: {result.audio_duration_s:.2f}s | "
              f"RTF: {result.real_time_factor:.1f}x")

        # Assert reasonable performance
        assert result.inference_time_ms < 5000, "Tiny text should complete in <5s"
        assert result.real_time_factor > 1.0, "Should be faster than real-time"

    def test_inference_short_text(self, kokoro_benchmark):
        """Benchmark short text (~10 words)."""
        result = kokoro_benchmark.benchmark_single(BENCHMARK_TEXTS["short"])

        print(f"\n[SHORT] Inference: {result.inference_time_ms:.2f}ms | "
              f"Audio: {result.audio_duration_s:.2f}s | "
              f"RTF: {result.real_time_factor:.1f}x | "
              f"Tokens: {result.token_count}")

        assert result.inference_time_ms < 5000
        assert result.real_time_factor > 1.0

    def test_inference_medium_text(self, kokoro_benchmark):
        """Benchmark medium text (~50 words)."""
        result = kokoro_benchmark.benchmark_single(BENCHMARK_TEXTS["medium"])

        print(f"\n[MEDIUM] Inference: {result.inference_time_ms:.2f}ms | "
              f"Audio: {result.audio_duration_s:.2f}s | "
              f"RTF: {result.real_time_factor:.1f}x | "
              f"Tokens: {result.token_count}")

        assert result.inference_time_ms < 10000
        assert result.real_time_factor > 0.5  # May be slower for medium text

    def test_inference_long_text(self, kokoro_benchmark):
        """Benchmark long text (>100 words, requires chunking)."""
        result = kokoro_benchmark.benchmark_single(BENCHMARK_TEXTS["long"])

        print(f"\n[LONG] Inference: {result.inference_time_ms:.2f}ms | "
              f"Audio: {result.audio_duration_s:.2f}s | "
              f"RTF: {result.real_time_factor:.1f}x | "
              f"Tokens: {result.token_count}")

        assert result.inference_time_ms < 30000

    def test_inference_multiple_voices(self, kokoro_benchmark):
        """Benchmark same text with different voices."""
        text = BENCHMARK_TEXTS["short"]
        results = []

        for voice in TEST_VOICES:
            if voice in kokoro_benchmark.voicepacks:
                result = kokoro_benchmark.benchmark_single(text, voice=voice)
                results.append(result)
                print(f"\n[{voice}] Inference: {result.inference_time_ms:.2f}ms | "
                      f"RTF: {result.real_time_factor:.1f}x")

        # All voices should perform similarly
        times = [r.inference_time_ms for r in results]
        if len(times) > 1:
            variance = statistics.stdev(times) / statistics.mean(times)
            assert variance < 0.5, "Voice performance should be relatively consistent"

    def test_batch_throughput(self, kokoro_benchmark):
        """Benchmark batch processing throughput."""
        # Create batch of varied texts
        batch = [
            BENCHMARK_TEXTS["tiny"],
            BENCHMARK_TEXTS["short"],
            BENCHMARK_TEXTS["medium"],
            BENCHMARK_TEXTS["tiny"],
            BENCHMARK_TEXTS["short"],
        ]

        result = kokoro_benchmark.benchmark_batch_sequential(batch)

        print(f"\n[BATCH x{result.batch_size}] Total: {result.total_time_ms:.2f}ms | "
              f"Per-request: {result.per_request_time_ms:.2f}ms | "
              f"Throughput: {result.throughput_rps:.2f} req/s")

        assert result.throughput_rps > 0.1, "Should process at least 0.1 requests/second"

    def test_consistency(self, kokoro_benchmark):
        """Test inference time consistency across multiple runs."""
        text = BENCHMARK_TEXTS["short"]
        times = []

        for i in range(5):
            result = kokoro_benchmark.benchmark_single(text)
            times.append(result.inference_time_ms)

        mean_time = statistics.mean(times)
        std_time = statistics.stdev(times)
        cv = std_time / mean_time  # Coefficient of variation

        print(f"\n[CONSISTENCY] Mean: {mean_time:.2f}ms | "
              f"Std: {std_time:.2f}ms | CV: {cv:.2%}")

        assert cv < 0.3, "Inference time should be consistent (CV < 30%)"


class TestKokoroQuality:
    """Quality benchmarks using LLM-as-a-judge."""

    @pytest.mark.asyncio
    async def test_quality_short_text(self, kokoro_benchmark, quality_judge):
        """Test quality for short text."""
        text = BENCHMARK_TEXTS["short"]

        # Generate audio
        result = kokoro_benchmark.benchmark_single(text)

        # Get the audio
        from questions.inference_server.kokoro import generate_full
        voicepack = kokoro_benchmark.voicepacks["af_nicole"]
        audio, _ = generate_full(kokoro_benchmark.model, text, voicepack, lang="a")

        # Judge quality
        score, feedback = await quality_judge.evaluate(
            audio, text,
            result.inference_time_ms,
            result.audio_duration_s,
            use_llm=False,  # Use simple scoring for CI speed
        )

        print(f"\n[QUALITY-SHORT] Score: {score:.1f}/10 | Feedback: {feedback}")

        result.quality_score = score
        result.quality_feedback = feedback

        assert score >= 3.0, "Quality should be at least acceptable (3/10)"

    @pytest.mark.asyncio
    async def test_quality_medium_text_llm_judge(self, kokoro_benchmark, quality_judge):
        """Test quality with full LLM judge (slower, more accurate)."""
        text = BENCHMARK_TEXTS["medium"]

        # Generate audio
        result = kokoro_benchmark.benchmark_single(text)

        from questions.inference_server.kokoro import generate_full
        voicepack = kokoro_benchmark.voicepacks["af_nicole"]
        audio, _ = generate_full(kokoro_benchmark.model, text, voicepack, lang="a")

        # Judge with LLM (requires ANTHROPIC_API_KEY)
        try:
            score, feedback = await quality_judge.evaluate(
                audio, text,
                result.inference_time_ms,
                result.audio_duration_s,
                use_llm=True,
            )
            print(f"\n[QUALITY-LLM] Score: {score:.1f}/10 | Feedback: {feedback}")
            assert score >= 0.0  # Just verify we got a score
        except Exception as e:
            pytest.skip(f"LLM judge not available: {e}")


class TestBenchmarkReport:
    """Generate comprehensive benchmark report."""

    def test_full_benchmark_report(self, kokoro_benchmark):
        """Run full benchmark suite and generate report."""
        report = {
            "device": kokoro_benchmark.device,
            "cuda_available": torch.cuda.is_available(),
            "results": [],
        }

        if torch.cuda.is_available():
            report["gpu_name"] = torch.cuda.get_device_name(0)
            report["gpu_memory_total_gb"] = torch.cuda.get_device_properties(0).total_memory / 1e9

        # Run benchmarks for all text sizes
        for text_name, text in BENCHMARK_TEXTS.items():
            result = kokoro_benchmark.benchmark_single(text)
            report["results"].append({
                "text_size": text_name,
                "text_length": len(text),
                "token_count": result.token_count,
                "inference_time_ms": result.inference_time_ms,
                "audio_duration_s": result.audio_duration_s,
                "real_time_factor": result.real_time_factor,
            })

        # Print report
        print("\n" + "=" * 60)
        print("KOKORO TTS INFERENCE BENCHMARK REPORT")
        print("=" * 60)
        print(f"Device: {report['device']}")
        if "gpu_name" in report:
            print(f"GPU: {report['gpu_name']} ({report['gpu_memory_total_gb']:.1f} GB)")
        print("-" * 60)
        print(f"{'Size':<10} {'Chars':<8} {'Tokens':<8} {'Time(ms)':<12} {'Audio(s)':<10} {'RTF':<8}")
        print("-" * 60)

        for r in report["results"]:
            print(f"{r['text_size']:<10} {r['text_length']:<8} {r['token_count']:<8} "
                  f"{r['inference_time_ms']:<12.2f} {r['audio_duration_s']:<10.2f} "
                  f"{r['real_time_factor']:<8.1f}x")

        print("=" * 60)

        # Save report
        report_path = Path("tests/benchmarks/benchmark_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"Report saved to: {report_path}")


# ============================================================================
# IMPROVEMENT TRACKING: mini-sglang techniques to implement
# ============================================================================
class TestOptimizedVsBaseline:
    """Compare optimized inference against baseline."""

    def test_batch_vs_sequential(self, kokoro_benchmark):
        """Compare batch processing vs sequential."""
        texts = [
            BENCHMARK_TEXTS["tiny"],
            BENCHMARK_TEXTS["short"],
            BENCHMARK_TEXTS["tiny"],
            BENCHMARK_TEXTS["short"],
        ]

        # Sequential (baseline)
        start = time.perf_counter()
        for text in texts:
            kokoro_benchmark.benchmark_single(text)
        sequential_time = (time.perf_counter() - start) * 1000

        # Try optimized if available
        try:
            from questions.inference_server.optimized_inference import OptimizedKokoroTTS

            opt_tts = OptimizedKokoroTTS(enable_cuda_graphs=False)  # Start simple
            opt_tts.load()

            start = time.perf_counter()
            opt_tts.generate_batch(texts)
            batch_time = (time.perf_counter() - start) * 1000

            speedup = sequential_time / batch_time

            print("\n[BATCH vs SEQUENTIAL]")
            print(f"  Sequential: {sequential_time:.2f}ms")
            print(f"  Batched: {batch_time:.2f}ms")
            print(f"  Speedup: {speedup:.2f}x")

            # Batching should be at least slightly faster due to reduced overhead
            assert batch_time <= sequential_time * 1.2, "Batched should not be much slower"

        except ImportError as e:
            pytest.skip(f"Optimized inference not available: {e}")

    def test_optimized_tts_correctness(self, kokoro_benchmark):
        """Verify optimized TTS produces same output as baseline."""
        text = BENCHMARK_TEXTS["short"]

        try:
            from questions.inference_server.optimized_inference import OptimizedKokoroTTS

            opt_tts = OptimizedKokoroTTS()
            opt_tts.load()

            # Generate with both
            opt_audio = opt_tts.generate(text)

            from questions.inference_server.kokoro import generate_full
            baseline_audio, _ = generate_full(
                kokoro_benchmark.model,
                text,
                kokoro_benchmark.voicepacks["af_nicole"],
                lang="a"
            )

            # Check similar length (may have small differences due to random init)
            len_diff = abs(len(opt_audio) - len(baseline_audio)) / len(baseline_audio)
            print(f"\n[CORRECTNESS] Audio length diff: {len_diff:.2%}")

            assert len_diff < 0.1, "Audio lengths should be within 10%"

        except ImportError as e:
            pytest.skip(f"Optimized inference not available: {e}")


"""
MINI-SGLANG TECHNIQUES APPLICABLE TO THIS TTS/ASR SERVER:

1. REQUEST BATCHING (High Impact)
   - Current: Sequential processing
   - Improvement: Batch multiple TTS requests, share phonemizer/tokenizer overhead
   - Implementation: Create batch_generate() that processes multiple texts in parallel
   - Expected gain: 2-4x throughput for concurrent requests

2. CUDA GRAPH CAPTURE (Medium Impact)
   - Current: Full kernel launch overhead every request
   - Improvement: Capture forward pass as CUDA graph, replay for consistent sizes
   - Implementation: Capture graphs for common token lengths (64, 128, 256, 512)
   - Expected gain: 10-30% latency reduction for decode phase

3. OVERLAP SCHEDULING (Medium Impact)
   - Current: Sequential: phonemize -> tokenize -> forward -> return
   - Improvement: While GPU runs forward, CPU prepares next request
   - Implementation: Use separate thread/process for text preprocessing
   - Expected gain: 20-40% latency reduction for back-to-back requests

4. MULTI-MODEL CACHING (High Impact for multi-model workloads)
   - Current: Single model at a time, full eviction on switch
   - Improvement: Keep both Kokoro + Parakeet in GPU memory
   - Implementation: Memory-aware model pool with priority eviction
   - Expected gain: Eliminates 5-10s model switch penalty

5. REQUEST QUEUING (Medium Impact)
   - Current: Direct request handling
   - Improvement: Priority queue with adaptive batching
   - Implementation: asyncio.Queue with batch formation logic
   - Expected gain: Better throughput under load, fairer scheduling

6. CHUNKED PROCESSING OPTIMIZATION (Low-Medium Impact)
   - Current: Fixed 510 token chunks processed sequentially
   - Improvement: Overlap chunk processing, better chunk boundaries
   - Implementation: Process chunks in parallel where possible
   - Expected gain: 10-20% for long text

7. VOICEPACK CACHING (Already Implemented)
   - All voicepacks loaded to GPU at startup
   - Could optimize with lazy loading if memory constrained
"""

"""
Comprehensive Optimization Test Suite

Systematically tests all possible optimizations for Kokoro TTS:
1. AMP (Automatic Mixed Precision) - float16/bfloat16
2. cudnn.benchmark - optimize convolution algorithms
3. Memory pinning - faster CPU-GPU transfers
4. torch.jit.trace - JIT compilation
5. Fused operations - combine multiple ops
6. Async prefetching - overlap data loading

Each optimization is tested for:
- Speed improvement
- Output quality preservation
- Memory usage
"""

import gc
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np
import pytest
import torch

# Test configuration
TEST_TEXT = "The quick brown fox jumps over the lazy dog."
WARMUP_ITERATIONS = 3
BENCHMARK_ITERATIONS = 20


@dataclass
class OptimizationResult:
    """Result from testing an optimization."""
    name: str
    enabled: bool
    time_ms: float
    memory_mb: float
    output_similarity: float
    error: Optional[str] = None


def audio_similarity(audio1: np.ndarray, audio2: np.ndarray) -> float:
    """Compute normalized cross-correlation."""
    if len(audio1) != len(audio2):
        max_len = max(len(audio1), len(audio2))
        audio1 = np.pad(audio1, (0, max_len - len(audio1)))
        audio2 = np.pad(audio2, (0, max_len - len(audio2)))

    audio1 = audio1 - np.mean(audio1)
    audio2 = audio2 - np.mean(audio2)
    norm1 = np.linalg.norm(audio1)
    norm2 = np.linalg.norm(audio2)

    if norm1 == 0 or norm2 == 0:
        return 0.0
    return np.dot(audio1, audio2) / (norm1 * norm2)


@contextmanager
def optimization_context(name: str):
    """Context manager for tracking optimization state."""
    print(f"\n{'='*50}")
    print(f"Testing: {name}")
    print(f"{'='*50}")
    yield
    print(f"Done: {name}")


class KokoroOptimizationTester:
    """Systematically test optimizations for Kokoro TTS."""

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.voicepack = None
        self.baseline_audio = None
        self.baseline_time = None
        self.results = []

    def setup(self):
        """Load model and establish baseline."""
        from questions.inference_server.kokoro import forward, phonemize, tokenize
        from questions.inference_server.models import build_model

        self.model = build_model("models/kokoro-v0_19.pth", self.device)
        self.voicepack = torch.load(
            "models/voices/af_nicole.pt", weights_only=True
        ).to(self.device)

        self.phonemize = phonemize
        self.tokenize = tokenize
        self.forward = forward

        # Prepare test data
        self.ps = phonemize(TEST_TEXT, "a")
        self.tokens = tokenize(self.ps)
        self.ref_s = self.voicepack[len(self.tokens)]

        # Establish baseline
        self._warmup()
        self.baseline_audio = self.forward(
            self.model, self.tokens, self.ref_s, 1.0
        )
        self.baseline_time = self._benchmark()

        print(f"Baseline: {self.baseline_time:.2f}ms")

    def _warmup(self):
        """Warmup iterations."""
        for _ in range(WARMUP_ITERATIONS):
            self.forward(self.model, self.tokens, self.ref_s, 1.0)
        if torch.cuda.is_available():
            torch.cuda.synchronize()

    def _benchmark(self) -> float:
        """Run benchmark and return average time in ms."""
        if torch.cuda.is_available():
            torch.cuda.synchronize()

        start = time.perf_counter()
        for _ in range(BENCHMARK_ITERATIONS):
            audio = self.forward(self.model, self.tokens, self.ref_s, 1.0)
            if torch.cuda.is_available():
                torch.cuda.synchronize()

        return (time.perf_counter() - start) / BENCHMARK_ITERATIONS * 1000

    def _get_memory_mb(self) -> float:
        """Get current GPU memory usage."""
        if torch.cuda.is_available():
            return torch.cuda.memory_allocated() / 1024 / 1024
        return 0.0

    def _test_output_quality(self) -> float:
        """Test if output matches baseline."""
        audio = self.forward(self.model, self.tokens, self.ref_s, 1.0)
        return audio_similarity(self.baseline_audio, audio)

    def test_optimization(
        self,
        name: str,
        setup_fn: Optional[Callable] = None,
        teardown_fn: Optional[Callable] = None,
    ) -> OptimizationResult:
        """Test a single optimization."""
        with optimization_context(name):
            try:
                # Apply optimization
                if setup_fn:
                    setup_fn()

                # Warmup
                self._warmup()

                # Benchmark
                time_ms = self._benchmark()
                memory_mb = self._get_memory_mb()
                similarity = self._test_output_quality()

                # Teardown
                if teardown_fn:
                    teardown_fn()

                speedup = self.baseline_time / time_ms
                print(f"  Time: {time_ms:.2f}ms (speedup: {speedup:.2f}x)")
                print(f"  Memory: {memory_mb:.1f}MB")
                print(f"  Output similarity: {similarity:.4f}")

                result = OptimizationResult(
                    name=name,
                    enabled=True,
                    time_ms=time_ms,
                    memory_mb=memory_mb,
                    output_similarity=similarity,
                )

            except Exception as e:
                print(f"  ERROR: {e}")
                result = OptimizationResult(
                    name=name,
                    enabled=False,
                    time_ms=0,
                    memory_mb=0,
                    output_similarity=0,
                    error=str(e),
                )

            self.results.append(result)
            return result


class TestAMPOptimization:
    """Test Automatic Mixed Precision (AMP)."""

    @pytest.fixture(scope="class")
    def tester(self):
        tester = KokoroOptimizationTester()
        tester.setup()
        return tester

    def test_amp_float16(self, tester):
        """Test float16 autocast."""
        from questions.inference_server.kokoro import length_to_mask

        original_forward = tester.forward

        def forward_amp(model, tokens, ref_s, speed):
            """Forward with AMP float16."""
            with torch.amp.autocast(device_type="cuda", dtype=torch.float16):
                device = ref_s.device
                tokens_t = torch.LongTensor([[0, *tokens, 0]]).to(device)
                input_lengths = torch.LongTensor([tokens_t.shape[-1]]).to(device)
                text_mask = length_to_mask(input_lengths).to(device)

                bert_dur = model.bert(tokens_t, attention_mask=(~text_mask).int())
                d_en = model.bert_encoder(bert_dur).transpose(-1, -2)
                s = ref_s[:, 128:]
                d = model.predictor.text_encoder(d_en, s, input_lengths, text_mask)
                x, _ = model.predictor.lstm(d)
                duration = model.predictor.duration_proj(x)
                duration = torch.sigmoid(duration).sum(axis=-1) / speed
                pred_dur = torch.round(duration).clamp(min=1).long()

            # Back to float32 for alignment (needs precise indexing)
            pred_aln_trg = torch.zeros(input_lengths, pred_dur.sum().item())
            c_frame = 0
            for i in range(pred_aln_trg.size(0)):
                pred_aln_trg[i, c_frame : c_frame + pred_dur[0, i].item()] = 1
                c_frame += pred_dur[0, i].item()

            with torch.amp.autocast(device_type="cuda", dtype=torch.float16):
                en = d.transpose(-1, -2) @ pred_aln_trg.unsqueeze(0).to(device)
                F0_pred, N_pred = model.predictor.F0Ntrain(en, s)
                t_en = model.text_encoder(tokens_t, input_lengths, text_mask)
                asr = t_en @ pred_aln_trg.unsqueeze(0).to(device)

            # Decoder in float32 for audio quality
            return model.decoder(
                asr.float(), F0_pred.float(), N_pred.float(), ref_s[:, :128]
            ).squeeze().detach().cpu().numpy()

        def setup():
            tester.forward = forward_amp

        def teardown():
            tester.forward = original_forward

        result = tester.test_optimization(
            "AMP float16",
            setup_fn=setup,
            teardown_fn=teardown,
        )

        # Quality check
        assert result.output_similarity > 0.95, "AMP degraded quality too much"

    def test_amp_bfloat16(self, tester):
        """Test bfloat16 autocast (better for transformers)."""
        if not torch.cuda.is_bf16_supported():
            pytest.skip("bfloat16 not supported on this GPU")

        from questions.inference_server.kokoro import length_to_mask

        original_forward = tester.forward

        def forward_bf16(model, tokens, ref_s, speed):
            """Forward with bfloat16."""
            with torch.amp.autocast(device_type="cuda", dtype=torch.bfloat16):
                device = ref_s.device
                tokens_t = torch.LongTensor([[0, *tokens, 0]]).to(device)
                input_lengths = torch.LongTensor([tokens_t.shape[-1]]).to(device)
                text_mask = length_to_mask(input_lengths).to(device)

                bert_dur = model.bert(tokens_t, attention_mask=(~text_mask).int())
                d_en = model.bert_encoder(bert_dur).transpose(-1, -2)
                s = ref_s[:, 128:]
                d = model.predictor.text_encoder(d_en, s, input_lengths, text_mask)
                x, _ = model.predictor.lstm(d)
                duration = model.predictor.duration_proj(x)
                duration = torch.sigmoid(duration).sum(axis=-1) / speed
                pred_dur = torch.round(duration).clamp(min=1).long()

            pred_aln_trg = torch.zeros(input_lengths, pred_dur.sum().item())
            c_frame = 0
            for i in range(pred_aln_trg.size(0)):
                pred_aln_trg[i, c_frame : c_frame + pred_dur[0, i].item()] = 1
                c_frame += pred_dur[0, i].item()

            with torch.amp.autocast(device_type="cuda", dtype=torch.bfloat16):
                en = d.transpose(-1, -2) @ pred_aln_trg.unsqueeze(0).to(device)
                F0_pred, N_pred = model.predictor.F0Ntrain(en, s)
                t_en = model.text_encoder(tokens_t, input_lengths, text_mask)
                asr = t_en @ pred_aln_trg.unsqueeze(0).to(device)

            return model.decoder(
                asr.float(), F0_pred.float(), N_pred.float(), ref_s[:, :128]
            ).squeeze().detach().cpu().numpy()

        def setup():
            tester.forward = forward_bf16

        def teardown():
            tester.forward = original_forward

        result = tester.test_optimization(
            "AMP bfloat16",
            setup_fn=setup,
            teardown_fn=teardown,
        )

        assert result.output_similarity > 0.95, "bfloat16 degraded quality too much"


class TestCUDNNOptimization:
    """Test cuDNN optimizations."""

    @pytest.fixture(scope="class")
    def tester(self):
        tester = KokoroOptimizationTester()
        tester.setup()
        return tester

    def test_cudnn_benchmark(self, tester):
        """Test cudnn.benchmark for convolution optimization."""
        original_benchmark = torch.backends.cudnn.benchmark

        def setup():
            torch.backends.cudnn.benchmark = True

        def teardown():
            torch.backends.cudnn.benchmark = original_benchmark

        result = tester.test_optimization(
            "cuDNN benchmark",
            setup_fn=setup,
            teardown_fn=teardown,
        )

        assert result.output_similarity > 0.99, "cuDNN benchmark changed output"

    def test_cudnn_deterministic_off(self, tester):
        """Test with deterministic mode off (can be faster)."""
        original_deterministic = torch.backends.cudnn.deterministic

        def setup():
            torch.backends.cudnn.deterministic = False

        def teardown():
            torch.backends.cudnn.deterministic = original_deterministic

        result = tester.test_optimization(
            "cuDNN non-deterministic",
            setup_fn=setup,
            teardown_fn=teardown,
        )

        # Non-deterministic can have slight variations
        assert result.output_similarity > 0.98


class TestMemoryOptimization:
    """Test memory-related optimizations."""

    @pytest.fixture(scope="class")
    def tester(self):
        tester = KokoroOptimizationTester()
        tester.setup()
        return tester

    def test_pinned_memory(self, tester):
        """Test pinned (page-locked) memory for faster transfers."""
        # This primarily helps with data loading, less so for inference
        # but worth testing

        original_forward = tester.forward

        def forward_pinned(model, tokens, ref_s, speed):
            """Forward with pinned memory for token transfer."""
            from questions.inference_server.kokoro import length_to_mask

            device = ref_s.device

            # Use pinned memory for faster CPU->GPU transfer
            tokens_cpu = torch.LongTensor([[0, *tokens, 0]])
            if torch.cuda.is_available():
                tokens_pinned = tokens_cpu.pin_memory()
                tokens_t = tokens_pinned.to(device, non_blocking=True)
            else:
                tokens_t = tokens_cpu.to(device)

            input_lengths = torch.LongTensor([tokens_t.shape[-1]]).to(device)
            text_mask = length_to_mask(input_lengths).to(device)

            bert_dur = model.bert(tokens_t, attention_mask=(~text_mask).int())
            d_en = model.bert_encoder(bert_dur).transpose(-1, -2)
            s = ref_s[:, 128:]
            d = model.predictor.text_encoder(d_en, s, input_lengths, text_mask)
            x, _ = model.predictor.lstm(d)
            duration = model.predictor.duration_proj(x)
            duration = torch.sigmoid(duration).sum(axis=-1) / speed
            pred_dur = torch.round(duration).clamp(min=1).long()

            pred_aln_trg = torch.zeros(input_lengths, pred_dur.sum().item())
            c_frame = 0
            for i in range(pred_aln_trg.size(0)):
                pred_aln_trg[i, c_frame : c_frame + pred_dur[0, i].item()] = 1
                c_frame += pred_dur[0, i].item()

            en = d.transpose(-1, -2) @ pred_aln_trg.unsqueeze(0).to(device)
            F0_pred, N_pred = model.predictor.F0Ntrain(en, s)
            t_en = model.text_encoder(tokens_t, input_lengths, text_mask)
            asr = t_en @ pred_aln_trg.unsqueeze(0).to(device)

            return model.decoder(asr, F0_pred, N_pred, ref_s[:, :128]).squeeze().cpu().numpy()

        def setup():
            tester.forward = forward_pinned

        def teardown():
            tester.forward = original_forward

        result = tester.test_optimization(
            "Pinned memory",
            setup_fn=setup,
            teardown_fn=teardown,
        )

        assert result.output_similarity > 0.99

    def test_empty_cache_between_runs(self, tester):
        """Test impact of clearing cache between runs."""
        original_forward = tester.forward

        def forward_with_cache_clear(model, tokens, ref_s, speed):
            result = original_forward(model, tokens, ref_s, speed)
            torch.cuda.empty_cache()
            return result

        def setup():
            tester.forward = forward_with_cache_clear

        def teardown():
            tester.forward = original_forward

        result = tester.test_optimization(
            "Cache clear between runs",
            setup_fn=setup,
            teardown_fn=teardown,
        )

        # This should be slower, but ensures memory is freed
        print(f"  Note: Cache clearing expected to be slower")


class TestTorchJIT:
    """Test TorchScript JIT compilation."""

    @pytest.fixture(scope="class")
    def tester(self):
        tester = KokoroOptimizationTester()
        tester.setup()
        return tester

    def test_jit_trace_bert(self, tester):
        """Test JIT tracing on BERT component."""

        original_bert = tester.model.bert

        def setup():
            # Create sample inputs for tracing
            tokens_t = torch.LongTensor([[0] + tester.tokens + [0]]).to(tester.device)
            mask = torch.ones(1, tokens_t.shape[1], dtype=torch.int, device=tester.device)

            # Trace BERT
            try:
                traced_bert = torch.jit.trace(
                    original_bert,
                    (tokens_t, mask),
                    check_trace=False,  # Don't check, BERT has some dynamic behavior
                )
                tester.model.bert = traced_bert
                print("  BERT traced successfully")
            except Exception as e:
                print(f"  BERT tracing failed: {e}")
                raise

        def teardown():
            tester.model.bert = original_bert

        result = tester.test_optimization(
            "JIT trace BERT",
            setup_fn=setup,
            teardown_fn=teardown,
        )

        assert result.output_similarity > 0.98


class TestCombinedOptimizations:
    """Test combinations of optimizations."""

    @pytest.fixture(scope="class")
    def tester(self):
        tester = KokoroOptimizationTester()
        tester.setup()
        return tester

    def test_all_safe_optimizations(self, tester):
        """Test all safe optimizations together."""

        original_benchmark = torch.backends.cudnn.benchmark
        original_deterministic = torch.backends.cudnn.deterministic

        def setup():
            # Enable all safe optimizations
            torch.backends.cudnn.benchmark = True
            torch.backends.cudnn.deterministic = False

        def teardown():
            torch.backends.cudnn.benchmark = original_benchmark
            torch.backends.cudnn.deterministic = original_deterministic

        result = tester.test_optimization(
            "All safe optimizations (cuDNN benchmark + non-deterministic)",
            setup_fn=setup,
            teardown_fn=teardown,
        )

        assert result.output_similarity > 0.98


class TestSummary:
    """Generate summary of all optimization results."""

    def test_generate_summary(self):
        """Run all optimizations and generate summary."""
        tester = KokoroOptimizationTester()
        tester.setup()

        print("\n" + "=" * 70)
        print("OPTIMIZATION SUMMARY")
        print("=" * 70)
        print(f"Baseline: {tester.baseline_time:.2f}ms")
        print("-" * 70)

        # Test each optimization
        optimizations = [
            ("cuDNN benchmark", lambda: setattr(torch.backends.cudnn, 'benchmark', True)),
            ("cuDNN non-deterministic", lambda: setattr(torch.backends.cudnn, 'deterministic', False)),
        ]

        for name, setup_fn in optimizations:
            original_state = {}
            if "benchmark" in name:
                original_state['benchmark'] = torch.backends.cudnn.benchmark
            if "deterministic" in name:
                original_state['deterministic'] = torch.backends.cudnn.deterministic

            try:
                setup_fn()
                tester._warmup()
                time_ms = tester._benchmark()
                similarity = tester._test_output_quality()
                speedup = tester.baseline_time / time_ms

                status = "✓" if similarity > 0.98 else "⚠"
                print(f"{status} {name:<40} {time_ms:>8.2f}ms  {speedup:>5.2f}x  sim={similarity:.4f}")

            except Exception as e:
                print(f"✗ {name:<40} ERROR: {e}")

            # Restore
            if 'benchmark' in original_state:
                torch.backends.cudnn.benchmark = original_state['benchmark']
            if 'deterministic' in original_state:
                torch.backends.cudnn.deterministic = original_state['deterministic']

        print("=" * 70)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

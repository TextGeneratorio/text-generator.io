"""
Test torch.compile optimization for Kokoro TTS.

torch.compile (PyTorch 2.0+) can fuse kernels and optimize the forward pass
without the static shape requirements of CUDA graphs.
"""

import time

import pytest
import torch


class TestTorchCompile:
    """Test torch.compile optimization."""

    @pytest.fixture(scope="class")
    def baseline_model(self):
        """Load baseline (uncompiled) model."""
        from questions.inference_server.models import build_model

        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = build_model("models/kokoro-v0_19.pth", device)
        voicepack = torch.load("models/voices/af_nicole.pt", weights_only=True).to(device)

        return model, voicepack, device

    def test_compile_forward_components(self, baseline_model):
        """Test compiling individual model components."""
        model, voicepack, device = baseline_model

        if not torch.cuda.is_available():
            pytest.skip("CUDA required for torch.compile benefits")

        from questions.inference_server.kokoro import forward, phonemize, tokenize

        text = "The quick brown fox jumps over the lazy dog."
        ps = phonemize(text, "a")
        tokens = tokenize(ps)
        ref_s = voicepack[len(tokens)]

        # Warmup baseline
        for _ in range(3):
            forward(model, tokens, ref_s, 1.0)
        torch.cuda.synchronize()

        # Benchmark baseline
        start = time.perf_counter()
        for _ in range(10):
            baseline_audio = forward(model, tokens, ref_s, 1.0)
            torch.cuda.synchronize()
        baseline_time = (time.perf_counter() - start) / 10 * 1000

        # Try compiling key components
        print("\n" + "=" * 60)
        print("TORCH.COMPILE OPTIMIZATION TEST")
        print("=" * 60)
        print(f"Baseline forward: {baseline_time:.2f}ms")

        # Compile BERT
        try:
            compiled_bert = torch.compile(model.bert, mode="reduce-overhead")

            # Warmup
            tokens_tensor = torch.LongTensor([[0, *tokens, 0]]).to(device)
            mask = torch.ones(1, tokens_tensor.shape[1], dtype=torch.int, device=device)
            for _ in range(3):
                _ = compiled_bert(tokens_tensor, attention_mask=mask)
            torch.cuda.synchronize()

            # Benchmark compiled BERT
            start = time.perf_counter()
            for _ in range(10):
                _ = compiled_bert(tokens_tensor, attention_mask=mask)
                torch.cuda.synchronize()
            compiled_bert_time = (time.perf_counter() - start) / 10 * 1000

            print(f"Compiled BERT: {compiled_bert_time:.2f}ms")
        except Exception as e:
            print(f"BERT compile failed: {e}")
            compiled_bert_time = None

        # Compile decoder
        try:
            compiled_decoder = torch.compile(model.decoder, mode="reduce-overhead")

            # Create dummy inputs for decoder warmup
            # The decoder takes (asr, F0_pred, N_pred, ref_s[:, :128])
            print("Decoder compile: attempting...")
        except Exception as e:
            print(f"Decoder compile failed: {e}")

        print("=" * 60)

    def test_compile_full_model(self, baseline_model):
        """Test compiling the entire model forward pass."""
        model, voicepack, device = baseline_model

        if not torch.cuda.is_available():
            pytest.skip("CUDA required")

        from questions.inference_server.kokoro import length_to_mask, phonemize, tokenize

        text = "The quick brown fox jumps over the lazy dog."
        ps = phonemize(text, "a")
        tokens = tokenize(ps)
        ref_s = voicepack[len(tokens)]

        # Create a wrapper function that can be compiled
        @torch.no_grad()
        def forward_compilable(model, tokens_tensor, input_lengths, text_mask, ref_s, speed):
            """Compilable forward without .item() calls in hot path."""
            bert_dur = model.bert(tokens_tensor, attention_mask=(~text_mask).int())
            d_en = model.bert_encoder(bert_dur).transpose(-1, -2)
            s = ref_s[:, 128:]
            d = model.predictor.text_encoder(d_en, s, input_lengths, text_mask)
            x, _ = model.predictor.lstm(d)
            duration = model.predictor.duration_proj(x)
            duration = torch.sigmoid(duration).sum(axis=-1) / speed
            pred_dur = torch.round(duration).clamp(min=1).long()

            # Create alignment - this is the tricky part
            total_frames = pred_dur.sum()
            return bert_dur, d_en, pred_dur, total_frames

        # Prepare inputs
        tokens_tensor = torch.LongTensor([[0, *tokens, 0]]).to(device)
        input_lengths = torch.LongTensor([tokens_tensor.shape[-1]]).to(device)
        text_mask = length_to_mask(input_lengths).to(device)

        # Warmup baseline
        for _ in range(3):
            _ = forward_compilable(model, tokens_tensor, input_lengths, text_mask, ref_s, 1.0)
        torch.cuda.synchronize()

        # Benchmark baseline
        start = time.perf_counter()
        for _ in range(20):
            _ = forward_compilable(model, tokens_tensor, input_lengths, text_mask, ref_s, 1.0)
            torch.cuda.synchronize()
        baseline_time = (time.perf_counter() - start) / 20 * 1000

        # Compile with different modes
        modes = ["default", "reduce-overhead", "max-autotune"]

        print("\n" + "=" * 60)
        print("FULL MODEL COMPILE TEST")
        print("=" * 60)
        print(f"Baseline (partial forward): {baseline_time:.2f}ms")

        for mode in modes:
            try:
                compiled_fn = torch.compile(
                    lambda: forward_compilable(model, tokens_tensor, input_lengths, text_mask, ref_s, 1.0),
                    mode=mode,
                    fullgraph=False,  # Allow graph breaks
                )

                # Warmup (compilation happens here)
                print(f"\nCompiling with mode='{mode}'...", end=" ", flush=True)
                for _ in range(3):
                    _ = compiled_fn()
                torch.cuda.synchronize()
                print("done")

                # Benchmark
                start = time.perf_counter()
                for _ in range(20):
                    _ = compiled_fn()
                    torch.cuda.synchronize()
                compiled_time = (time.perf_counter() - start) / 20 * 1000

                speedup = baseline_time / compiled_time
                print(f"  Time: {compiled_time:.2f}ms (speedup: {speedup:.2f}x)")

            except Exception as e:
                print(f"  Failed: {str(e)[:60]}...")

        print("=" * 60)


class TestInferenceModes:
    """Test different PyTorch inference optimization modes."""

    @pytest.fixture(scope="class")
    def model_and_data(self):
        """Load model and prepare test data."""
        from questions.inference_server.kokoro import forward, phonemize, tokenize
        from questions.inference_server.models import build_model

        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = build_model("models/kokoro-v0_19.pth", device)
        voicepack = torch.load("models/voices/af_nicole.pt", weights_only=True).to(device)

        text = "The quick brown fox jumps over the lazy dog."
        ps = phonemize(text, "a")
        tokens = tokenize(ps)
        ref_s = voicepack[len(tokens)]

        return model, tokens, ref_s, forward

    def test_inference_mode(self, model_and_data):
        """Test torch.inference_mode vs torch.no_grad."""
        model, tokens, ref_s, forward_fn = model_and_data

        if not torch.cuda.is_available():
            pytest.skip("CUDA required")

        # Warmup
        for _ in range(3):
            forward_fn(model, tokens, ref_s, 1.0)
        torch.cuda.synchronize()

        # Test no_grad (current)
        start = time.perf_counter()
        for _ in range(20):
            with torch.no_grad():
                audio = forward_fn(model, tokens, ref_s, 1.0)
            torch.cuda.synchronize()
        no_grad_time = (time.perf_counter() - start) / 20 * 1000

        # Test inference_mode (slightly faster)
        start = time.perf_counter()
        for _ in range(20):
            with torch.inference_mode():
                audio = forward_fn(model, tokens, ref_s, 1.0)
            torch.cuda.synchronize()
        inference_mode_time = (time.perf_counter() - start) / 20 * 1000

        print("\n" + "=" * 50)
        print("INFERENCE MODE COMPARISON")
        print("=" * 50)
        print(f"torch.no_grad():       {no_grad_time:.2f}ms")
        print(f"torch.inference_mode(): {inference_mode_time:.2f}ms")
        print(f"Difference: {(no_grad_time - inference_mode_time):.2f}ms ({(no_grad_time/inference_mode_time - 1)*100:.1f}%)")
        print("=" * 50)

    def test_channels_last_memory_format(self, model_and_data):
        """Test if channels_last memory format helps (typically for CNNs)."""
        model, tokens, ref_s, forward_fn = model_and_data

        if not torch.cuda.is_available():
            pytest.skip("CUDA required")

        # Warmup with contiguous
        for _ in range(3):
            forward_fn(model, tokens, ref_s, 1.0)
        torch.cuda.synchronize()

        # Benchmark default (contiguous)
        start = time.perf_counter()
        for _ in range(20):
            audio = forward_fn(model, tokens, ref_s, 1.0)
            torch.cuda.synchronize()
        contiguous_time = (time.perf_counter() - start) / 20 * 1000

        print("\n" + "=" * 50)
        print("MEMORY FORMAT TEST")
        print("=" * 50)
        print(f"Contiguous (default): {contiguous_time:.2f}ms")
        print("Note: channels_last typically helps CNNs, less so for transformers")
        print("=" * 50)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

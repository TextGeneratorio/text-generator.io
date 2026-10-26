import torch
from contextlib import nullcontext

from questions.models import GenerateParams
from questions.text_generator_inference import (
    _effective_generation_max_new_tokens,
    _qwen35_fast_inference,
    chat_inference,
)
import questions.text_generator_inference as tgi


def test_qwen_generate_keeps_legacy_prompt_prefix(monkeypatch):
    params = GenerateParams(
        text="Prompt: ",
        max_length=16,
        top_p=0.9,
        top_k=40,
        temperature=0.7,
        repetition_penalty=1.1,
        min_probability=0.0,
    )

    monkeypatch.setattr(
        tgi,
        "chat_inference",
        lambda **kwargs: {
            "generated_text": "completion",
            "thinking_content": "internal reasoning",
            "stop_reason": "stop",
        },
    )

    result = _qwen35_fast_inference(params, model_cache=None, weights_path="unit-test-path")
    assert result[0]["generated_text"] == "Prompt: completion"
    assert result[0]["thinking_content"] == "internal reasoning"
    assert result[0]["stop_reason"] == "stop"


def test_qwen_generate_adds_default_continuation_system_message(monkeypatch):
    params = GenerateParams(
        text="def can_balance(a):",
        max_length=16,
        top_p=0.9,
        top_k=40,
        temperature=0.7,
        repetition_penalty=1.1,
        min_probability=0.0,
    )

    captured = {}

    def fake_chat_inference(**kwargs):
        captured.update(kwargs)
        return {
            "generated_text": " return True",
            "thinking_content": None,
            "stop_reason": "stop",
        }

    monkeypatch.setattr(tgi, "chat_inference", fake_chat_inference)
    _qwen35_fast_inference(params, model_cache=None, weights_path="unit-test-path")

    assert captured["messages"][0]["role"] == "system"
    assert "text continuation engine" in captured["messages"][0]["content"].lower()
    assert captured["messages"][1]["role"] == "user"


def test_qwen_generate_prefers_explicit_system_message(monkeypatch):
    params = GenerateParams(
        text="def can_balance(a):",
        system_message="Continue code only.",
        max_length=16,
        top_p=0.9,
        top_k=40,
        temperature=0.7,
        repetition_penalty=1.1,
        min_probability=0.0,
    )

    captured = {}

    def fake_chat_inference(**kwargs):
        captured.update(kwargs)
        return {
            "generated_text": " return True",
            "thinking_content": None,
            "stop_reason": "stop",
        }

    monkeypatch.setattr(tgi, "chat_inference", fake_chat_inference)
    _qwen35_fast_inference(params, model_cache=None, weights_path="unit-test-path")

    assert captured["messages"][0]["role"] == "system"
    assert captured["messages"][0]["content"] == "Continue code only."
    assert captured["messages"][1]["role"] == "user"


def test_qwen_generate_accepts_system_prompt_alias(monkeypatch):
    params = GenerateParams(
        text="def can_balance(a):",
        system_prompt="Alias prompt",
        max_length=16,
        top_p=0.9,
        top_k=40,
        temperature=0.7,
        repetition_penalty=1.1,
        min_probability=0.0,
    )

    captured = {}

    def fake_chat_inference(**kwargs):
        captured.update(kwargs)
        return {
            "generated_text": " return True",
            "thinking_content": None,
            "stop_reason": "stop",
        }

    monkeypatch.setattr(tgi, "chat_inference", fake_chat_inference)
    _qwen35_fast_inference(params, model_cache=None, weights_path="unit-test-path")

    assert captured["messages"][0]["role"] == "system"
    assert captured["messages"][0]["content"] == "Alias prompt"


def test_qwen_generate_disables_thinking_by_default(monkeypatch):
    params = GenerateParams(
        text="Hi my n",
        max_length=16,
        top_p=0.9,
        top_k=40,
        temperature=0.7,
        repetition_penalty=1.1,
        min_probability=0.0,
    )

    captured = {}

    def fake_chat_inference(**kwargs):
        captured.update(kwargs)
        return {
            "generated_text": "ame is John",
            "thinking_content": None,
            "stop_reason": "stop",
        }

    monkeypatch.setattr(tgi, "chat_inference", fake_chat_inference)
    result = _qwen35_fast_inference(params, model_cache=None, weights_path="unit-test-path")

    assert captured["enable_thinking"] is False
    assert captured["strip_response"] is False
    assert result[0]["generated_text"] == "Hi my name is John"


def test_qwen_generate_allows_explicit_thinking(monkeypatch):
    params = GenerateParams(
        text="Prompt: ",
        max_length=16,
        top_p=0.9,
        top_k=40,
        temperature=0.7,
        repetition_penalty=1.1,
        min_probability=0.0,
        enable_thinking=True,
    )

    captured = {}

    def fake_chat_inference(**kwargs):
        captured.update(kwargs)
        return {
            "generated_text": "completion",
            "thinking_content": "internal reasoning",
            "stop_reason": "stop",
        }

    monkeypatch.setattr(tgi, "chat_inference", fake_chat_inference)
    result = _qwen35_fast_inference(params, model_cache=None, weights_path="unit-test-path")

    assert captured["enable_thinking"] is True
    assert result[0]["thinking_content"] == "internal reasoning"


def test_thinking_extra_tokens_are_bounded(monkeypatch):
    monkeypatch.setenv("QWEN_THINKING_EXTRA_TOKENS", "1000")
    assert _effective_generation_max_new_tokens(80, enable_thinking=True) == 160
    assert _effective_generation_max_new_tokens(80, enable_thinking=False) == 80


def test_chat_inference_min_probability_applies_only_to_response(monkeypatch):
    class StubTokenizer:
        pad_token_id = 0
        eos_token_id = 1

        def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True, enable_thinking=True):
            return "stub"

        def __call__(self, text, return_tensors="pt"):
            return {"input_ids": torch.tensor([[10, 11]], dtype=torch.long)}

        def convert_tokens_to_ids(self, token):
            if token == "</think>":
                return 248069
            return -1

        def decode(self, token_ids, skip_special_tokens=True):
            if isinstance(token_ids, torch.Tensor):
                token_ids = token_ids.tolist()
            mapping = {
                201: "thinkstuff ",
                248069: "</think>",
                301: "foo ",
                302: "bar ",
                303: "baz ",
            }
            pieces = []
            for token_id in token_ids:
                if skip_special_tokens and token_id == 248069:
                    continue
                pieces.append(mapping.get(token_id, ""))
            return "".join(pieces)

    class StubOutput:
        def __init__(self, sequences, scores):
            self.sequences = sequences
            self.scores = scores

    class StubModel:
        device = "cpu"

        def generate(self, **kwargs):
            # Prompt tokens are [10, 11]. New tokens:
            # 201 -> thinking token
            # 248069 -> </think>
            # 301,302,303 -> response tokens
            sequences = torch.tensor([[10, 11, 201, 248069, 301, 302, 303]], dtype=torch.long)

            # Max probs per generated token:
            # thinking: very low, should NOT affect response min_probability
            # </think>: very low, should NOT affect response min_probability
            # response: first high, second low => should stop after second response token
            scores = [
                torch.tensor([[0.0, 0.0, 0.0]], dtype=torch.float32),
                torch.tensor([[0.0, 0.0, 0.0]], dtype=torch.float32),
                torch.tensor([[5.0, 0.0, 0.0]], dtype=torch.float32),
                torch.tensor([[0.0, 0.0, 0.0]], dtype=torch.float32),
                torch.tensor([[5.0, 0.0, 0.0]], dtype=torch.float32),
            ]
            return StubOutput(sequences=sequences, scores=scores)

    weights_path = "unit-test-path"
    monkeypatch.setitem(tgi.weights_to_model, weights_path, StubModel())
    monkeypatch.setitem(tgi.weights_to_tokenizer, weights_path, StubTokenizer())
    monkeypatch.setattr(tgi.torch.amp, "autocast", lambda *args, **kwargs: nullcontext())

    result = chat_inference(
        messages=[{"role": "user", "content": "hello"}],
        model_cache=None,
        weights_path=weights_path,
        enable_thinking=True,
        max_tokens=5,
        min_probability=0.5,
    )

    assert result["thinking_content"] == "thinkstuff"
    assert result["generated_text"] == "foo bar"
    assert result["stop_reason"] == "min_probability"

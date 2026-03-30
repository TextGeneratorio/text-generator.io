"""
Tests for Qwen3.5 text continuation spacing / subword-splitting logic.

Key design:
- chat_inference is called with strip_response=False so the model's leading
  whitespace is preserved.  The model's tokeniser encodes word-boundary info:
    "Maybe we" → next token is ' could'  (space-prefixed → new word)
    "Hi my n"  → next token is 'ame'     (no space       → completing subword)
- _qwen35_fast_inference does a plain concatenation; no extra space logic needed.
- _needs_space is kept as a utility for other callers.
"""

from unittest.mock import call, patch

import pytest

from questions.text_generator_inference import _needs_space, _qwen35_fast_inference
from questions.models import GenerateParams


# ---------------------------------------------------------------------------
# Unit tests for _needs_space helper (still used by other callers)
# ---------------------------------------------------------------------------

class TestNeedsSpace:
    def test_word_ending_plus_word_continuation(self):
        assert _needs_space("Maybe we", "could chat") is True

    def test_space_at_end_of_input(self):
        assert _needs_space("Maybe we ", "could chat") is False

    def test_continuation_starts_with_space(self):
        assert _needs_space("Maybe we", " could chat") is False

    def test_continuation_is_punctuation(self):
        assert _needs_space("Hello", ".") is False
        assert _needs_space("Hello", "?") is False
        assert _needs_space("Hello", "!") is False
        assert _needs_space("Hello", ",") is False
        assert _needs_space("Hello", ";") is False
        assert _needs_space("Hello", ":") is False

    def test_input_ends_with_newline(self):
        assert _needs_space("Hello\n", "World") is False

    def test_empty_inputs(self):
        assert _needs_space("", "World") is False
        assert _needs_space("Hello", "") is False

    def test_period_before_word(self):
        assert _needs_space("End of sentence.", "Next sentence") is True


# ---------------------------------------------------------------------------
# Integration-level tests for _qwen35_fast_inference
#
# The model's raw output (strip_response=False) encodes word boundaries:
#   ' could' (leading space) → new word after "Maybe we"
#   'ame'    (no space)      → subword completion after "Hi my n"
# ---------------------------------------------------------------------------

def _make_params(text, max_length=10):
    return GenerateParams(
        text=text,
        max_length=max_length,
        number_of_results=1,
        temperature=1.0,
        top_p=0.9,
        top_k=40,
        repetition_penalty=1.0,
        min_probability=0,
        stop_sequences=[],
    )


def _mock_result(text):
    return {"generated_text": text, "thinking_content": None, "stop_reason": "max_length"}


@patch("questions.text_generator_inference.chat_inference", return_value=_mock_result(" could chat"))
def test_word_boundary_space_via_model_token(mock_ci):
    """
    "Maybe we" + model-token ' could chat' (leading space) → "Maybe we could chat".
    The model's leading space is the signal; no heuristic needed.
    """
    params = _make_params("Hi i'm bored so looking for something to do? Maybe we")
    results = _qwen35_fast_inference(params, model_cache=None, weights_path="models/Qwen3.5-4B")
    generated = results[0]["generated_text"]
    assert "we could chat" in generated, f"Expected 'we could chat', got: {repr(generated)}"
    assert "wecould" not in generated


@patch("questions.text_generator_inference.chat_inference", return_value=_mock_result("ame is John"))
def test_subword_continuation_no_space(mock_ci):
    """
    "Hi my n" + model-token 'ame is John' (no leading space) → "Hi my name is John".
    Subword completion: direct concat, no space inserted.
    """
    params = _make_params("Hi my n")
    results = _qwen35_fast_inference(params, model_cache=None, weights_path="models/Qwen3.5-4B")
    generated = results[0]["generated_text"]
    assert "Hi my name is John" in generated, f"Expected 'Hi my name is John', got: {repr(generated)}"
    assert "Hi my n ame" not in generated, f"Spurious space inserted: {repr(generated)}"


@patch("questions.text_generator_inference.chat_inference", return_value=_mock_result(" name is John"))
def test_subword_model_outputs_full_word_with_space(mock_ci):
    """
    Edge case: model outputs ' name is John' (full word with space) for "Hi my n".
    The space is preserved; result is "Hi my n name is John" — model chose to restart the word.
    We don't second-guess this; direct concat is still correct given the model's output.
    """
    params = _make_params("Hi my n")
    results = _qwen35_fast_inference(params, model_cache=None, weights_path="models/Qwen3.5-4B")
    generated = results[0]["generated_text"]
    # Whatever the model chose, we concatenate directly — no double-space
    assert "Hi my n  " not in generated, f"Double space: {repr(generated)}"


@patch("questions.text_generator_inference.chat_inference", return_value=_mock_result("."))
def test_no_space_before_punctuation_raw(mock_ci):
    """Model outputs '.' (punctuation) → no space prepended regardless."""
    params = _make_params("Hello")
    results = _qwen35_fast_inference(params, model_cache=None, weights_path="models/Qwen3.5-4B")
    generated = results[0]["generated_text"]
    assert "Hello." in generated
    assert "Hello ." not in generated


@patch("questions.text_generator_inference.chat_inference")
def test_strip_response_false_is_passed_to_chat_inference(mock_ci):
    """_qwen35_fast_inference must call chat_inference with strip_response=False."""
    mock_ci.return_value = _mock_result(" world")
    params = _make_params("Hello")
    _qwen35_fast_inference(params, model_cache=None, weights_path="models/Qwen3.5-4B")
    _, kwargs = mock_ci.call_args
    assert kwargs.get("strip_response") is False, (
        "chat_inference must be called with strip_response=False so the model's "
        "leading whitespace is preserved for word-boundary detection"
    )


@patch(
    "questions.text_generator_inference.chat_inference",
    return_value={"generated_text": "Hi my n could chat", "thinking_content": None, "stop_reason": "stop"},
)
def test_no_duplication_when_response_starts_with_prompt(mock_ci):
    """If model echoes the full prompt, it should not be duplicated."""
    prompt = "Hi my n"
    mock_ci.return_value = _mock_result(f"{prompt} could chat")
    params = _make_params(prompt)
    results = _qwen35_fast_inference(params, model_cache=None, weights_path="models/Qwen3.5-4B")
    generated = results[0]["generated_text"]
    assert generated.count("Hi my n") == 1, f"Prompt duplicated: {repr(generated)}"

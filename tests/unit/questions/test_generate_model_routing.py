from questions import text_generator_inference
from questions.constants import weights_path_tgz
from questions.models import GenerateParams


class RecordingModelCache:
    most_recent_name = None

    def __init__(self):
        self.loaded_names = []

    def add_or_get(self, model_name, add_model_func):
        self.loaded_names.append(model_name)
        return object()


def test_cold_best_generate_uses_available_text_model(monkeypatch):
    cache = RecordingModelCache()
    params = GenerateParams(
        text="Hi im bored so looking",
        max_length=20,
        max_sentences=1,
        min_probability=0.7,
        model="best",
        enable_thinking=False,
    )

    monkeypatch.setitem(text_generator_inference._is_qwen35_model, weights_path_tgz, True)
    monkeypatch.setattr(
        text_generator_inference,
        "_qwen35_fast_inference",
        lambda generate_params, model_cache, weights_path: [{"generated_text": generate_params.text + " ok"}],
    )

    result = text_generator_inference.fast_inference(params, cache)

    assert cache.loaded_names == ["chat_model"]
    assert result == [{"generated_text": "Hi im bored so looking ok"}]

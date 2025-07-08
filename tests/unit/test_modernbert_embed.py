import importlib
import sys
import types
import pytest

pytest.skip("torch not available in this environment", allow_module_level=True)

class DummyCache:
    def __init__(self):
        self.model = None
    def add_or_get(self, name, fn):
        if self.model is None:
            self.model = fn()
        return self.model

def _fake_model(*args, **kwargs):
    class DummyModel(torch.nn.Module):
        config = types.SimpleNamespace(hidden_size=8)
        def forward(self, input_ids, attention_mask, return_dict=True):
            batch = input_ids.size(0)
            return types.SimpleNamespace(last_hidden_state=torch.zeros((batch, 1, 8)))
    return DummyModel()

class FakeTokens(dict):
    def to(self, device):
        return self


def _fake_tokenizer(text, truncation=None, return_tensors=None, return_attention_mask=None, padding=None):
    return FakeTokens({"input_ids": torch.tensor([[1]]), "attention_mask": torch.tensor([[1]])})

def test_get_modernbert_uses_checkpoint(monkeypatch):
    calls = {}
    monkeypatch.setattr("transformers.AutoModel.from_pretrained", lambda cp: (_fake_model(), calls.setdefault("cp", cp))[0])
    monkeypatch.setattr("transformers.AutoTokenizer.from_pretrained", lambda cp: _fake_tokenizer)
    bert_embed = importlib.reload(sys.modules.get("questions.bert_embed")) if "questions.bert_embed" in sys.modules else importlib.import_module("questions.bert_embed")
    bert_embed.modernbert = None
    model = bert_embed.get_modernbert()
    assert calls["cp"] == bert_embed.checkpoint
    assert model is bert_embed.modernbert


def test_get_bert_embeddings_fast(monkeypatch):
    monkeypatch.setattr("transformers.AutoModel.from_pretrained", lambda cp: _fake_model())
    monkeypatch.setattr("transformers.AutoTokenizer.from_pretrained", lambda cp: _fake_tokenizer)
    bert_embed = importlib.reload(sys.modules.get("questions.bert_embed")) if "questions.bert_embed" in sys.modules else importlib.import_module("questions.bert_embed")
    bert_embed.modernbert = None
    result = bert_embed.get_bert_embeddings_fast(["hello"], DummyCache())
    assert isinstance(result, list) and isinstance(result[0], list)

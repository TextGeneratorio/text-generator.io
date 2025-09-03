from unittest import mock

from scripts import example_smollm3


def test_example_smollm3(monkeypatch):
    fake_tokenizer = mock.MagicMock()
    fake_model = mock.MagicMock()
    fake_tokenizer.apply_chat_template.return_value = "prompt"
    fake_inputs = mock.MagicMock()
    fake_inputs.to.return_value = {"input_ids": [[0, 1]]}
    fake_tokenizer.__call__ = mock.MagicMock(return_value=fake_inputs)
    fake_model.generate.return_value = [[0, 1, 2]]
    fake_model.to.return_value = fake_model

    monkeypatch.setattr(
        example_smollm3, "AutoTokenizer", mock.MagicMock(from_pretrained=mock.MagicMock(return_value=fake_tokenizer))
    )
    monkeypatch.setattr(
        example_smollm3, "AutoModelForCausalLM", mock.MagicMock(from_pretrained=mock.MagicMock(return_value=fake_model))
    )

    example_smollm3.main()
    fake_model.generate.assert_called_once()

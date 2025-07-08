from unittest import mock

import pytest
pytest.skip("requires local models", allow_module_level=True)
server = None


def test_load_audio_model(monkeypatch):
    fake_model = mock.MagicMock()
    monkeypatch.setattr(
        server.nemo_asr.models.ASRModel,
        "from_pretrained",
        mock.MagicMock(return_value=fake_model),
    )
    server.audio_model = None
    model = server.load_audio_model()
    assert model is fake_model
    server.nemo_asr.models.ASRModel.from_pretrained.assert_called_once_with(
        model_name="nvidia/parakeet-tdt-0.6b-v2"
    )
    fake_model.to.assert_called()

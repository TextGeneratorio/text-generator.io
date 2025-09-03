import pytest

pytestmark = [pytest.mark.inference, pytest.mark.audio]


@pytest.mark.skipif(True, reason="Audio model tests require inference dependencies")
def test_load_audio_model():
    """Test audio model loading functionality (skipped by default)"""
    pass

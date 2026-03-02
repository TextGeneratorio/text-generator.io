from questions.models import GenerateSpeechParams


def test_generate_speech_params_maps_legacy_speaker():
    params = GenerateSpeechParams(text="hello", speaker="Male fast")
    assert params.voice == "am_adam"


def test_generate_speech_params_voice_overrides_legacy_speaker():
    params = GenerateSpeechParams(text="hello", speaker="Male fast", voice="af_nicole")
    assert params.voice == "af_nicole"

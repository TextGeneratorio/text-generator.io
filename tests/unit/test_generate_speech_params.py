from questions.models import GenerateSpeechParams


def test_generate_speech_params_maps_legacy_speaker():
    params = GenerateSpeechParams(text="hello", speaker="Male fast")
    assert params.voice == "am_adam"


def test_generate_speech_params_maps_distinct_legacy_speakers():
    expected = {
        "Male fast": "am_adam",
        "Male default": "am_michael",
        "Male slower": "bm_lewis",
        "Female 1": "af_bella",
        "Female 2": "af_sarah",
        "BDL (male)": "am_adam",
        "KSP (male)": "am_michael",
        "RMS (male)": "bm_lewis",
        "CLB (female)": "af_bella",
        "SLT (female)": "af_sarah",
    }

    for speaker, voice in expected.items():
        assert GenerateSpeechParams(text="hello", speaker=speaker).voice == voice


def test_generate_speech_params_voice_overrides_legacy_speaker():
    params = GenerateSpeechParams(text="hello", speaker="Male fast", voice="af_nicole")
    assert params.voice == "af_nicole"


def test_generate_speech_params_supertonic_defaults():
    params = GenerateSpeechParams(text="hello", voice="M1")
    assert params.voice == "M1"
    assert params.language == "en"
    assert params.steps == 4
    assert params.speed == 1.0

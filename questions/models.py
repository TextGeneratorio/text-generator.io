from time import time
from typing import Optional, List

from fastapi import UploadFile
from pydantic import BaseModel

from questions.utils import random_string


class CustomBaseModel(BaseModel):
    def dict(self, **kwargs):
        hidden_fields = set(
            attribute_name
            for attribute_name, model_field in self.__fields__.items()
            if model_field.field_info.extra.get("hidden") is True
        )
        kwargs.setdefault("exclude", hidden_fields)
        return super().dict(**kwargs)


class AudioParams(BaseModel):
    audio_url: Optional[str]
    translate_to_english: bool = False
    """Whether to translate the audio to english during processing it"""

    output_filetype: str = "txt"
    """The output filetype of the audio file, either txt or srt for a subtitles file importable into youtube"""

class AudioParamsOrAudioFile(AudioParams):
    audio_file: Optional[UploadFile]


class SpeechSegment(BaseModel):
    id: int
    seek: float
    start: float
    end: float
    text: str
    temperature: float
    avg_logprob: float
    compression_ratio: float
    no_speech_prob: float
class AudioReturn(BaseModel):
    text: str
    segments: List[SpeechSegment]
    language: str

class GenerateParams(BaseModel):
    text: str
    number_of_results: int = 1

    # stopping criteria

    max_length: Optional[int] = 100
    min_length: Optional[int] = 1
    max_sentences: Optional[int] = None
    min_probability: Optional[float] = 0.0
    stop_sequences: Optional[List[str]] = []

    # advanced params
    top_p: Optional[float] = 0.9
    top_k: Optional[int] = 40
    temperature: Optional[float] = 0.7
    seed: Optional[int] = None
    repetition_penalty: Optional[float] = 1.2

    model: Optional[str] = None

class GenerateSpeechParams(BaseModel):
    text: str
    voice: str = "af"  # Default voice (50-50 mix of Bella & Sarah)
    language: str = "en-us"  # Default to US English
    speed: float = 1.0
    volume: float = 1.0
    sample_rate: int = 24000  # Kokoro outputs 24kHz audio


class OpenaiParams(BaseModel):
    prompt: str
    n: int = 1
    best_of: int = 1  # unused
    echo: bool = False

    # stopping criteria

    max_tokens: Optional[int] = 100
    min_length: Optional[int] = 1
    # used by us only
    max_sentences: Optional[int] = None
    min_probability: Optional[float] = 0.0
    # seed: Optional[int] = None

    stop: Optional[List[str]] = []

    stream: bool = False  # unused
    suffix: str = False # unused

    # advanced params
    top_p: Optional[float] = 0.9
    top_k: Optional[int] = 40
    temperature: Optional[float] = 0.7
    repetition_penalty: Optional[float]  = 1.2

    frequency_penalty: Optional[float]  = 1.2  # unused
    presense_penalty: Optional[float]  = 1.2  # unused


def map_to_generate_params(openai_params: OpenaiParams) -> GenerateParams:
    generate_params = create_generate_params(
        openai_params.prompt,
        openai_params.n,
        openai_params.max_tokens,
        openai_params.min_length,
        openai_params.max_sentences,
        openai_params.min_probability,
        openai_params.stop,
        openai_params.top_p,
        openai_params.top_k,
        openai_params.temperature,
    )
    return generate_params


def map_to_openai_response(results, generate_params: GenerateParams):
    """
        takes a result with the following structure:
        [{
            'generated_text': '...',
            'stop_reason': 'min_prob',
        }]
        and returns a response with the following structure:
    {
      "id": "cmpl-5Qp5AcdxucJDiiPWqjlx0oODPa9VV",
      "object": "text_completion",
      "created": 1657074572,
      "model": "text-davinci-001",
      "choices": [
        {
          "text": "\n\"results\": [\n{\n\"title\": \"Hey (meaning hi or hello)\",\n\"text\": \"Hey is a casual way to say hello or hi. It can be used as a standalone word, or as part of a phrase. Hey is an informal term, and should not be used in formal situations.\"\n}\n],\n\"infoUrl\": \"https://www.merriam-webster.com/dictionary/hey\",\n\"imageUrl\": null,\n\"displayTextUrl\": null,",
          "index": 0,
          "logprobs": null,
          "finish_reason": "stop"
        }
      ],
      "usage": {
        "prompt_tokens": 185,
        "completion_tokens": 112,
        "total_tokens": 297
      }
    }"""
    response = {}
    response["id"] = "cmpl-" + random_string(10)
    response["object"] = "text_completion"
    response["created"] = int(time())
    response["model"] = "text-generator"
    response["choices"] = []
    for i, result in enumerate(results):
        response["choices"].append(
            {
                "text": result["generated_text"],
                "index": i,
                "logprobs": None,
                "finish_reason": result["stop_reason"],
            }
        )
    response["usage"] = {"prompt_tokens": 0, "completion_tokens": 1, "total_tokens": 1}
    return response


class FeatureExtractParams(BaseModel):
    text: str
    num_features: Optional[int]

class SummarizationParams(BaseModel):
    text: str
    max_length: Optional[int]


class CreateUserRequest(BaseModel):
    email: str
    # emailVerified: str
    uid: str
    photoURL: Optional[str] = None
    token: str


class GetUserRequest(BaseModel):
    uid: str
    email: str  # todo fix vuln getting user by email


class CreateCheckoutRequest(BaseModel):
    type: Optional[str] = "monthly"  # legacy todo rm me
    subscription_type: Optional[str] = "monthly"
    referral: Optional[str] = ""


def create_generate_params(
    text,
    number_of_results=1,
    max_length=100,
    min_length=1,
    max_sentences=None,
    min_probability=0.0,
    stop_sequences=[],
    top_p=0.9,
    top_k=40,
    temperature=0.7,
    model='best',
):
    params = {}
    params["text"] = text
    params["number_of_results"] = number_of_results
    params["max_length"] = max_length
    params["min_length"] = min_length
    params["max_sentences"] = max_sentences

    params["top_p"] = top_p
    params["top_k"] = top_k
    params["temperature"] = temperature

    params["min_probability"] = min_probability
    params["stop_sequences"] = stop_sequences
    params["seed"] = 42  # for the test suite
    params["model"] = model

    # if not min_probability and early_terminate:
    #     if early_terminate == 'shortest':
    #         params['min_probability'] = 0.993
    #     elif early_terminate == 'medium':
    #         params['min_probability'] = 0.9
    #     elif early_terminate == 'long':
    #         params['min_probability'] = 0.7
    #     elif early_terminate == 'longest':
    #         params['min_probability'] = 0.3
    return GenerateParams(**params)

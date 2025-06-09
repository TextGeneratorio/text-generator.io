#!/usr/bin/env python
import os
import random
from io import BytesIO
from tempfile import NamedTemporaryFile
from typing import Union, List, Iterator

from .tts_utils import srt_format_timestamp, write_srt, synthesize_full_text

import torch
import youtube_dl
from fastapi import BackgroundTasks, UploadFile, File, Form
from fastapi import Request, Header
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging
from questions.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
from starlette.responses import (
    JSONResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
    HTMLResponse,
)

from questions.audio_server.audio_dl import request_get
from questions.constants import weights_path_tgz
from questions.db_models import User
from questions.inference_server.model_cache import ModelCache
from questions.models import (
    GenerateParams,
    FeatureExtractParams,
    OpenaiParams,
    map_to_generate_params,
    map_to_openai_response,
    AudioParams,
    GenerateSpeechParams,
    AudioParamsOrAudioFile,
    SummarizationParams,
)
from questions.payments.payments import (
    get_subscription_item_id_for_user,
    create_subscription_for_user,
    get_subscription_item_id_for_user_email,
)
from questions.perplexity import DEVICE
from questions.summarization import get_extractive_summary
from questions.text_gen_pipeline import TextGenPipeline
from questions.text_generator_inference import (
    load_pipelines_and_model,
    fast_inference,
    fast_feature_extract_inference,
)
from questions.utils import log_time
from sellerinfo import session_secret
from .models import build_model
from .kokoro import generate, generate_full

import librosa

from questions.inference_server.claude_queries import query_to_claude_async

assert TextGenPipeline is not None  # needed to override

# pip install google-api-python-client google-cloud-storage google-auth-httplib2 google-auth-oauthlib

config = {}
config["webapp2_extras.sessions"] = session_secret

templates = Jinja2Templates(directory=".")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

GCLOUD_STATIC_BUCKET_URL = "https://storage.googleapis.com/questions-346919/static"
import sellerinfo
import stripe

app = FastAPI(
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    title="Generate Text API",
    description="Generate text, control stopping criteria like max_length/max_sentences",
    version="1",
)

import whisper
import numpy as np

MODEL_CACHE = ModelCache()

# @app.post("/files/")
# async def create_files(files: bytes = File()):
#     return {"file_sizes": [len(file) for file in files]}

languages = {
    "af_za": "Afrikaans",
    "am_et": "Amharic",
    "ar_eg": "Arabic",
    "as_in": "Assamese",
    "az_az": "Azerbaijani",
    "be_by": "Belarusian",
    "bg_bg": "Bulgarian",
    "bn_in": "Bengali",
    "bs_ba": "Bosnian",
    "ca_es": "Catalan",
    "cmn_hans_cn": "Chinese",
    "cs_cz": "Czech",
    "cy_gb": "Welsh",
    "da_dk": "Danish",
    "de_de": "German",
    "el_gr": "Greek",
    "en_us": "English",
    "es_419": "Spanish",
    "et_ee": "Estonian",
    "fa_ir": "Persian",
    "fi_fi": "Finnish",
    "fil_ph": "Tagalog",
    "fr_fr": "French",
    "gl_es": "Galician",
    "gu_in": "Gujarati",
    "ha_ng": "Hausa",
    "he_il": "Hebrew",
    "hi_in": "Hindi",
    "hr_hr": "Croatian",
    "hu_hu": "Hungarian",
    "hy_am": "Armenian",
    "id_id": "Indonesian",
    "is_is": "Icelandic",
    "it_it": "Italian",
    "ja_jp": "Japanese",
    "jv_id": "Javanese",
    "ka_ge": "Georgian",
    "kk_kz": "Kazakh",
    "km_kh": "Khmer",
    "kn_in": "Kannada",
    "ko_kr": "Korean",
    "lb_lu": "Luxembourgish",
    "ln_cd": "Lingala",
    "lo_la": "Lao",
    "lt_lt": "Lithuanian",
    "lv_lv": "Latvian",
    "mi_nz": "Maori",
    "mk_mk": "Macedonian",
    "ml_in": "Malayalam",
    "mn_mn": "Mongolian",
    "mr_in": "Marathi",
    "ms_my": "Malay",
    "mt_mt": "Maltese",
    "my_mm": "Myanmar",
    "nb_no": "Norwegian",
    "ne_np": "Nepali",
    "nl_nl": "Dutch",
    "oc_fr": "Occitan",
    "pa_in": "Punjabi",
    "pl_pl": "Polish",
    "ps_af": "Pashto",
    "pt_br": "Portuguese",
    "ro_ro": "Romanian",
    "ru_ru": "Russian",
    "sd_in": "Sindhi",
    "sk_sk": "Slovak",
    "sl_si": "Slovenian",
    "sn_zw": "Shona",
    "so_so": "Somali",
    "sr_rs": "Serbian",
    "sv_se": "Swedish",
    "sw_ke": "Swahili",
    "ta_in": "Tamil",
    "te_in": "Telugu",
    "tg_tj": "Tajik",
    "th_th": "Thai",
    "tr_tr": "Turkish",
    "uk_ua": "Ukrainian",
    "ur_pk": "Urdu",
    "uz_uz": "Uzbek",
    "vi_vn": "Vietnamese",
    "yo_ng": "Yoruba",
}

# expose best of?
options = {}  # dict(beam_size=5, best_of=5) (makes it slower)
transcribe_options = dict(task="transcribe", **options)
translate_options = dict(task="translate", **options)

# %%
references = []
transcriptions = []
translations = []

# for audio, text in tqdm(dataset):
#     transcription = audio_model.transcribe(audio, **transcribe_options)["text"]
#     translation = audio_model.transcribe(audio, **translate_options)["text"]
# result = audio_model.transcribe("/media/lee/78ca132e-d181-4406-aea5-3c9665f486cc/Videos/intro-bitbanknz.mp3") 40/6s

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# download gpt neo model and load it into memory

# DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# DEVICE = "cpu"

# storage_client = storage.Client.from_service_account_json('/google-cloud/keyfile/service_account.json')


# def download_model(model_path):
# # download gpt neo model and load it into memory
# # download from gs://20-questions/gpt-neo-model.tar.gz
# # download artefact to disk
# bucket_name = "20-questions"
# bucket=storage_client.get_bucket(bucket_name)
# gsutil.download_file_to_file(model_path, "gpt-neo-model.tar.gz")
# pass

session_dict = {}

# weights_path = "models/gpt-neo-1.3B-halfed/"

# weights_path = "models/tg-2b5/"
# weights_path = "models/tg-6b3/"


# weights_path = "models/gpt-tiny/" # default to 'distilgpt2'


debug = os.environ.get("SERVER_SOFTWARE", "").startswith("Development")

is_app_engine = os.environ.get("IS_APP_ENGINE", False)
# if not is_app_engine:
#     def initial_load():
#         model = MODEL_CACHE.add_or_get("text_model", load_pipelines_and_model)
#     daemon = Thread(target=initial_load, args=(), name="Background")
#     # # # download in background thread so that the server can start faster.
#     daemon.start()


# def ensure_pipelines_loaded():
# if questions.text_generator_inference.loading:
#     return daemon.join()


# takes too long to start if so.
# if not debug:
#     load_pipelines_and_model()


if debug:
    stripe_keys = {
        "secret_key": sellerinfo.STRIPE_TEST_SECRET,
        "publishable_key": sellerinfo.STRIPE_TEST_KEY,
    }
    GCLOUD_STATIC_BUCKET_URL = ""
else:
    stripe_keys = {
        "secret_key": sellerinfo.STRIPE_LIVE_SECRET,
        "publishable_key": sellerinfo.STRIPE_LIVE_KEY,
    }

stripe.api_key = stripe_keys["secret_key"]

API_KEY = os.getenv("API_KEY", None)


# if API_KEY:
#     # get user for secret API key
#     get_user_for_api_key = User.bySecret(API_KEY)
#     # get stripe subscription for user
#     get_subscription_for_api_key = get_self_hosted_subscription_item_id_for_user(get_user_for_api_key.stripe_id)
#     if get_subscription_for_api_key:
#         logger.info("API key is valid")
#     else:
#         logger.info(f"API key is invalid, self hosted subscription not found for user {get_user_for_api_key.email}")
#         logger.info(f"Please contact support at lee.penkman@wordsmashing.com")
#         sys.exit(1)
# todo per seat


def set_session_for_user(user):
    session_dict[user.secret] = user


def track_stripe_request_usage(secret, quantity: int):
    # track a request being used in stripe
    # get the current users stripe subscription
    # todo fix this collection for when running multiple instances (lock?)
    existing_user = session_dict.get(secret)
    db_user = None
    if existing_user:
        existing_user.charges_monthly += int(quantity * 10)
        User.save(existing_user)
    if not existing_user:
        db_user = User.bySecret(secret)
        if not db_user:
            logger.error(f"user not found for secret: {secret}")
            return
        db_user.charges_monthly += int(quantity * 10)
        User.save(db_user)
        set_session_for_user(db_user)

    existing_user = existing_user or db_user

    subscription_item_id = get_subscription_item_id_for_user_email(existing_user.email)
    if not subscription_item_id:
        logger.info(
            f"no subscription item id for user: {existing_user.email} {existing_user.stripe_id}"
        )
        # Create a new subscription item
        subscription = create_subscription_for_user(existing_user.stripe_id)
        logger.info(f"created subscription: {subscription}")
        try:
            subscription_item_id = subscription["items"].data[0]["id"]
        except Exception as e:
            logger.error(e)
            logger.error(subscription)
    # TODO batching
    # todo block if none
    stripe.SubscriptionItem.create_usage_record(
        subscription_item_id,
        quantity=quantity,
        # timestamp=int(time.time()),
    )


def validate_generate_params(generate_params):
    validate_result = ""
    if generate_params.text == "":
        validate_result = "Please enter some text"
    return validate_result


audio_model = None


def load_audio_model():
    global audio_model
    # about 10s
    with log_time("load whisper model"):
        # audio_model = whisper.load_model("large") # todo specify download_root to a fast ssd
        if not audio_model:
            audio_model = whisper.load_model(
                "medium", download_root="models"
            )  # todo specify download_root to a fast ssd
            audio_model.eval()
        audio_model = audio_model.to("cuda")
        logger.info(
            f"Model is {'multilingual' if audio_model.is_multilingual else 'English-only'} "
            f"and has {sum(np.prod(p.shape) for p in audio_model.parameters()):,} parameters."
            f"and is on {audio_model.device}"
        )
        return audio_model


def fast_audio_extract_inference(audio_params: AudioParamsOrAudioFile):
    audio_model = MODEL_CACHE.add_or_get("audio_model", load_audio_model)
    if audio_params.audio_url is None:
        audio_file = audio_params.audio_file
        audio_bytes = audio_file.file.read()
    elif "youtube.com" in audio_params.audio_url:
        # todo hopefully people never use this slow/secret route
        # todo soundcloud /spotify etc>?
        # todo download youtube video

        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                    "preferredquality": "192",
                }
            ],
            "postprocessor_args": ["-ar", "16000"],
            "prefer_ffmpeg": True,
            "keepvideo": False,
            # download to temp file
            "outtmpl": "/tmp/audio.wav",
            # download to memory
        }
        with log_time("download youtube"):
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download(
                    [audio_params.audio_url],
                )
                audio_bytes = ydl.prepare_filename(
                    ydl.extract_info(audio_params.audio_url)
                )
                with open(audio_bytes, "rb") as f:
                    audio_bytes = f.read()
    else:
        with log_time("download audio"):
            audio_request = request_get(audio_params.audio_url)
            response = audio_request.result()
            if response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to download audio file at {audio_params.audio_url}",
                )
            response.raw.decode_content = True
            audio_bytes = response.content

    with torch.inference_mode():
        opts = transcribe_options  # dict(beam_size=5, best_of=5)
        if audio_params.translate_to_english:
            opts = translate_options
        # write to /dev/shm ... assume mp3
        tmp_file = NamedTemporaryFile(dir="/dev/shm", delete=True, suffix=".mp3")
        tmp_file.write(audio_bytes)
        result = audio_model.transcribe(tmp_file.name, **opts)

        # clean data
        tmp_file.close()
        for segment in result["segments"]:
            del segment["tokens"]
        result["text"] = result["text"].strip()
        return result



@app.post("/api/v1/audio-file-extraction")
async def audio_file_extraction(
    background_tasks: BackgroundTasks,
    request: Request,
    response: Response,
    # files: List[UploadFile] = File(...),
    # files: list[bytes] = File(None, description="Multiple files as bytes"),
    audio_file: UploadFile = File(None, description="Audio file"),
    translate_to_english: bool = Form(False),
    output_filetype: str = Form("txt"),
    secret: Union[str, None] = Header(default=None),
):
    audio_params = AudioParamsOrAudioFile(
        audio_file=audio_file,
        audio_url=None,
        translate_to_english=translate_to_english,
        output_filetype=output_filetype,
    )
    return await audio_extract_shared(
        background_tasks, audio_params, request, response, secret
    )


@app.post("/api/v1/audio-extraction")
async def audio_extraction(
    feature_extract_params: AudioParams,  # wav files or mp3 supported
    # audio_file: UploadFile,
    background_tasks: BackgroundTasks,
    request: Request,
    response: Response,
    secret: Union[str, None] = Header(default=None),
):
    # if not request_authorized(request, secret):
    #     return HTTPException(
    #         status_code=401, detail="Please subscribe at https://text-generator.io/subscribe first"
    #     )
    return await audio_extract_shared(
        background_tasks, feature_extract_params, request, response, secret
    )


# @app.get("/restart-server")
# async def restart_server():
#     # os.system("sudo systemctl restart text-generator")
#     # restart gunicorn with sighup
#     os.system("kill -SIGHUP `pgrep gunicorn`")
#     return "restarting server"


async def audio_extract_shared(
    background_tasks, feature_extract_params, request, response, secret
):
    # if not request_authorized(request, secret):
    #     return HTTPException(
    #         status_code=401,
    #         detail="Please subscribe at https://text-generator.io/subscribe first, also make sure there is an up to date credit card saved in your account"
    #     )
    inference_result = fast_audio_extract_inference(feature_extract_params)
    if "X-Rapid-API-Key" not in request.headers:
        # todo fix
        seconds_taken = inference_result["segments"][-1]["end"]
        # price of quantity is 1 for .01
        price = seconds_taken * 0.00005
        quantity = price // 0.01
        remainder = price % 0.01
        if random.random() < remainder * 100:
            quantity += 1
        if quantity:
            if (
                not API_KEY and secret != sellerinfo.TEXT_GENERATOR_SECRET
            ):  # skip logging for our secret
                background_tasks.add_task(
                    track_stripe_request_usage, secret=secret, quantity=int(quantity)
                )
    if feature_extract_params.output_filetype == "srt":
        # response = StreamingResponse(
        # non streaming response
        response.headers["Content-Disposition"] = "attachment; filename=audio.srt"
        return write_srt(inference_result["segments"])
    return inference_result


@app.post("/api/v1/feature-extraction")
async def feature_extraction(
    feature_extract_params: FeatureExtractParams,
    background_tasks: BackgroundTasks,
    request: Request,
    secret: Union[str, None] = Header(default=None),
):
    # global daemon
    # slow warmup on new servers
    # model = MODEL_CACHE.add_or_get("text_model", load_pipelines_and_model)
    # daemon.join()
    inference_result = fast_feature_extract_inference(
        feature_extract_params, MODEL_CACHE
    )
    if "X-Rapid-API-Key" not in request.headers:
        # todo fix
        if random.randint(1, 10) == 10:
            if not API_KEY and secret != sellerinfo.TEXT_GENERATOR_SECRET:
                background_tasks.add_task(
                    track_stripe_request_usage, secret=secret, quantity=1
                )
    return inference_result[: feature_extract_params.num_features]


@app.post("/api/v1/summarization")
async def feature_extraction(
    summarization_params: SummarizationParams,
    background_tasks: BackgroundTasks,
    request: Request,
    secret: Union[str, None] = Header(default=None),
):
    # global daemon
    # slow warmup on new servers
    # model = MODEL_CACHE.add_or_get("text_model", load_pipelines_and_model)
    # daemon.join()
    text = get_extractive_summary(summarization_params.text, MODEL_CACHE)
    if "X-Rapid-API-Key" not in request.headers:
        # todo fix
        if random.randint(1, 10) == 10:
            if not API_KEY and secret != sellerinfo.TEXT_GENERATOR_SECRET:
                background_tasks.add_task(
                    track_stripe_request_usage, secret=secret, quantity=1
                )
    return JSONResponse({"generated_text": text})


@app.get("/liveness_check")
async def liveness_check(request: Request):
    # global daemon
    inference_result = fast_inference(
        generate_params=GenerateParams(
            text="hi my friend", min_probability=0.9, max_length=1, model="any"
        ),
        model_cache=MODEL_CACHE,
    )
    return JSONResponse(inference_result)


def user_secret_matches(secret):
    existing_user = session_dict.get(secret)
    db_user = None
    if not existing_user:
        db_user = User.bySecret(secret)
        if not db_user:
            logger.error(f"user not found for secret: {secret}")
            return None
        set_session_for_user(db_user)

    existing_user = existing_user or db_user
    return existing_user


def request_authorized(request: Request, secret):
    if API_KEY:
        if secret == API_KEY:
            return True
        else:
            logger.error("Error invalid api key for request: %s", request.url)
            return False
    # todo fix vuln
    if "X-Rapid-API-Key" in request.headers or "x-rapid-api-key" in request.headers:
        return True
    return user_secret_matches(secret)


import soundfile as sf


speech_processor = None
speechgen_model = None
speech_vocoder = None


def load_speechgen_model():
    global speech_processor
    global speechgen_model
    global speech_vocoder

    if not speechgen_model:
        # Load Kokoro model
        device = "cuda" if torch.cuda.is_available() else "cpu"
        speechgen_model = build_model("models/kokoro-v0_19.pth", device)

        # Load voice packs
        voicepacks = {}
        voice_names = [
            "af",
            "af_bella",
            "af_sarah",
            "am_adam",
            "am_michael",
            "bf_emma",
            "bf_isabella",
            "bm_george",
            "bm_lewis",
            "af_nicole",
            "af_sky",
        ]

        for voice in voice_names:
            voicepacks[voice] = torch.load(
                f"models/voices/{voice}.pt", weights_only=True
            ).to(device)

    return speechgen_model, voicepacks


speaker_embeddings = {
    "BDL": "questions/speech/spkemb/cmu_us_bdl_arctic-wav-arctic_a0009.npy",
    "CLB": "questions/speech/spkemb/cmu_us_clb_arctic-wav-arctic_a0144.npy",
    "KSP": "questions/speech/spkemb/cmu_us_ksp_arctic-wav-arctic_b0087.npy",
    "RMS": "questions/speech/spkemb/cmu_us_rms_arctic-wav-arctic_b0353.npy",
    "SLT": "questions/speech/spkemb/cmu_us_slt_arctic-wav-arctic_a0508.npy",
}


def write_wav(processed_np_speech, rate):
    # todo fix to use io.BytesIO
    bytes = BytesIO()
    bytes.name = "audio.wav"
    sf.write(bytes, processed_np_speech, rate, subtype="PCM_24")
    # bytesio to bytes
    return bytes.getvalue()


@app.post("/api/v1/generate_speech")
async def generate_speech(
    generate_speech_params: GenerateSpeechParams,
    background_tasks: BackgroundTasks,
    request: Request,
    response: Response,
    secret: Union[str, None] = Header(default=None),
):
    if not request_authorized(request, secret):
        return HTTPException(
            status_code=401,
            detail="Invalid Secret, please use the secret found in /account also subscribe at https://text-generator.io/subscribe first, also make sure there is an up to date credit card saved in your account",
        )
    text = generate_speech_params.text

    voice = generate_speech_params.voice
    speed = generate_speech_params.speed
    rate, processed_np_speech = audio_process(text, voice, speed)
    # write audio to response file
    response.headers["Content-Disposition"] = "attachment; filename=audio.wav"
    # (16000, speech)
    if "X-Rapid-API-Key" not in request.headers:
        # todo fix
        if not API_KEY and secret != sellerinfo.TEXT_GENERATOR_SECRET:
            background_tasks.add_task(
                track_stripe_request_usage, secret=secret, quantity=1
            )
    # write np array to wav
    wav = write_wav(processed_np_speech, rate)
    file = Response(wav, media_type="audio/wav")
    return file
    # return Response(wav, media_type="audio/wav")


def gradio_audio_process(text, voice, speed=1.0):
    """Simplified function that only takes the required parameters"""
    if len(text.strip()) == 0:
        return (24000, np.zeros(0).astype(np.int16))

    model, voicepacks = MODEL_CACHE.add_or_get("speech_model", load_speechgen_model)

    # Get the voicepack
    voicepack = voicepacks.get(voice, voicepacks["af_nicole"])

    # Generate audio using Kokoro
    # generate_full handles inputs longer than the default token limit
    audio, phonemes = generate_full(model, text, voicepack, lang=voice[0], speed=speed)

    return (24000, audio)


speaker_ui_name_to_code_name = {
    "Male fast": "BDL (male)",
    "Female 1": "CLB (female)",
    "Male default": "KSP (male)",
    "Male slower": "RMS (male)",
    "Female 2": "SLT (female)",
}
speaker_embeddings_loaded = {}


def load_speaker_embedding(speaker):
    speaker_embedding = np.load(speaker_embeddings[speaker[:3]])

    speaker_embedding = torch.tensor(speaker_embedding).unsqueeze(0).to(DEVICE)
    return speaker_embedding


for ui_name, code_name in speaker_ui_name_to_code_name.items():
    speaker_embeddings_loaded[ui_name] = load_speaker_embedding(code_name)


def audio_process(text, voice="af_nicole", speed=1.0):
    model, voicepacks = MODEL_CACHE.add_or_get("speech_model", load_speechgen_model)

    if len(text.strip()) == 0:
        return (24000, np.zeros(0).astype(np.int16))

    # Get the voicepack
    voicepack = voicepacks.get(voice, voicepacks["af_nicole"])

    # Generate audio using Kokoro
    # generate_full handles inputs longer than the default token limit
    audio, phonemes = generate_full(model, text, voicepack, lang=voice[0], speed=speed)

    # we could do this but use speed instead
    # Convert to float32 for time-stretch
    # audio_float = audio.astype(np.float32) / 32767.0
    # # Apply time stretch based on 'speed' param (e.g. 2.0 = 2x faster)
    # # if speed != 1.0:
    # #     audio_float = librosa.effects.time_stretch(audio_float, rate=speed)

    # # Convert back to int16
    # audio_stretched = (audio_float * 32767.0).astype(np.int16)

    return (24000, audio)




# gradio web app at https://text-generator.io/gradio_tts

examples = [
    ["It is not in the stars to hold our destiny but in ourselves.", "Male default"],
    ["Oliver went to the opera in October.", "Female 2"],
    [
        "She sells seashells by the seashore. I saw a kitten eating chicken in the kitchen.",
        "Male slower",
    ],
    [
        "Brisk brave brigadiers brandished broad bright blades, blunderbusses, and bludgeons—balancing them badly.",
        "Female 1",
    ],
    ["A synonym for cinnamon is a cinnamon synonym.", "Male fast"],
    [
        "How much wood would a woodchuck chuck if a woodchuck could chuck wood? He would chuck, he would, as much as he could, and chuck as much wood as a woodchuck would if a woodchuck could chuck wood.",
        "Female 2",
    ],
]
title = "Text To Speech"
description = (
    "<b>How to use:</b> Enter some English text and choose a speaker. Click Submit "
)
article = """
<p>Checkout the API docs at <a target="_blank" href="https://text-generator.io/docs">/docs</a></p>
"""

# def get_token(request: gr.Request):
#     headers = request.kwargs.get("headers") or {}
#     raw_cookie = headers.get("cookie") or ""
#     cookies = dict(i.split("=", 1) for i in raw_cookie.split("; "))
#     return cookies.get("access-token") or cookies.get("access-token-unsecure")

# def get_cookies(request: gr.Request):
#     return request.cookies.get('secret')

# Comment out or remove the old Gradio interface block if not needed:
# audio_app = gr.Interface(
#     fn=gradio_audio_process,
#     inputs=[
#         gr.Text(label="Input Text", value="It was the best of times, it was the worst of times."),
#         gr.Radio(
#             label="Voice",
#             choices=[
#                 "af", "af_bella", "af_sarah",
#                 "am_adam", "am_michael", "bf_emma",
#                 "bf_isabella", "bm_george", "bm_lewis",
#                 "af_nicole", "af_sky"
#             ],
#             value="af"
#         ),
#         gr.Slider(label="Speed", minimum=0.5, maximum=2.0, step=0.1, value=1.0),
#     ],
#     outputs=[
#         gr.Audio(label="Generated Speech", type="numpy"),
#     ],
#     title=title,
#     description=description,
#     article=article,
#     examples=examples,
#     css="""
#     .lg.primary {
#         background-color: rgba(0,188,212,1) !important;
#         background: linear-gradient(177deg, #d79f2a 0%, #d34675 150%) !important;
#         color: #fff !important;
#         outline: none !important;
#         border: none !important;
#     }
#     .lg.primary:hover, .lg.primary:focus {
#         background-color: rgb(241, 125, 52) !important;
#     }
#     """,
#     queue=False
# )
# audio_app = gr.routes.App.create_app(audio_app)
# app.mount("/gradio_tts", audio_app)

########################################
# New custom Gradio Blocks with JS/CSS #
########################################

# audio_custom_blocks = gr.Blocks()

# with audio_custom_blocks:
#     # Minimal HTML/JS example to call our /api/v1/generate_speech endpoint.
#     # The fetch returns a WAV file; we convert to a blob for the audio player.
#     gr.HTML("""
#     <h2>Custom TTS Interface</h2>
#     <textarea id="tts_input" style="width:80%; height:60px;" placeholder="Enter some text here"></textarea>
#     <br/>
#     <label for="voice">Voice:</label>
#     <select id="voice">
#         <option value="af_nicole">af_nicole</option>
#         <option value="af_bella">af_bella</option>
#         <option value="af_sarah">af_sarah</option>
#         <option value="am_adam">am_adam</option>
#         <option value="am_michael">am_michael</option>
#         <option value="bf_emma">bf_emma</option>
#         <option value="bf_isabella">bf_isabella</option>
#         <option value="bm_george">bm_george</option>
#         <option value="bm_lewis">bm_lewis</option>
#         <option value="af_sky">af_sky</option>
#     </select>
#     <br/><br/>
#     <label for="speed">Speed:</label>
#     <input type="range" id="speed" min="0.5" max="2.0" step="0.1" value="1.0" style="width:30%;">
#     <span id="speed_value">1.0</span>
#     <br/>
#     <button id="generate_btn">Generate Speech</button>
#     <br/><br/>
#     <audio id="result_audio" controls></audio>

#     <script>
#     // Dynamically display the speed value
#     const speedSlider = document.getElementById("speed");
#     const speedValueSpan = document.getElementById("speed_value");
#     speedSlider.addEventListener("input", () => {
#       speedValueSpan.textContent = speedSlider.value;
#     });

#     async function generateSpeech() {
#       const text = document.getElementById("tts_input").value;
#       const voice = document.getElementById("voice").value;
#       const speed = document.getElementById("speed").value;

#       if (!text.trim()) {
#         alert("Please enter some text first.");
#         return;
#       }

#       try {
#         const response = await fetch("/api/v1/generate_speech", {
#           method: "POST",
#           headers: { "Content-Type": "application/json" },
#           body: JSON.stringify({ text, voice, speed })
#         });

#         if (!response.ok) {
#           alert("Speech generation failed!");
#           return;
#         }

#         // Convert response wav data to blob and set audio source
#         const blob = await response.blob();
#         const audioUrl = URL.createObjectURL(blob);
#         const audioElement = document.getElementById("result_audio");
#         audioElement.src = audioUrl;
#         audioElement.load();
#         audioElement.play();
#       } catch (err) {
#         console.error(err);
#         alert("An error occurred while generating speech.");
#       }
#     }

#     document.getElementById("generate_btn").addEventListener("click", generateSpeech);
#     </script>
#     """)

# # Turn off queue, just like before
# # audio_custom_blocks.queue = False

# # Create the Gradio app from custom blocks
# # audio_custom_app = gr.routes.App.create_app(audio_custom_blocks)
# # audio_custom_app.blocks.config["show_errors"] = True
# # audio_custom_app.blocks.config["debug"] = True
# # audio_custom_app.blocks.config["cors_allowed_origins"] = ["*"]

# # Mount the new custom app on /gradio_tts or whichever endpoint is desired
# # app.mount("/gradio_tts", audio_custom_app)

# @app.get("/config")
# async def config_route():
#     return RedirectResponse("/gradio_tts/info")


@app.get("/setcookie")
async def setcookie(secret: str, request: Request, response: Response):
    response.set_cookie("secret", value=secret)  # , httponly=True)
    return {"message": "Cookie set"}


@app.get("/gradio_frame")
async def gradio_frame_route(secret: str, request: Request):
    return templates.TemplateResponse(
        "templates/gradio-frame.jinja2", {"request": request, "secret": secret}
    )


@app.post("/api/v1/generate")
async def generate_route(
    generate_params: GenerateParams,
    background_tasks: BackgroundTasks = None,
    request: Request = None,
    secret: Union[str, None] = Header(default=None),
):
    validation_result = validate_generate_params(generate_params)
    if validation_result:
        # return a 400 bad request from fast api
        return HTTPException(status_code=400, detail=validation_result)

    # print(model.config.max_length)
    # print(tokenizer.model_max_length)
    # model.config.max_length = tokenizer.model_max_length

    # with log_time("authorize"):
    #     if not request_authorized(request, secret):
    #         return HTTPException(
    #             status_code=401, detail="Please subscribe at https://text-generator.io/subscribe first"
    #         )
    # todo validate api key and user
    inference_result = fast_inference(generate_params, MODEL_CACHE)
    # todo vuln
    if request and background_tasks:
        if (
            "X-Rapid-API-Key" not in request.headers
            and "x-rapid-api-key" not in request.headers
        ):
            if not API_KEY and secret != sellerinfo.TEXT_GENERATOR_SECRET:
                background_tasks.add_task(
                    track_stripe_request_usage, secret=secret, quantity=1
                )
    return inference_result


@app.post("/api/discord")
async def discord_route(
    type: str = Form(...),
    id: str = Form(...),
    data: str = Form(...),
    # text: str,
    # background_tasks: BackgroundTasks = None,
    # request: Request = None,
    # secret: Union[str, None] = Header(default=None),
    # response: Response = None,
):
    generate_params = GenerateParams(
        **{
            "text": "in 2022 the stock market has been expected to reach a record high.",
            "number_of_results": 1,
            "max_length": 100,
            "max_sentences": 1,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        }
    )


@app.post("/api/v1/generate-bulk")
async def generate_route_bulk(
    bulk_params: List[GenerateParams],
    background_tasks: BackgroundTasks = None,
    request: Request = None,
    secret: Union[str, None] = Header(default=None),
):
    # global daemon
    # print(model.config.max_length)
    # print(tokenizer.model_max_length)
    # model.config.max_length = tokenizer.model_max_length
    model = MODEL_CACHE.add_or_get(
        "text_model", lambda: load_pipelines_and_model(weights_path_tgz)
    )
    # daemon.join()
    inference_results = []
    for generate_params in bulk_params:

        validation_result = validate_generate_params(generate_params)
        if validation_result:
            # return a 400 bad request from fast api
            return HTTPException(status_code=400, detail=validation_result)

    for generate_params in bulk_params:
        inference_result = fast_inference(generate_params)
        inference_results.append(inference_result)
    # todo vuln
    if request and background_tasks:
        if "X-Rapid-API-Key" not in request.headers:
            if not API_KEY and secret != sellerinfo.TEXT_GENERATOR_SECRET:
                background_tasks.add_task(
                    track_stripe_request_usage, secret=secret, quantity=len(bulk_params)
                )
    return inference_results


# ### Bulk generate via csv file upload
# @app.post("/api/v1/generate-batch-csv")
# async def generate_batch_route(
#     background_tasks: BackgroundTasks,
#     request: Request,
#     secret: Union[str, None] = Header(default=None),
#         csv_file: UploadFile = File(default="csv file"),
#
# ):
# #     global daemon
#         # print(model.config.max_length)
#         # print(tokenizer.model_max_length)
#         # model.config.max_length = tokenizer.model_max_length
#         model = MODEL_CACHE.add_or_get("text_model", load_pipelines_and_model)
#         # daemon.join()
#     data = {}
#     contents = await csv_file.read()
#     decoded = contents.decode()
#     buffer = StringIO(decoded)
#     csvReader = csv.DictReader(buffer)
#     for rows in csvReader:
#         generate_params = csv_file.
#     validation_result = validate_generate_params(generate_params)
#     if validation_result:
#         # return a 400 bad request from fast api
#         return HTTPException(status_code=400, detail=validation_result)
#
#     inference_result = fast_inference(generate_params)
#     # todo vuln
#     if "X-Rapid-API-Key" not in request.headers:
#         background_tasks.add_task(track_stripe_request_usage, secret=secret, quantity=1)
#     return inference_result


@app.post("/v1/engines/{engine_name}/completions")
async def openai_route_named(
    engine_name: str,
    openai_params: OpenaiParams,
    background_tasks: BackgroundTasks = None,
    request: Request = None,
    secret: Union[str, None] = Header(default=None),
):
    # global daemon
    # print(model.config.max_length)
    # print(tokenizer.model_max_length)
    # model.config.max_length = tokenizer.model_max_length
    # model = MODEL_CACHE.add_or_get("text_model", lambda: load_pipelines_and_model(weights_path_tgz))
    # daemon.join()
    generate_params = map_to_generate_params(openai_params)
    validation_result = validate_generate_params(generate_params)
    if validation_result:
        # return a 400 bad request from fast api
        return HTTPException(status_code=400, detail=validation_result)
    if (
        "X-Rapid-API-Key" not in request.headers
        and "x-rapid-api-key" not in request.headers
    ):
        header_auth = request.headers.get("Authorization", " ")
        authorization_split = header_auth.split(" ")
        if len(authorization_split) == 2:
            if authorization_split[1]:
                secret = authorization_split[1]
    if not request_authorized(request, secret):
        return HTTPException(
            status_code=401,
            detail="Please subscribe at https://text-generator.io/subscribe first, also ensure you have a credit card on file",
        )
    inference_result = fast_inference(generate_params, MODEL_CACHE)
    if not openai_params.echo:
        ## remove all the inputs from the generated texts
        for i in range(len(inference_result)):
            inference_result[i]["generated_text"] = inference_result[i][
                "generated_text"
            ][len(openai_params.prompt) :]
    # todo vuln
    if request and background_tasks:
        if (
            "X-Rapid-API-Key" not in request.headers
            and "x-rapid-api-key" not in request.headers
        ):
            if not API_KEY and secret != sellerinfo.TEXT_GENERATOR_SECRET:
                background_tasks.add_task(
                    track_stripe_request_usage, secret=secret, quantity=1
                )
    # map to openai response
    return map_to_openai_response(inference_result, generate_params)


@app.post("/v1/completions")
async def openai_route(
    openai_params: OpenaiParams,
    background_tasks: BackgroundTasks = None,
    request: Request = None,
    secret: Union[str, None] = Header(default=None),
):
    return await openai_route_named(
        "engine", openai_params, background_tasks, request, secret
    )


# redirect / to /docs
@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


# @app.get("/gradio_tts_setup")
# async def gradio_setup(response: Response, secret: str=None):
#     if secret and secret != "undefined":
#         response.set_cookie(key="tg_secret", value=secret)
#     return RedirectResponse(url="/gradio_tts")


logger.info(
    """
Welcome to the Text Generator API!
Thanks for using our service. We hope you enjoy it and it means a lot to us that you are here.

Let me know how it goes and if you have any questions or feedback, please reach out at lee.penkman@wordsmashing.com

Downloading models may take a long time on the first run.
"""
)


@app.get("/text-to-speech-demo")
def tts_demo(request: Request):
    return templates.TemplateResponse(
        "shared/text-to-speech.jinja2",
        {
            "request": request,
            "title": "Custom Text-to-Speech Demo",
        },
    )


# @app.post("/api/v1/generate-long")
# async def generate_long_text(
#     generate_params: GenerateParams,
#     background_tasks: BackgroundTasks = None,
#     request: Request = None,
#     secret: Union[str, None] = Header(default=None),
# ):
#     """
#     Generate longer text using Claude 3.7 via netwrck.com API
#     This is optimized for longer, more creative text generation
#     """
#     validation_result = validate_generate_params(generate_params)
#     if validation_result:
#         return HTTPException(status_code=400, detail=validation_result)
#
#     # Authorize the request
#     if request and "X-Rapid-API-Key" not in request.headers and "x-rapid-api-key" not in request.headers:
#         if not API_KEY and secret != sellerinfo.TEXT_GENERATOR_SECRET:
#             if not request_authorized(request, secret):
#                 return HTTPException(
#                     status_code=401,
#                     detail="Please subscribe at https://text-generator.io/subscribe first"
#                 )
#
#     try:
#         # Prepare the prompt for Claude
#         prompt = generate_params.text
#
#         # Set up system message to control generation parameters
#         system_message = f"""
# You are a creative text generation assistant. Generate text that continues from the given prompt.
#
# Parameters to follow:
# - Temperature: {generate_params.temperature}
# - Creativity level: {"high" if generate_params.temperature > 0.7 else "medium" if generate_params.temperature > 0.3 else "low"}
# - Maximum length: {generate_params.max_length} tokens
#
# Important instructions:
# - Continue the text naturally from where the prompt ends
# - Do not repeat the prompt in your response
# - Do not add any explanations, notes, or metadata
# - Do not use phrases like "Here's a continuation" or "Continuing from the prompt"
# - Just generate the continuation text directly
#         """
#
#         # Set up stop sequences
#         stop_sequences = None
#         if generate_params.stop_sequences and len(generate_params.stop_sequences) > 0:
#             stop_sequences = frozenset(generate_params.stop_sequences)
#
#         # Call Claude API
#         generated_text = await query_to_claude_async(
#             prompt=prompt,
#             stop_sequences=stop_sequences,
#             system_message=system_message,
#         )
#
#         # Handle the response
#         if generated_text is None:
#             return HTTPException(status_code=500, detail="Failed to generate text with Claude")
#
#         # Format the response to match the standard API format
#         result = [{
#             "generated_text": prompt + generated_text,
#             "finished_reason": "length",
#             "model": "claude-3-sonnet-20240229"
#         }]
#
#         # Track usage if needed
#         if request and background_tasks:
#             if "X-Rapid-API-Key" not in request.headers and "x-rapid-api-key" not in request.headers:
#                 if not API_KEY and secret != sellerinfo.TEXT_GENERATOR_SECRET:
#                     # Claude is more expensive, so we charge 3 units
#                     background_tasks.add_task(track_stripe_request_usage, secret=secret, quantity=3)
#
#         return result
#
#     except Exception as e:
#         logger.error(f"Error generating text with Claude: {e}")
#         return HTTPException(status_code=500, detail=f"Error generating text: {str(e)}")
#
# @app.post("/api/v1/generate-large")
# async def generate_large_text(
#     generate_params: GenerateParams,
#     background_tasks: BackgroundTasks = None,
#     request: Request = None,
#     secret: Union[str, None] = Header(default=None),
# ):
#     """
# Generate large amounts of text using Claude models
# This endpoint accepts a model parameter to specify which Claude model to use
#     """
#     validation_result = validate_generate_params(generate_params)
#     if validation_result:
#         return HTTPException(status_code=400, detail=validation_result)
#
#     # Authorize the request
#     if request and "X-Rapid-API-Key" not in request.headers and "x-rapid-api-key" not in request.headers:
#         if not API_KEY and secret != sellerinfo.TEXT_GENERATOR_SECRET:
#             if not request_authorized(request, secret):
#                 return HTTPException(
#                     status_code=401,
#                     detail="Please subscribe at https://text-generator.io/subscribe first"
#                 )
#
#     try:
#         # Prepare the prompt for Claude
#         prompt = generate_params.text
#         model_name = "claude-3-7-sonnet-20250219"
#
#         # Set up system message to control generation parameters
#         system_message = f"""
#         You are a creative text generation assistant. Generate text that continues from the given prompt.
#
#         Parameters to follow:
#         - Temperature: {generate_params.temperature}
#         - Creativity level: {"high" if generate_params.temperature > 0.7 else "medium" if generate_params.temperature > 0.3 else "low"}
#         - Maximum length: {generate_params.max_length} tokens
#
#         Important instructions:
#         - Continue the text naturally from where the prompt ends
#         - Do not repeat the prompt in your response
#         - Do not add any explanations, notes, or metadata
#         - Do not use phrases like "Here's a continuation" or "Continuing from the prompt"
#         - Just generate the continuation text directly
#         """
#
#         # Set up stop sequences
#         stop_sequences = None
#         if generate_params.stop_sequences and len(generate_params.stop_sequences) > 0:
#             stop_sequences = frozenset(generate_params.stop_sequences)
#
#         # Call Claude API with the specified model
#         generated_text = await query_to_claude_async(
#             prompt=prompt,
#             stop_sequences=stop_sequences,
#             system_message=system_message,
#             model=model_name,  # Pass the model name to the Claude API function
#         )
#
#         # Handle the response
#         if generated_text is None:
#             return HTTPException(status_code=500, detail="Failed to generate text with Claude")
#
#         # Format the response to match the standard API format
#         result = [{
#             "generated_text": prompt + generated_text,
#             "finished_reason": "length",
#             "model": model_name
#         }]
#
#         # Track usage if needed
#         if request and background_tasks:
#             if "X-Rapid-API-Key" not in request.headers and "x-rapid-api-key" not in request.headers:
#                 if not API_KEY and secret != sellerinfo.TEXT_GENERATOR_SECRET:
#                     # Claude is more expensive, so we charge more units based on the model
#                     quantity = 5 if "opus" in model_name else 3 if "sonnet" in model_name else 2
#                     background_tasks.add_task(track_stripe_request_usage, secret=secret, quantity=quantity)
#
#         return result
#
#     except Exception as e:
#         logger.error(f"Error generating text with Claude: {e}")
#         return HTTPException(status_code=500, detail=f"Error generating text: {str(e)}")

if __name__ == "__main__":

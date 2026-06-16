#!/usr/bin/env python
import asyncio
import logging
import os
import random
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List, Union

import numpy as np
import youtube_dl
from fastapi import BackgroundTasks, File, Form, Header, Request, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from questions.inference_server.tts_utils import apply_manual_speed, optimize_tts_audio_for_speed, write_srt
from questions.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
from typing import Optional

from pydantic import BaseModel
from starlette.responses import (
    JSONResponse,
    RedirectResponse,
    Response,
)

from questions.audio_server.audio_dl import request_get
from questions.constants import weights_path_tgz
from questions.db_models_postgres import User, get_db_session_sync
from questions.models import (
    AudioParams,
    AudioParamsOrAudioFile,
    ChatCompletionParams,
    FeatureExtractParams,
    GenerateParams,
    GenerateSpeechParams,
    OpenaiParams,
    SummarizationParams,
    map_to_chat_completion_response,
    map_to_generate_params,
    map_to_openai_response,
)
from questions.utils import log_time
from sellerinfo import session_secret

# pip install google-api-python-client google-cloud-storage google-auth-httplib2 google-auth-oauthlib

config = {}
config["webapp2_extras.sessions"] = session_secret

templates = Jinja2Templates(directory=".")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

GCLOUD_STATIC_BUCKET_URL = "https://text-generatorstatic.text-generator.io/static"
import stripe

import sellerinfo

app = FastAPI(
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    title="Generate Text API",
    description="Generate text, control stopping criteria like max_length/max_sentences",
    version="1",
)

MODEL_CACHE = None
MULTIMODAL_PROCESSORS = {}
MULTIMODAL_MODELS = {}
INFERENCE_CONCURRENCY = max(1, int(os.getenv("INFERENCE_CONCURRENCY", "1")))
_inference_sem = None
DEEP_LIVENESS_MIN_FREE_VRAM_GB = float(os.getenv("DEEP_LIVENESS_MIN_FREE_VRAM_GB", "8.0"))

GEMMA_TEXT_IMAGE_MODEL_ID = os.getenv(
    "GEMMA_TEXT_IMAGE_MODEL_ID",
    os.getenv("GEMMA_MULTIMODAL_MODEL_ID", "google/gemma-4-26B-A4B-it"),
)
GEMMA_AUDIO_MODEL_ID = os.getenv("GEMMA_AUDIO_MODEL_ID", "google/gemma-4-e4b-it")
GEMMA_VIDEO_MODEL_ID = os.getenv("GEMMA_VIDEO_MODEL_ID", GEMMA_AUDIO_MODEL_ID)
GEMMA_VIDEO_SAMPLE_INTERVAL_SECONDS = max(0.1, float(os.getenv("GEMMA_VIDEO_SAMPLE_INTERVAL_SECONDS", "2.0")))
GEMMA_VIDEO_CHANGE_THRESHOLD = max(0.0, float(os.getenv("GEMMA_VIDEO_CHANGE_THRESHOLD", "8.0")))
GEMMA_VIDEO_MAX_FRAMES = max(1, int(os.getenv("GEMMA_VIDEO_MAX_FRAMES", "32")))
GEMMA_VIDEO_MAX_CANDIDATES = max(GEMMA_VIDEO_MAX_FRAMES, int(os.getenv("GEMMA_VIDEO_MAX_CANDIDATES", "600")))
GEMMA_FRAME_MAX_DIM = max(64, int(os.getenv("GEMMA_FRAME_MAX_DIM", "896")))
GEMMA_AUDIO_MAX_SECONDS = max(1, int(os.getenv("GEMMA_AUDIO_MAX_SECONDS", "30")))
GEMMA_AUDIO_SAMPLE_RATE = max(8000, int(os.getenv("GEMMA_AUDIO_SAMPLE_RATE", "16000")))
GEMMA_AUDIO_SILENCE_TOP_DB = max(10, int(os.getenv("GEMMA_AUDIO_SILENCE_TOP_DB", "32")))
GEMMA_ATTN_IMPLEMENTATION = (os.getenv("GEMMA_ATTN_IMPLEMENTATION", "sdpa") or "").strip() or None
GEMMA_ENABLE_TORCH_COMPILE = os.getenv("GEMMA_ENABLE_TORCH_COMPILE", "0").lower() in {"1", "true", "yes", "on"}
GEMMA_TORCH_COMPILE_MODE = os.getenv("GEMMA_TORCH_COMPILE_MODE", "reduce-overhead")
GEMMA_TORCH_COMPILE_BACKEND = os.getenv("GEMMA_TORCH_COMPILE_BACKEND", "inductor")
GEMMA_TORCH_COMPILE_FULLGRAPH = os.getenv("GEMMA_TORCH_COMPILE_FULLGRAPH", "0").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
GEMMA_TORCH_COMPILE_DYNAMIC = os.getenv("GEMMA_TORCH_COMPILE_DYNAMIC")
GEMMA_ENABLE_TF32 = os.getenv("GEMMA_ENABLE_TF32", "1").lower() in {"1", "true", "yes", "on"}
GEMMA_ENABLE_FLASH_SDP = os.getenv("GEMMA_ENABLE_FLASH_SDP", "1").lower() in {"1", "true", "yes", "on"}
GEMMA_ENABLE_MEM_EFFICIENT_SDP = os.getenv("GEMMA_ENABLE_MEM_EFFICIENT_SDP", "1").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
GEMMA_ENABLE_MATH_SDP = os.getenv("GEMMA_ENABLE_MATH_SDP", "1").lower() in {"1", "true", "yes", "on"}


def _get_torch():
    import torch

    return torch


def _get_multimodal_classes():
    from transformers import AutoModelForCausalLM, AutoProcessor

    return AutoModelForCausalLM, AutoProcessor


def _get_compile_config_class():
    from transformers import CompileConfig

    return CompileConfig


def _model_device(model):
    device = getattr(model, "device", None)
    if device is not None:
        return device
    try:
        return next(model.parameters()).device
    except Exception:
        return "cpu"


def _clear_global_model_refs():
    """Called by ModelCache when idle timeout triggers — resets all global model references."""
    global audio_model, speechgen_model, speech_processor, speech_vocoder, speech_voicepacks
    global supertonic_tts, supertonic_voice_styles
    global MULTIMODAL_MODELS, MULTIMODAL_PROCESSORS

    audio_model = None
    speechgen_model = None
    speech_processor = None
    speech_vocoder = None
    speech_voicepacks = None
    supertonic_tts = None
    supertonic_voice_styles = {}
    MULTIMODAL_MODELS = {}
    MULTIMODAL_PROCESSORS = {}
    logger.info("Cleared all global model references (idle unload)")


def _deep_liveness_vram_status():
    try:
        from questions.inference_server import model_cache as model_cache_module
    except Exception:
        return True, None

    if model_cache_module.DEVICE != "cuda":
        return True, None

    mem = model_cache_module.get_gpu_memory_info()
    return mem.get("free", 0) >= DEEP_LIVENESS_MIN_FREE_VRAM_GB, mem


def _get_model_cache():
    global MODEL_CACHE
    if MODEL_CACHE is None:
        from questions.inference_server.model_cache import ModelCache

        MODEL_CACHE = ModelCache()
        MODEL_CACHE.register_idle_callback(_clear_global_model_refs)
    return MODEL_CACHE


def _get_inference_sem():
    """Return the per-event-loop gate for GPU-bound blocking inference."""
    global _inference_sem
    if _inference_sem is None:
        _inference_sem = asyncio.Semaphore(INFERENCE_CONCURRENCY)
    return _inference_sem


async def _run_gpu_bound(func, *args, **kwargs):
    """Run blocking model work in a worker thread while keeping FastAPI responsive.

    The semaphore preserves the existing one-at-a-time GPU behavior by default, but
    the event loop can still serve lightweight endpoints such as /liveness_check
    while a request is loading or restoring a model.
    """
    sem = _get_inference_sem()
    async with sem:
        return await asyncio.to_thread(func, *args, **kwargs)


def _parse_optional_bool_env(value: Optional[str]) -> Optional[bool]:
    if value is None or value == "":
        return None
    return value.lower() in {"1", "true", "yes", "on"}


def _configure_multimodal_torch_runtime():
    torch = _get_torch()

    if GEMMA_ENABLE_TF32:
        if hasattr(torch, "set_float32_matmul_precision"):
            torch.set_float32_matmul_precision("high")
        if hasattr(torch.backends.cuda, "matmul") and hasattr(torch.backends.cuda.matmul, "allow_tf32"):
            torch.backends.cuda.matmul.allow_tf32 = True
        if hasattr(torch.backends, "cudnn"):
            torch.backends.cudnn.allow_tf32 = True
            torch.backends.cudnn.benchmark = True

    if hasattr(torch.backends, "cuda"):
        if hasattr(torch.backends.cuda, "enable_flash_sdp"):
            torch.backends.cuda.enable_flash_sdp(GEMMA_ENABLE_FLASH_SDP)
        if hasattr(torch.backends.cuda, "enable_mem_efficient_sdp"):
            torch.backends.cuda.enable_mem_efficient_sdp(GEMMA_ENABLE_MEM_EFFICIENT_SDP)
        if hasattr(torch.backends.cuda, "enable_math_sdp"):
            torch.backends.cuda.enable_math_sdp(GEMMA_ENABLE_MATH_SDP)


def _maybe_set_multimodal_attention_implementation(model):
    if not GEMMA_ATTN_IMPLEMENTATION or not hasattr(model, "set_attn_implementation"):
        return

    try:
        model.set_attn_implementation(GEMMA_ATTN_IMPLEMENTATION)
        logger.info("Using Gemma attention implementation: %s", GEMMA_ATTN_IMPLEMENTATION)
    except Exception as exc:
        logger.warning("Failed to set Gemma attention implementation to %s: %s", GEMMA_ATTN_IMPLEMENTATION, exc)


def _build_multimodal_compile_config():
    if not GEMMA_ENABLE_TORCH_COMPILE:
        return None

    CompileConfig = _get_compile_config_class()
    return CompileConfig(
        backend=GEMMA_TORCH_COMPILE_BACKEND,
        mode=GEMMA_TORCH_COMPILE_MODE,
        fullgraph=GEMMA_TORCH_COMPILE_FULLGRAPH,
        dynamic=_parse_optional_bool_env(GEMMA_TORCH_COMPILE_DYNAMIC),
    )


def _build_multimodal_generation_kwargs(
    max_tokens: int,
    temperature: float,
    top_p: float,
    top_k: int,
):
    generation_kwargs = {
        "max_new_tokens": max(1, int(max_tokens or 1024)),
        "do_sample": bool(temperature and temperature > 0),
    }
    if generation_kwargs["do_sample"]:
        generation_kwargs.update(
            {
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
            }
        )

    compile_config = _build_multimodal_compile_config()
    if compile_config is not None:
        generation_kwargs["compile_config"] = compile_config
        generation_kwargs["cache_implementation"] = "static"

    return generation_kwargs


@lru_cache(maxsize=1)
def _ensure_text_pipeline_override():
    # Importing this module patches transformers SUPPORTED_TASKS for our custom pipeline.
    from questions.text_gen_pipeline import TextGenPipeline

    return TextGenPipeline


def _fast_inference(*args, **kwargs):
    _ensure_text_pipeline_override()
    from questions.text_generator_inference import fast_inference

    return fast_inference(*args, **kwargs)


def _direct_inference(*args, **kwargs):
    _ensure_text_pipeline_override()
    from questions.text_generator_inference import direct_inference

    return direct_inference(*args, **kwargs)


def _chat_inference(*args, **kwargs):
    _ensure_text_pipeline_override()
    from questions.text_generator_inference import chat_inference

    return chat_inference(*args, **kwargs)


def _chat_inference_streaming(*args, **kwargs):
    _ensure_text_pipeline_override()
    from questions.text_generator_inference import chat_inference_streaming

    return chat_inference_streaming(*args, **kwargs)


def _fast_feature_extract_inference(*args, **kwargs):
    _ensure_text_pipeline_override()
    from questions.text_generator_inference import fast_feature_extract_inference

    return fast_feature_extract_inference(*args, **kwargs)


def _load_pipelines_and_model(*args, **kwargs):
    _ensure_text_pipeline_override()
    from questions.text_generator_inference import load_pipelines_and_model

    return load_pipelines_and_model(*args, **kwargs)


def _get_extractive_summary(*args, **kwargs):
    from questions.summarization import get_extractive_summary

    return get_extractive_summary(*args, **kwargs)


def _caption_image_bytes(*args, **kwargs):
    from questions.image_captioning.gitbase_captioner import caption_image_bytes

    return caption_image_bytes(*args, **kwargs)


@lru_cache(maxsize=1)
def _get_kokoro_runtime():
    from questions.inference_server.kokoro import compile_model, generate_full
    from questions.inference_server.models import build_model

    return compile_model, generate_full, build_model


@lru_cache(maxsize=1)
def _get_device():
    from questions.perplexity import DEVICE

    return DEVICE

# Preload models on startup for faster first requests (disabled by default for safety)
PRELOAD_MODELS = os.environ.get("PRELOAD_MODELS", "0") == "1"


@app.on_event("startup")
async def preload_models():
    """Preload commonly used models at startup to avoid cold-start latency."""
    if not PRELOAD_MODELS:
        logger.info("Model preloading disabled (PRELOAD_MODELS=0)")
        return

    import asyncio
    logger.info("Preloading models for fast inference...")

    # Run preloads in background to not block startup
    async def _preload():
        try:
            model_cache = _get_model_cache()

            # Preload text generation model
            logger.info("Preloading text generation model...")
            _fast_inference(
                generate_params=GenerateParams(text="warmup", max_length=1),
                model_cache=model_cache,
            )

            # Preload embeddings model
            logger.info("Preloading embeddings model...")
            _fast_feature_extract_inference(
                feature_extract_params=FeatureExtractParams(text="warmup", num_features=768),
                model_cache=model_cache,
            )

            # Preload TTS model
            logger.info("Preloading TTS model...")
            load_speechgen_model()

            logger.info(f"All models preloaded! Cached: {model_cache.list_models()}")

        except Exception as e:
            logger.error(f"Preload error (non-fatal): {e}")

    asyncio.create_task(_preload())


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
STRIPE_CREDIT_BALANCE_METADATA_KEY = "textgen_credit_balance_cents"
# Optional partner secret for the image-caption endpoint. Configure via the
# NETWRCK_IMAGE_CAPTION_SECRET env var; empty default means "disabled" so no
# real secret ships in source. The auth check requires a truthy secret, so an
# empty value here never authorizes a request.
NETWRCK_IMAGE_CAPTION_SECRET = os.getenv("NETWRCK_IMAGE_CAPTION_SECRET", "")


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


def _get_user_for_secret(secret):
    if not secret:
        return None
    return user_secret_matches(secret)


def _get_stripe_credit_balance_cents(stripe_id: Optional[str]) -> int:
    if not stripe_id:
        return 0
    try:
        customer = stripe.Customer.retrieve(stripe_id)
        metadata = getattr(customer, "metadata", None) or customer.get("metadata", {}) or {}
        return max(0, int(metadata.get(STRIPE_CREDIT_BALANCE_METADATA_KEY, 0)))
    except Exception as exc:
        logger.warning("Failed to load Stripe credit balance for %s: %s", stripe_id, exc)
        return 0


def _set_stripe_credit_balance_cents(stripe_id: str, balance_cents: int) -> int:
    normalized_balance = max(0, int(balance_cents))
    stripe.Customer.modify(
        stripe_id,
        metadata={STRIPE_CREDIT_BALANCE_METADATA_KEY: str(normalized_balance)},
    )
    return normalized_balance


def _sync_credit_balance_to_cache(secret: Optional[str], balance_cents: int):
    if not secret:
        return
    existing_user = session_dict.get(secret)
    if existing_user is not None:
        existing_user.free_credits = balance_cents

    try:
        db = get_db_session_sync()
        try:
            db_user = User.get_by_secret(db, secret)
            if db_user:
                db_user.free_credits = balance_cents
                db.commit()
        finally:
            db.close()
    except Exception as exc:
        logger.warning("Failed to sync cached credit balance for secret %s: %s", secret, exc)


def _user_has_subscription_or_credits(secret, minimum_credits: int = 1) -> bool:
    user = _get_user_for_secret(secret)
    if not user:
        return False

    from ..subscription_utils import check_user_subscription

    if check_user_subscription(user):
        return True

    return _get_stripe_credit_balance_cents(user.stripe_id) >= max(1, int(minimum_credits))


def _consume_user_credits(secret, quantity: int) -> bool:
    user = _get_user_for_secret(secret)
    if not user or not user.stripe_id:
        return False

    from ..subscription_utils import check_user_subscription

    if check_user_subscription(user):
        return True

    quantity = max(1, int(quantity))
    current_balance = _get_stripe_credit_balance_cents(user.stripe_id)
    if current_balance < quantity:
        return False

    new_balance = _set_stripe_credit_balance_cents(user.stripe_id, current_balance - quantity)
    _sync_credit_balance_to_cache(secret, new_balance)
    return True


def track_stripe_request_usage(secret, quantity: int):
    # Validate user subscription status without metering usage
    # get the current user
    existing_user = session_dict.get(secret)
    db_user = None

    if existing_user:
        existing_user.charges_monthly += int(quantity * 10)
        # Update user in database
        try:
            db = get_db_session_sync()
            try:
                db_user_obj = User.get_by_secret(db, secret)
                if db_user_obj:
                    db_user_obj.charges_monthly = existing_user.charges_monthly
                    db.commit()
            finally:
                db.close()
        except Exception:
            pass
    if not existing_user:
        try:
            db = get_db_session_sync()
            try:
                db_user = User.get_by_secret(db, secret)
                if not db_user:
                    logger.error(f"user not found for secret: {secret}")
                    return
                db_user.charges_monthly += int(quantity * 10)
                db.commit()
                set_session_for_user(db_user)
            finally:
                db.close()
        except Exception:
            logger.error(f"database error for secret: {secret}")
            return

    existing_user = existing_user or db_user

    # Check if user has active subscription (no metering)
    from ..subscription_utils import check_user_subscription

    has_subscription = check_user_subscription(existing_user)
    if not has_subscription:
        logger.warning(f"User {existing_user.email} does not have an active subscription")
    else:
        logger.info(f"User {existing_user.email} has active subscription - request allowed")


def validate_generate_params(generate_params):
    validate_result = ""
    if generate_params.text == "":
        validate_result = "Please enter some text"
    return validate_result


audio_model = None


def _message_has_media_content(message: dict) -> bool:
    content = message.get("content")
    return isinstance(content, list)


def _normalize_content_part(part: dict) -> dict:
    if hasattr(part, "model_dump"):
        part = part.model_dump()
    elif hasattr(part, "dict"):
        part = part.dict()

    part_type = (part.get("type") or "").lower()

    if part_type in {"text", "input_text"}:
        return {"type": "text", "text": part.get("text", "")}

    if part_type in {"image", "image_url", "input_image"}:
        return {"type": "image", "url": part.get("url") or part.get("image_url")}

    if part_type in {"audio", "input_audio"}:
        return {"type": "audio", "url": part.get("url") or part.get("audio_url")}

    if part_type in {"video", "video_url", "input_video"}:
        return {"type": "video", "url": part.get("url") or part.get("video_url")}

    raise HTTPException(status_code=400, detail=f"Unsupported content part type: {part.get('type')}")


def _normalize_chat_messages(messages: list[dict]) -> list[dict]:
    normalized_messages = []
    for message in messages:
        content = message.get("content")
        if isinstance(content, list):
            normalized_messages.append(
                {
                    "role": message["role"],
                    "content": [_normalize_content_part(part) for part in content],
                }
            )
        else:
            normalized_messages.append({"role": message["role"], "content": content})
    return normalized_messages


def _multimodal_cache_key(model_id: str) -> str:
    return f"multimodal_model::{model_id}"


def _collect_media_types(messages: list[dict]) -> set[str]:
    media_types = set()
    for message in messages:
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            part_type = (part.get("type") or "").lower()
            if part_type in {"audio", "video", "image"}:
                media_types.add(part_type)
    return media_types


def _select_multimodal_model_id(messages: list[dict]) -> str:
    media_types = _collect_media_types(messages)
    if "audio" in media_types:
        return GEMMA_AUDIO_MODEL_ID
    if "video" in media_types:
        return GEMMA_VIDEO_MODEL_ID
    return GEMMA_TEXT_IMAGE_MODEL_ID


def load_multimodal_model(model_id: Optional[str] = None):
    global MULTIMODAL_MODELS
    global MULTIMODAL_PROCESSORS

    selected_model_id = model_id or GEMMA_TEXT_IMAGE_MODEL_ID

    if selected_model_id in MULTIMODAL_MODELS and selected_model_id in MULTIMODAL_PROCESSORS:
        return MULTIMODAL_PROCESSORS[selected_model_id], MULTIMODAL_MODELS[selected_model_id]

    AutoModelForCausalLM, AutoProcessor = _get_multimodal_classes()
    _configure_multimodal_torch_runtime()

    with log_time("load gemma multimodal model"):
        logger.info("Loading Gemma multimodal model: %s", selected_model_id)
        processor = AutoProcessor.from_pretrained(selected_model_id, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            selected_model_id,
            dtype="auto",
            device_map="auto",
            trust_remote_code=True,
        )
        _maybe_set_multimodal_attention_implementation(model)
        MULTIMODAL_PROCESSORS[selected_model_id] = processor
        MULTIMODAL_MODELS[selected_model_id] = model
        logger.info("Gemma multimodal model ready: %s", selected_model_id)

    return processor, model


def _parse_multimodal_response_text(processor, response_text: str) -> tuple[Optional[str], str]:
    parser = getattr(processor, "parse_response", None)
    if callable(parser):
        try:
            parsed = parser(response_text)
            if isinstance(parsed, dict):
                thinking = parsed.get("thinking") or parsed.get("thought") or parsed.get("reasoning_content")
                content = parsed.get("text") or parsed.get("content") or parsed.get("response")
                if content is not None:
                    return thinking, str(content).strip()
            elif isinstance(parsed, str):
                return None, parsed.strip()
        except Exception as exc:
            logger.warning("Gemma parse_response failed, falling back to raw decode: %s", exc)

    if "<|channel|>thought" in response_text and "<channel|>" in response_text:
        try:
            _, tail = response_text.split("<|channel|>thought", 1)
            thought_text, final_text = tail.split("<channel|>", 1)
            return thought_text.strip() or None, final_text.strip()
        except ValueError:
            pass

    return None, response_text.strip()


def _multimodal_chat_inference(
    messages: list,
    model_cache=None,
    model_id: Optional[str] = None,
    enable_thinking: bool = False,
    max_tokens: int = 1024,
    temperature: float = 1.0,
    top_p: float = 0.95,
    top_k: int = 64,
):
    selected_model_id = model_id or _select_multimodal_model_id(messages)
    if model_cache is not None:
        processor, model = model_cache.add_or_get(
            _multimodal_cache_key(selected_model_id),
            lambda: load_multimodal_model(selected_model_id),
        )
    else:
        processor, model = load_multimodal_model(selected_model_id)

    normalized_messages = _normalize_chat_messages(messages)
    inputs = processor.apply_chat_template(
        normalized_messages,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
        add_generation_prompt=True,
        enable_thinking=enable_thinking,
    )

    model_device = _model_device(model)
    if hasattr(inputs, "to"):
        inputs = inputs.to(model_device)
    elif isinstance(inputs, dict):
        inputs = {k: v.to(model_device) if hasattr(v, "to") else v for k, v in inputs.items()}

    input_ids = inputs["input_ids"]
    input_len = input_ids.shape[-1]

    generation_kwargs = _build_multimodal_generation_kwargs(
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
    )

    with _get_torch().inference_mode():
        outputs = model.generate(**inputs, **generation_kwargs)

    if hasattr(outputs, "sequences"):
        sequence = outputs.sequences[0]
    else:
        sequence = outputs[0]
    new_tokens = sequence[input_len:]
    decoded = processor.decode(new_tokens, skip_special_tokens=False)
    thinking_content, generated_text = _parse_multimodal_response_text(processor, decoded)
    return {
        "generated_text": generated_text,
        "thinking_content": thinking_content,
        "stop_reason": "stop",
        "model": selected_model_id,
    }


def _guess_media_suffix(name: Optional[str], default_suffix: str) -> str:
    if not name:
        return default_suffix
    suffix = Path(name).suffix
    return suffix if suffix else default_suffix


def _load_audio_bytes(audio_params: AudioParamsOrAudioFile) -> tuple[bytes, Optional[str]]:
    if hasattr(audio_params, "audio_file") and audio_params.audio_file is not None:
        audio_file = audio_params.audio_file
        return audio_file.file.read(), getattr(audio_file, "filename", None)

    if audio_params.audio_url and "youtube.com" in audio_params.audio_url:
        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                    "preferredquality": "192",
                }
            ],
            "postprocessor_args": ["-ar", str(GEMMA_AUDIO_SAMPLE_RATE)],
            "prefer_ffmpeg": True,
            "keepvideo": False,
            "outtmpl": "/tmp/audio.wav",
        }
        with log_time("download youtube"):
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([audio_params.audio_url])
                downloaded_path = ydl.prepare_filename(ydl.extract_info(audio_params.audio_url))
                with open(downloaded_path, "rb") as file_handle:
                    return file_handle.read(), downloaded_path

    if audio_params.audio_url:
        with log_time("download audio"):
            audio_request = request_get(audio_params.audio_url)
            response = audio_request.result()
            if response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to download audio file at {audio_params.audio_url}",
                )
            response.raw.decode_content = True
            return response.content, audio_params.audio_url

    raise HTTPException(status_code=400, detail="Either audio_file or audio_url must be provided")


def _split_audio_for_transcription(audio_bytes: bytes, source_name: Optional[str]) -> list[tuple[float, float, str]]:
    import librosa

    suffix = _guess_media_suffix(source_name, ".wav")
    tmp_input = NamedTemporaryFile(dir="/dev/shm", delete=False, suffix=suffix)
    try:
        tmp_input.write(audio_bytes)
        tmp_input.flush()
        tmp_input.close()

        waveform, sample_rate = librosa.load(tmp_input.name, sr=GEMMA_AUDIO_SAMPLE_RATE, mono=True)
    finally:
        try:
            os.unlink(tmp_input.name)
        except OSError:
            pass

    if waveform.size == 0:
        return []

    intervals = librosa.effects.split(waveform, top_db=GEMMA_AUDIO_SILENCE_TOP_DB)
    if len(intervals) == 0:
        intervals = np.array([[0, len(waveform)]])

    chunks: list[tuple[float, float, str]] = []
    current_start = int(intervals[0][0])
    current_end = int(intervals[0][1])

    for interval_start, interval_end in intervals[1:]:
        proposed_end = int(interval_end)
        if (proposed_end - current_start) / sample_rate <= GEMMA_AUDIO_MAX_SECONDS:
            current_end = proposed_end
            continue

        chunks.extend(
            _slice_waveform_chunk_ranges(waveform, sample_rate, current_start, current_end, GEMMA_AUDIO_MAX_SECONDS)
        )
        current_start = int(interval_start)
        current_end = int(interval_end)

    chunks.extend(_slice_waveform_chunk_ranges(waveform, sample_rate, current_start, current_end, GEMMA_AUDIO_MAX_SECONDS))
    return chunks


def _slice_waveform_chunk_ranges(
    waveform: np.ndarray,
    sample_rate: int,
    start_index: int,
    end_index: int,
    max_seconds: int,
) -> list[tuple[float, float, str]]:
    import soundfile as soundfile_runtime

    chunks: list[tuple[float, float, str]] = []
    max_samples = max(1, int(max_seconds * sample_rate))
    chunk_start = start_index

    while chunk_start < end_index:
        chunk_end = min(end_index, chunk_start + max_samples)
        chunk_waveform = waveform[chunk_start:chunk_end]
        chunk_file = NamedTemporaryFile(dir="/dev/shm", delete=False, suffix=".wav")
        try:
            soundfile_runtime.write(chunk_file.name, chunk_waveform, sample_rate)
        finally:
            chunk_file.close()
        chunks.append((chunk_start / sample_rate, chunk_end / sample_rate, chunk_file.name))
        chunk_start = chunk_end

    return chunks


def _cleanup_chunk_files(chunks: list[tuple[float, float, str]]):
    for _, _, chunk_path in chunks:
        try:
            os.unlink(chunk_path)
        except OSError:
            pass


def _transcription_prompt(translate_to_english: bool) -> str:
    if translate_to_english:
        return "Transcribe the audio in English. Return only the transcript text."
    return "Transcribe the audio verbatim. Return only the transcript text."


def _sample_video_frames(video_bytes: bytes, source_name: Optional[str]) -> list:
    import cv2
    import numpy as np

    suffix = _guess_media_suffix(source_name, ".mp4")
    tmp = NamedTemporaryFile(dir="/dev/shm", delete=False, suffix=suffix)
    tmp.write(video_bytes)
    tmp.flush()
    tmp.close()
    frame_paths = []
    try:
        cap = cv2.VideoCapture(tmp.name)
        fps = cap.get(cv2.CAP_PROP_FPS)
        if not fps or fps != fps or fps <= 0:
            fps = 1.0
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        step = max(1, int(round(GEMMA_VIDEO_SAMPLE_INTERVAL_SECONDS * fps)))
        if total > 0 and total // step > GEMMA_VIDEO_MAX_CANDIDATES:
            step = max(step, total // GEMMA_VIDEO_MAX_CANDIDATES)
        use_seek = total > 0
        last = None
        cand = 0
        pos = 0
        while cand < GEMMA_VIDEO_MAX_CANDIDATES:
            if use_seek:
                cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
            ok, frame = cap.read()
            if not ok:
                break
            cand += 1
            pos += step
            small = cv2.cvtColor(cv2.resize(frame, (64, 64)), cv2.COLOR_BGR2GRAY).astype(np.float32)
            if last is None or float(np.mean(np.abs(small - last))) >= GEMMA_VIDEO_CHANGE_THRESHOLD:
                last = small
                h, w = frame.shape[:2]
                m = max(h, w)
                if m > GEMMA_FRAME_MAX_DIM:
                    scale = GEMMA_FRAME_MAX_DIM / float(m)
                    frame = cv2.resize(frame, (max(1, int(w * scale)), max(1, int(h * scale))))
                fp = NamedTemporaryFile(dir="/dev/shm", delete=False, suffix=".jpg")
                fp.close()
                cv2.imwrite(fp.name, frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                frame_paths.append(fp.name)
                if len(frame_paths) >= GEMMA_VIDEO_MAX_FRAMES:
                    break
            if not use_seek and step > 1:
                skipped = 0
                while skipped < step - 1 and cap.grab():
                    skipped += 1
        cap.release()
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
    return frame_paths


def _run_video_prompt_with_multimodal_model(video_bytes, source_name, prompt, max_tokens):
    with log_time("sample video frames"):
        frame_paths = _sample_video_frames(video_bytes, source_name)
    if not frame_paths:
        raise HTTPException(status_code=400, detail="Could not extract frames from video")
    logger.info("Sampled %d frames for video", len(frame_paths))
    try:
        content = [{"type": "image", "url": p} for p in frame_paths]
        content.append({"type": "text", "text": prompt})
        result = _multimodal_chat_inference(
            messages=[{"role": "user", "content": content}],
            model_cache=_get_model_cache(),
            model_id=GEMMA_VIDEO_MODEL_ID,
            enable_thinking=False,
            max_tokens=max_tokens,
            temperature=0.0,
            top_p=0.95,
            top_k=64,
        )
        return (result.get("generated_text") or "").strip()
    finally:
        for p in frame_paths:
            try:
                os.unlink(p)
            except OSError:
                pass


def _run_media_prompt_with_multimodal_model(
    media_type: str,
    media_bytes: bytes,
    source_name: Optional[str],
    prompt: str,
    max_tokens: int = 512,
) -> str:
    if media_type == "video":
        return _run_video_prompt_with_multimodal_model(media_bytes, source_name, prompt, max_tokens)
    suffix_defaults = {
        "audio": ".wav",
        "image": ".png",
        "video": ".mp4",
    }
    suffix = _guess_media_suffix(source_name, suffix_defaults.get(media_type, ".bin"))
    selected_model_id = _select_multimodal_model_id(
        [{"role": "user", "content": [{"type": media_type, "url": source_name or suffix}, {"type": "text", "text": prompt}]}]
    )
    tmp_file = NamedTemporaryFile(dir="/dev/shm", delete=False, suffix=suffix)
    try:
        tmp_file.write(media_bytes)
        tmp_file.flush()
        tmp_file.close()
        result = _multimodal_chat_inference(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": media_type, "url": tmp_file.name},
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            model_cache=_get_model_cache(),
            model_id=selected_model_id,
            enable_thinking=False,
            max_tokens=max_tokens,
            temperature=0.0,
            top_p=0.95,
            top_k=64,
        )
        return (result.get("generated_text") or "").strip()
    finally:
        try:
            os.unlink(tmp_file.name)
        except OSError:
            pass


def _transcribe_audio_with_multimodal_model(
    audio_bytes: bytes,
    source_name: Optional[str],
    translate_to_english: bool,
    include_segments: bool,
) -> dict:
    chunks = _split_audio_for_transcription(audio_bytes, source_name)
    if not chunks:
        return {"text": "", "segments": []}

    chunk_results = []
    prompt = _transcription_prompt(translate_to_english)
    try:
        for start_seconds, end_seconds, chunk_path in chunks:
            result = _multimodal_chat_inference(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "audio", "url": chunk_path},
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
                model_cache=_get_model_cache(),
                model_id=GEMMA_AUDIO_MODEL_ID,
                enable_thinking=False,
                max_tokens=512,
                temperature=0.0,
                top_p=0.95,
                top_k=64,
            )
            chunk_text = (result.get("generated_text") or "").strip()
            if not chunk_text:
                continue
            chunk_results.append(
                {
                    "seek": 0,
                    "start": round(start_seconds, 3),
                    "end": round(end_seconds, 3),
                    "text": chunk_text,
                    "temperature": 0.0,
                    "avg_logprob": 0.0,
                    "compression_ratio": 0.0,
                    "no_speech_prob": 0.0,
                }
            )
    finally:
        _cleanup_chunk_files(chunks)

    transcript_parts = [segment["text"] for segment in chunk_results]
    transcript = "\n".join(part for part in transcript_parts if part).strip()
    return {
        "text": transcript,
        "segments": chunk_results if include_segments else [],
    }


class GemmaAudioTranscriber:
    def transcribe(self, audio_inputs, timestamps: bool = True):
        outputs = []
        for audio_input in audio_inputs:
            if isinstance(audio_input, str):
                with open(audio_input, "rb") as file_handle:
                    audio_bytes = file_handle.read()
                source_name = audio_input
            else:
                audio_bytes = audio_input
                source_name = None

            result = _transcribe_audio_with_multimodal_model(
                audio_bytes=audio_bytes,
                source_name=source_name,
                translate_to_english=False,
                include_segments=timestamps,
            )
            outputs.append(result)
        return outputs


def load_audio_model():
    """Load and return the multimodal transcription adapter."""
    global audio_model
    if audio_model is None:
        with log_time("load gemma transcription adapter"):
            load_multimodal_model(GEMMA_AUDIO_MODEL_ID)
            audio_model = GemmaAudioTranscriber()
    return audio_model


def _extract_asr_segments(asr_output) -> list:
    """Best-effort extraction of segment timing data from NeMo ASR output."""
    segments = []
    if asr_output is None:
        return segments

    segment_values = None
    for key in ("segments", "items", "timestamp"):
        value = getattr(asr_output, key, None) if not isinstance(asr_output, dict) else asr_output.get(key)
        if key == "timestamp":
            if isinstance(value, dict):
                value = value.get("segment")
            else:
                value = None
        if value is not None:
            segment_values = value
            break

    if segment_values is None:
        return segments

    if not isinstance(segment_values, (list, tuple)):
        return segments

    for segment in segment_values:
        if not isinstance(segment, dict):
            continue
        start = segment.get("start", 0.0)
        end = segment.get("end", 0.0)
        text = segment.get("text", "") or segment.get("segment", "")
        segments.append(
            {
                "seek": segment.get("seek", 0),
                "start": float(start) if isinstance(start, (int, float)) else 0.0,
                "end": float(end) if isinstance(end, (int, float)) else 0.0,
                "text": text.strip(),
                "temperature": float(segment.get("temperature", 0.0))
                if isinstance(segment.get("temperature"), (int, float))
                else 0.0,
                "avg_logprob": float(segment.get("avg_logprob", 0.0))
                if isinstance(segment.get("avg_logprob"), (int, float))
                else 0.0,
                "compression_ratio": float(segment.get("compression_ratio", 0.0))
                if isinstance(segment.get("compression_ratio"), (int, float))
                else 0.0,
                "no_speech_prob": float(segment.get("no_speech_prob", 0.0))
                if isinstance(segment.get("no_speech_prob"), (int, float))
                else 0.0,
            }
        )

    return segments


def _extract_asr_text_and_segments(asr_result, include_segments: bool) -> tuple[str, list]:
    """Extract plain text and segment timing from NeMo transcription output."""
    if isinstance(asr_result, (list, tuple)) and asr_result:
        asr_result = asr_result[0]

    text = ""
    segments: list = []

    if asr_result is None:
        return text, segments

    if isinstance(asr_result, dict):
        text = asr_result.get("text", "") or asr_result.get("pred_text", "")
        if include_segments:
            segments = _extract_asr_segments(asr_result)
        return str(text).strip(), segments

    text = getattr(asr_result, "text", "")
    if not text:
        text = getattr(asr_result, "pred_text", "")
    if include_segments:
        segments = _extract_asr_segments(asr_result)
    return str(text).strip(), segments


def fast_audio_extract_inference(audio_params: AudioParamsOrAudioFile):
    model_cache = _get_model_cache()
    audio_model = model_cache.add_or_get("audio_model", load_audio_model)
    audio_bytes, source_name = _load_audio_bytes(audio_params)

    include_segments = bool(audio_params.include_segments)
    if (audio_params.output_filetype or "").lower() == "srt":
        include_segments = True

    result = _transcribe_audio_with_multimodal_model(
        audio_bytes=audio_bytes,
        source_name=source_name,
        translate_to_english=audio_params.translate_to_english,
        include_segments=include_segments,
    )

    # Keep the adapter hot in the model cache for benchmark code that still imports load_audio_model().
    model_cache.add_or_get("audio_model", load_audio_model)
    if hasattr(audio_model, "transcribe"):
        return result
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
    include_segments: bool = Form(True),
    secret: Union[str, None] = Header(default=None),
):
    audio_params = AudioParamsOrAudioFile(
        audio_file=audio_file,
        audio_url=None,
        translate_to_english=translate_to_english,
        output_filetype=output_filetype,
        include_segments=include_segments,
    )
    return await audio_extract_shared(background_tasks, audio_params, request, response, secret)


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
    return await audio_extract_shared(background_tasks, feature_extract_params, request, response, secret)


# @app.get("/restart-server")
# async def restart_server():
#     # os.system("sudo systemctl restart text-generator")
#     # restart gunicorn with sighup
#     os.system("kill -SIGHUP `pgrep gunicorn`")
#     return "restarting server"


async def audio_extract_shared(background_tasks, feature_extract_params, request, response, secret):
    if request and "X-Rapid-API-Key" not in request.headers and "x-rapid-api-key" not in request.headers:
        if not API_KEY and secret != sellerinfo.TEXT_GENERATOR_SECRET:
            if not _user_has_subscription_or_credits(secret, minimum_credits=1):
                raise HTTPException(
                    status_code=401,
                    detail="Please subscribe or buy API credits at https://text-generator.io/account before transcribing audio",
                )
    try:
        logger.info("Starting audio extraction")
        inference_result = fast_audio_extract_inference(feature_extract_params)
        logger.info("Audio extraction completed successfully")
    except Exception as e:
        logger.error(f"Error in audio extraction: {e}")
        logger.error(f"Error type: {type(e)}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Audio extraction failed: {str(e)}")
    if "X-Rapid-API-Key" not in request.headers:
        # todo fix
        if inference_result["segments"] and len(inference_result["segments"]) > 0:
            seconds_taken = inference_result["segments"][-1]["end"]
        else:
            # Default to 1 second if no segments found
            seconds_taken = 1.0
        # price of quantity is 1 for .01
        price = seconds_taken * 0.00005
        quantity = price // 0.01
        remainder = price % 0.01
        if random.random() < remainder * 100:
            quantity += 1
        if not API_KEY and secret != sellerinfo.TEXT_GENERATOR_SECRET:
            _consume_user_credits(secret, max(1, int(quantity or 1)))
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
    inference_result = await _run_gpu_bound(_fast_feature_extract_inference, feature_extract_params, _get_model_cache())
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
    text = await _run_gpu_bound(
        _get_extractive_summary,
        summarization_params.text, _get_model_cache(), max_length=summarization_params.max_length or 0
    )
    if "X-Rapid-API-Key" not in request.headers:
        # todo fix
        if random.randint(1, 10) == 10:
            if not API_KEY and secret != sellerinfo.TEXT_GENERATOR_SECRET:
                background_tasks.add_task(track_stripe_request_usage, secret=secret, quantity=1)
    return JSONResponse({"generated_text": text})


@app.get("/liveness_check")
async def liveness_check(request: Request, deep: int = 0):
    try:
        model_cache = _get_model_cache()
        cached = model_cache.list_models()
        if deep:
            has_vram, gpu_memory = _deep_liveness_vram_status()
            if not has_vram:
                logger.warning(
                    "Skipping deep liveness inference: %.2fGB free VRAM below %.2fGB threshold",
                    gpu_memory.get("free", 0),
                    DEEP_LIVENESS_MIN_FREE_VRAM_GB,
                )
                return JSONResponse({
                    "status": "ok",
                    "inference": "ok",
                    "cached_models": cached,
                    "deep_check": "skipped_low_vram",
                    "gpu_memory": gpu_memory,
                    "min_free_vram_gb": DEEP_LIVENESS_MIN_FREE_VRAM_GB,
                })

            # Run a real inference to confirm the pipeline actually works.
            result = await _run_gpu_bound(
                _fast_inference,
                GenerateParams(text="hello", max_length=3, min_probability=0, number_of_results=1),
                model_cache,
            )
            if not result or not isinstance(result, list) or not result[0].get("generated_text"):
                raise RuntimeError(f"Inference returned unexpected result: {result}")
            return JSONResponse({
                "status": "ok",
                "inference": "ok",
                "cached_models": cached,
                "deep_check": "ok",
            })
        # Lightweight health check — never loads or touches models so that
        # periodic health probes don't defeat the idle unload timer.
        return JSONResponse({
            "status": "ok",
            "inference": "ok",
            "cached_models": cached,
        })
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=503)


def user_secret_matches(secret):
    existing_user = session_dict.get(secret)
    db_user = None
    if not existing_user:
        try:
            db = get_db_session_sync()
            try:
                db_user = User.get_by_secret(db, secret)
                if not db_user:
                    logger.error(f"user not found for secret: {secret}")
                    return None
                set_session_for_user(db_user)
            finally:
                db.close()
        except Exception:
            logger.error(f"database error for secret: {secret}")
            return None

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


def image_caption_secret_authorized(request: Request, secret):
    if secret and secret == NETWRCK_IMAGE_CAPTION_SECRET:
        return True
    return request_authorized(request, secret)


def _env_flag(name: str, default: bool) -> bool:
    default_str = "1" if default else "0"
    value = os.environ.get(name, default_str).strip().lower()
    return value in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return default


def _optimize_generated_audio(audio: np.ndarray, sample_rate: int = 24000) -> np.ndarray:
    trim_edges = _env_flag("TTS_TRIM_EDGE_SILENCE", True)
    compress_internal = _env_flag("TTS_COMPRESS_INTERNAL_SILENCE", False)
    if not trim_edges and not compress_internal:
        return audio

    return optimize_tts_audio_for_speed(
        audio,
        sample_rate=sample_rate,
        trim_edges=trim_edges,
        compress_internal=compress_internal,
        edge_trim_ms=max(_env_int("TTS_MAX_EDGE_TRIM_MS", 120), 0),
        internal_silence_min_ms=max(_env_int("TTS_INTERNAL_SILENCE_MIN_MS", 250), 0),
        internal_silence_keep_ms=max(_env_int("TTS_INTERNAL_SILENCE_KEEP_MS", 80), 0),
        threshold=max(_env_int("TTS_SILENCE_THRESHOLD", 64), 1),
    )


import soundfile as sf

speech_processor = None
speechgen_model = None
speech_vocoder = None
speech_voicepacks = None  # Global voicepacks cache
supertonic_tts = None
supertonic_voice_styles = {}

SUPERTONIC_LANGUAGE_CATALOG = {
    "en": "English",
    "ko": "Korean",
    "ja": "Japanese",
    "ar": "Arabic",
    "bg": "Bulgarian",
    "cs": "Czech",
    "da": "Danish",
    "de": "German",
    "el": "Greek",
    "es": "Spanish",
    "et": "Estonian",
    "fi": "Finnish",
    "fr": "French",
    "hi": "Hindi",
    "hr": "Croatian",
    "hu": "Hungarian",
    "id": "Indonesian",
    "it": "Italian",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "nl": "Dutch",
    "pl": "Polish",
    "pt": "Portuguese",
    "ro": "Romanian",
    "ru": "Russian",
    "sk": "Slovak",
    "sl": "Slovenian",
    "sv": "Swedish",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "vi": "Vietnamese",
}
SUPERTONIC_VOICES = tuple(f"{prefix}{index}" for prefix in ("M", "F") for index in range(1, 6))
SUPERTONIC_DEFAULT_STEPS = 4
SUPERTONIC_SYNTH_SPEED = 1.0
SUPERTONIC_DEFAULT_SILENCE_SECONDS = 0.3


def load_speechgen_model():
    global speech_processor
    global speechgen_model
    global speech_vocoder
    global speech_voicepacks

    if not speechgen_model:
        torch = _get_torch()
        compile_model, _, build_model = _get_kokoro_runtime()

        # Load Kokoro model
        device = "cuda" if torch.cuda.is_available() else "cpu"
        speechgen_model = build_model("models/kokoro-v0_19.pth", device)

        # Compile BERT for faster inference (optional, controlled by env var)
        # NOTE: Disabled by default - torch.compile causes CUDA graph assertion errors
        # with dynamic input sizes. Enable with KOKORO_COMPILE=1 if needed for benchmarks.
        if os.environ.get("KOKORO_COMPILE", "0") == "1" and device == "cuda":
            speechgen_model = compile_model(speechgen_model)

        # Load voice packs
        speech_voicepacks = {}
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
            speech_voicepacks[voice] = torch.load(f"models/voices/{voice}.pt", weights_only=True).to(device)

        logger.info(f"Loaded Kokoro TTS with {len(speech_voicepacks)} voices")

    return speechgen_model, speech_voicepacks


def normalize_supertonic_voice(voice: str) -> str:
    voice = (voice or "").strip()
    if voice.lower().startswith("supertonic:"):
        voice = voice.split(":", 1)[1].strip()
    voice = voice.upper()
    if voice in SUPERTONIC_VOICES:
        return voice
    return ""


def is_supertonic_voice_request(voice: str) -> bool:
    voice = (voice or "").strip()
    return voice.lower().startswith("supertonic:") or bool(normalize_supertonic_voice(voice))


def normalize_supertonic_language(language: str) -> str:
    language = (language or "en").strip().lower().replace("_", "-")
    if language == "na":
        return "na"

    language = language.split("-", 1)[0]
    if language in SUPERTONIC_LANGUAGE_CATALOG:
        return language

    supported = ", ".join(SUPERTONIC_LANGUAGE_CATALOG)
    raise ValueError(f"Unsupported Supertonic language '{language}'. Supported languages: {supported}")


def _env_provider_list(name: str) -> Optional[list[str]]:
    value = os.environ.get(name, "").strip()
    if not value:
        return None
    return [provider.strip() for provider in value.split(",") if provider.strip()]


def _supertonic_onnx_providers() -> list[str]:
    import onnxruntime as ort

    available = set(ort.get_available_providers())
    requested = _env_provider_list("SUPERTONIC_ONNX_PROVIDERS")
    if requested is None:
        requested = []
        if _env_flag("SUPERTONIC_ENABLE_TENSORRT", False):
            requested.append("TensorrtExecutionProvider")
        if _env_flag("SUPERTONIC_ENABLE_CUDA", False):
            requested.append("CUDAExecutionProvider")
        requested.append("CPUExecutionProvider")

    providers = [provider for provider in requested if provider in available]
    if not providers:
        providers = ["CPUExecutionProvider"]
    return providers


def _supertonic_thread_counts(providers: list[str]) -> tuple[Optional[int], Optional[int]]:
    def _optional_env_int(name: str) -> Optional[int]:
        value = os.environ.get(name)
        if value is None or value == "":
            return None
        try:
            return max(1, int(value))
        except ValueError:
            logger.warning("Ignoring invalid %s=%r", name, value)
            return None

    intra_threads = _optional_env_int("SUPERTONIC_INTRA_OP_THREADS")
    inter_threads = _optional_env_int("SUPERTONIC_INTER_OP_THREADS")
    if "CUDAExecutionProvider" in providers or "TensorrtExecutionProvider" in providers:
        return intra_threads or 1, inter_threads or 1

    cpu_count = os.cpu_count() or 1
    return intra_threads or min(cpu_count, 16), inter_threads or 1


def _configure_supertonic_onnx_runtime() -> tuple[list[str], Optional[int], Optional[int]]:
    providers = _supertonic_onnx_providers()

    # Supertonic 1.3.1 has a hard-coded provider list in its loader module.
    # Patch it before TTS construction so the loaded sessions use GPU EPs when
    # the installed onnxruntime exposes them.
    import supertonic.config as supertonic_config
    import supertonic.loader as supertonic_loader

    supertonic_config.DEFAULT_ONNX_PROVIDERS = providers
    supertonic_loader.DEFAULT_ONNX_PROVIDERS = providers

    intra_threads, inter_threads = _supertonic_thread_counts(providers)
    logger.info(
        "Supertonic ONNX providers=%s intra_threads=%s inter_threads=%s",
        providers,
        intra_threads if intra_threads is not None else "auto",
        inter_threads if inter_threads is not None else "auto",
    )
    return providers, intra_threads, inter_threads


def load_supertonic_tts():
    global supertonic_tts
    if not supertonic_tts:
        from supertonic import TTS

        _providers, intra_threads, inter_threads = _configure_supertonic_onnx_runtime()
        supertonic_tts = TTS(
            auto_download=True,
            intra_op_num_threads=intra_threads,
            inter_op_num_threads=inter_threads,
        )
        logger.info(
            "Loaded Supertonic TTS with %s voices and %s languages",
            len(SUPERTONIC_VOICES),
            len(SUPERTONIC_LANGUAGE_CATALOG),
        )
        _warmup_supertonic_tts(supertonic_tts)
    return supertonic_tts


def get_supertonic_voice_style(tts, voice: str):
    if voice not in supertonic_voice_styles:
        supertonic_voice_styles[voice] = tts.get_voice_style(voice_name=voice)
    return supertonic_voice_styles[voice]


def _supertonic_fast_synthesize(tts, text: str, style, steps: int, lang: str):
    from supertonic.config import DEFAULT_MAX_CHUNK_LENGTH, DEFAULT_MAX_CHUNK_LENGTH_KO
    from supertonic.utils import chunk_text

    max_chunk_length = DEFAULT_MAX_CHUNK_LENGTH_KO if lang == "ko" else DEFAULT_MAX_CHUNK_LENGTH
    chunks = chunk_text(text, max_chunk_length)
    wavs = []
    durations = []
    for chunk in chunks:
        wav, duration = tts.model([chunk], style, steps, SUPERTONIC_SYNTH_SPEED, lang)
        wavs.append(wav)
        durations.append(duration)

    silence = np.zeros(
        (1, int(SUPERTONIC_DEFAULT_SILENCE_SECONDS * tts.sample_rate)),
        dtype=np.float32,
    )
    parts = []
    for index, wav in enumerate(wavs):
        parts.append(wav)
        if index < len(wavs) - 1:
            parts.append(silence)

    audio = np.concatenate(parts, axis=1)
    duration = sum(durations) + SUPERTONIC_DEFAULT_SILENCE_SECONDS * max(0, len(wavs) - 1)
    return audio, duration


def _warmup_supertonic_tts(tts) -> None:
    if not _env_flag("SUPERTONIC_WARMUP", True):
        return
    try:
        state = np.random.get_state()
        try:
            style = get_supertonic_voice_style(tts, "M1")
            _supertonic_fast_synthesize(tts, "Warmup.", style, SUPERTONIC_DEFAULT_STEPS, "en")
        finally:
            np.random.set_state(state)
        logger.info("Completed Supertonic warmup")
    except Exception as exc:
        logger.warning("Supertonic warmup skipped: %s", exc)


def supertonic_audio_process(text, voice="M1", speed=1.0, language="en", steps=SUPERTONIC_DEFAULT_STEPS):
    if len(text.strip()) == 0:
        return (24000, np.zeros(0).astype(np.int16))

    voice = normalize_supertonic_voice(voice)
    if not voice:
        supported = ", ".join(SUPERTONIC_VOICES)
        raise ValueError(f"Unsupported Supertonic voice. Supported voices: {supported}")

    lang = normalize_supertonic_language(language)
    tts = _get_model_cache().add_or_get("supertonic_tts", load_supertonic_tts)
    style = get_supertonic_voice_style(tts, voice)
    steps = steps or SUPERTONIC_DEFAULT_STEPS
    if _env_flag("SUPERTONIC_FAST_PATH", True):
        try:
            audio, _duration = _supertonic_fast_synthesize(tts, text, style, steps, lang)
        except Exception as exc:
            logger.warning("Supertonic fast path failed, falling back to package pipeline: %s", exc)
            audio, _duration = tts.synthesize(
                text,
                voice_style=style,
                total_steps=steps,
                speed=SUPERTONIC_SYNTH_SPEED,
                lang=lang,
            )
    else:
        audio, _duration = tts.synthesize(
            text,
            voice_style=style,
            total_steps=steps,
            speed=SUPERTONIC_SYNTH_SPEED,
            lang=lang,
        )
    audio = np.asarray(audio)
    if audio.ndim == 2:
        if audio.shape[0] == 1:
            audio = audio[0]
        elif audio.shape[1] == 1:
            audio = audio[:, 0]
        else:
            audio = np.mean(audio, axis=0)
    audio = audio.astype(np.float32, copy=False)

    audio = apply_manual_speed(audio, speed)
    audio = _optimize_generated_audio(audio, sample_rate=tts.sample_rate)
    return (tts.sample_rate, audio)


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


@app.get("/api/v1/speech/catalog")
async def speech_catalog():
    return {
        "providers": {
            "kokoro": {
                "voices": [
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
                ],
                "languages": {"en-us": "American English", "en-gb": "British English"},
            },
            "supertonic": {
                "voices": list(SUPERTONIC_VOICES),
                "languages": SUPERTONIC_LANGUAGE_CATALOG,
                "default_steps": SUPERTONIC_DEFAULT_STEPS,
                "default_synthesis_speed": SUPERTONIC_SYNTH_SPEED,
            },
        }
    }


@app.post("/api/v1/generate_speech")
async def generate_speech(
    generate_speech_params: GenerateSpeechParams,
    background_tasks: BackgroundTasks,
    request: Request,
    response: Response,
    secret: Union[str, None] = Header(default=None),
):
    if not request_authorized(request, secret):
        raise HTTPException(
            status_code=401,
            detail="Invalid Secret, please use the secret found in /account also subscribe at https://text-generator.io/subscribe first, also make sure there is an up to date credit card saved in your account",
        )
    text = generate_speech_params.text

    voice = generate_speech_params.voice
    speed = generate_speech_params.speed
    try:
        rate, processed_np_speech = audio_process(
            text,
            voice,
            speed,
            language=generate_speech_params.language,
            steps=generate_speech_params.steps,
        )
        wav = write_wav(processed_np_speech, rate)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Speech synthesis failed for voice=%s language=%s", voice, generate_speech_params.language)
        return JSONResponse(
            {"detail": "Speech synthesis failed. Please try again."},
            status_code=500,
        )

    headers = {"Content-Disposition": "attachment; filename=audio.wav"}
    # (16000, speech)
    if "X-Rapid-API-Key" not in request.headers:
        # todo fix
        if not API_KEY and secret != sellerinfo.TEXT_GENERATOR_SECRET:
            background_tasks.add_task(track_stripe_request_usage, secret=secret, quantity=1)
    return Response(wav, media_type="audio/wav", headers=headers, background=background_tasks)
    # return Response(wav, media_type="audio/wav")


def gradio_audio_process(text, voice, speed=1.0, language="en", steps=SUPERTONIC_DEFAULT_STEPS):
    """Simplified function that only takes the required parameters"""
    if len(text.strip()) == 0:
        return (24000, np.zeros(0).astype(np.int16))

    if is_supertonic_voice_request(voice):
        return supertonic_audio_process(text, voice=voice, speed=speed, language=language, steps=steps)

    model, voicepacks = _get_model_cache().add_or_get("speech_model", load_speechgen_model)

    # Get the voicepack
    voicepack = voicepacks.get(voice, voicepacks["af_nicole"])

    # Generate audio using Kokoro
    # generate_full handles inputs longer than the default token limit
    _, generate_full, _ = _get_kokoro_runtime()
    audio, phonemes = generate_full(model, text, voicepack, lang=voice[0], speed=speed)
    audio = _optimize_generated_audio(audio, sample_rate=24000)

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
    torch = _get_torch()
    speaker_embedding = np.load(speaker_embeddings[speaker[:3]])
    speaker_embedding = torch.tensor(speaker_embedding).unsqueeze(0).to(_get_device())
    return speaker_embedding


def get_speaker_embeddings_loaded():
    if speaker_embeddings_loaded:
        return speaker_embeddings_loaded
    for ui_name, code_name in speaker_ui_name_to_code_name.items():
        speaker_embeddings_loaded[ui_name] = load_speaker_embedding(code_name)
    return speaker_embeddings_loaded


def audio_process(text, voice="af_nicole", speed=1.0, language="en", steps=SUPERTONIC_DEFAULT_STEPS):
    if len(text.strip()) == 0:
        return (24000, np.zeros(0).astype(np.int16))

    if is_supertonic_voice_request(voice):
        return supertonic_audio_process(text, voice=voice, speed=speed, language=language, steps=steps)

    model, voicepacks = _get_model_cache().add_or_get("speech_model", load_speechgen_model)

    # Get the voicepack
    voicepack = voicepacks.get(voice, voicepacks["af_nicole"])

    # Generate audio using Kokoro
    # generate_full handles inputs longer than the default token limit
    _, generate_full, _ = _get_kokoro_runtime()
    audio, phonemes = generate_full(model, text, voicepack, lang=voice[0], speed=speed)
    audio = _optimize_generated_audio(audio, sample_rate=24000)

    # we could do this but use speed instead
    # Convert to float32 for time-stretch
    # audio_float = audio.astype(np.float32) / 32767.0
    # # Apply time stretch based on 'speed' param (e.g. 2.0 = 2x faster)
    # # if speed != 1.0:
    # #     audio_float = librosa.effects.time_stretch(audio_float, rate=speed)

    # # Convert back to int16
    # audio_stretched = (audio_float * 32767.0).astype(np.int16)

    return (24000, audio)


class ImageCaptionParams(BaseModel):
    """Parameters for image captioning"""

    image_url: Optional[str] = None
    fast_mode: bool = True
    custom_prompt: Optional[str] = None  # For future use if needed


class VideoQuestionParams(BaseModel):
    video_url: Optional[str] = None
    question: str = "Describe this video."


@app.post("/api/v1/image-caption")
async def image_caption(
    image_file: Optional[UploadFile] = File(None, description="Image file (JPEG, PNG, etc.)"),
    image_url: Optional[str] = Form(None, description="URL of image to caption"),
    fast_mode: bool = Form(True, description="Use fast captioning mode for speed"),
    custom_prompt: Optional[str] = Form(None, description="Optional custom captioning prompt"),
    background_tasks: BackgroundTasks = None,
    request: Request = None,
    secret: Union[str, None] = Header(default=None),
):
    """
    Generate caption for uploaded image or image URL using GitBase model.

    - **image_file**: Image file to caption (JPEG, PNG, WebP, etc.) OR
    - **image_url**: URL of image to caption
    - **fast_mode**: Use fast mode (true) or quality mode (false)
    - **secret**: Your API secret for authentication

    Returns JSON with the generated caption.
    """
    # Validate that either file or URL is provided
    if not image_file and not image_url:
        raise HTTPException(status_code=400, detail="Either image_file or image_url must be provided")

    if image_file and image_url:
        raise HTTPException(status_code=400, detail="Provide either image_file or image_url, not both")

    # Check authorization
    if request and "X-Rapid-API-Key" not in request.headers and "x-rapid-api-key" not in request.headers:
        if not API_KEY and secret != sellerinfo.TEXT_GENERATOR_SECRET:
            if not image_caption_secret_authorized(request, secret):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid secret. Please subscribe at https://text-generator.io/subscribe and use your API secret",
                )

    try:
        image_bytes = None
        filename = None

        if image_file:
            # Handle uploaded file
            if not image_file.content_type or not image_file.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail="File must be an image (JPEG, PNG, WebP, etc.)")

            image_bytes = await image_file.read()
            filename = image_file.filename

        elif image_url:
            # Handle image URL
            import httpx

            logger.info(f"Downloading image from URL: {image_url}")

            # Download image from URL asynchronously
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(image_url, timeout=10.0)
                    if response.status_code != 200:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Failed to download image from URL: HTTP {response.status_code}"
                        )

                    # Validate content type
                    content_type = response.headers.get('Content-Type', '')
                    if not content_type.startswith('image/'):
                        raise HTTPException(
                            status_code=400,
                            detail=f"URL does not point to an image. Content-Type: {content_type}"
                        )

                    image_bytes = response.content
                    filename = image_url.split('/')[-1] or 'image_from_url'

            except httpx.HTTPError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to download image from URL: {str(e)}"
                )

        # Validate image size (limit to 10MB)
        if len(image_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image file too large. Maximum size is 10MB.")

        logger.info(
            f"Processing image captioning request: {filename}, size: {len(image_bytes)} bytes, fast_mode: {fast_mode}"
        )

        prompt = custom_prompt or "Describe this image in a concise, useful caption."
        with log_time("image captioning"):
            caption = _caption_image_bytes(image_bytes, prompt=prompt, fast_mode=fast_mode)

        logger.info(f"Generated caption: {caption}")

        # Track usage for billing
        if request and background_tasks:
            if "X-Rapid-API-Key" not in request.headers and "x-rapid-api-key" not in request.headers:
                if not API_KEY and secret not in {sellerinfo.TEXT_GENERATOR_SECRET, NETWRCK_IMAGE_CAPTION_SECRET}:
                    _consume_user_credits(secret, 1)

        return JSONResponse(
            {
                "caption": caption,
                "filename": filename,
                "fast_mode": fast_mode,
                "model": "microsoft/git-base",
                "source": "file" if image_file else "url",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in image captioning: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Image captioning failed: {str(e)}")


@app.post("/api/v1/video-question")
async def video_question(
    video_file: Optional[UploadFile] = File(None, description="Video file"),
    video_url: Optional[str] = Form(None, description="URL of video to analyze"),
    question: str = Form("Describe this video.", description="Question to ask about the video"),
    background_tasks: BackgroundTasks = None,
    request: Request = None,
    secret: Union[str, None] = Header(default=None),
):
    if not video_file and not video_url:
        raise HTTPException(status_code=400, detail="Either video_file or video_url must be provided")
    if video_file and video_url:
        raise HTTPException(status_code=400, detail="Provide either video_file or video_url, not both")

    if request and "X-Rapid-API-Key" not in request.headers and "x-rapid-api-key" not in request.headers:
        if not API_KEY and secret != sellerinfo.TEXT_GENERATOR_SECRET:
            if not _user_has_subscription_or_credits(secret, minimum_credits=1):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid secret. Please subscribe or buy API credits at https://text-generator.io/account",
                )

    try:
        video_bytes = None
        filename = None

        if video_file:
            video_bytes = await video_file.read()
            filename = video_file.filename
        else:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(video_url, timeout=20.0)
                if response.status_code != 200:
                    raise HTTPException(status_code=400, detail=f"Failed to download video from URL: HTTP {response.status_code}")
                video_bytes = response.content
                filename = video_url.split("/")[-1] or "video_from_url"

        answer = _run_media_prompt_with_multimodal_model(
            media_type="video",
            media_bytes=video_bytes,
            source_name=filename,
            prompt=question,
            max_tokens=512,
        )

        if request and background_tasks:
            if "X-Rapid-API-Key" not in request.headers and "x-rapid-api-key" not in request.headers:
                if not API_KEY and secret != sellerinfo.TEXT_GENERATOR_SECRET:
                    _consume_user_credits(secret, 1)

        return JSONResponse(
            {
                "answer": answer,
                "question": question,
                "filename": filename,
                "model": GEMMA_VIDEO_MODEL_ID,
                "source": "file" if video_file else "url",
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in video question endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Video understanding failed: {str(e)}")



import base64 as _base64_mod

@app.post('/api/v1/multimodal-generate')
async def multimodal_generate(
    background_tasks: BackgroundTasks,
    request: Request,
    response: Response,
    audio_file: UploadFile = File(..., description='Audio input file'),
    text: str = Form(''),
    voice: str = Form('af_heart'),
    language: str = Form('en'),
    speed: float = Form(1.0),
    steps: int = Form(SUPERTONIC_DEFAULT_STEPS),
    max_length: int = Form(500),
    secret: Union[str, None] = Header(default=None),
):
    """Audio+text in -> Gemma 4 generates text -> Kokoro TTS generates audio -> returns both."""
    if request and 'X-Rapid-API-Key' not in request.headers and 'x-rapid-api-key' not in request.headers:
        if not API_KEY and secret != sellerinfo.TEXT_GENERATOR_SECRET:
            if not _user_has_subscription_or_credits(secret, minimum_credits=1):
                raise HTTPException(
                    status_code=401,
                    detail='Please subscribe or buy API credits at https://text-generator.io/account',
                )

    audio_bytes = await audio_file.read()
    filename = audio_file.filename or 'audio_input'

    generated_text = _run_media_prompt_with_multimodal_model(
        media_type='audio',
        media_bytes=audio_bytes,
        source_name=filename,
        prompt=text or 'Respond to this audio.',
        max_tokens=max_length,
    )

    rate, speech_np = audio_process(generated_text, voice=voice, speed=speed, language=language, steps=steps)
    wav_bytes = write_wav(speech_np, rate)

    audio_b64 = _base64_mod.b64encode(wav_bytes).decode()

    if request and background_tasks:
        if 'X-Rapid-API-Key' not in request.headers and 'x-rapid-api-key' not in request.headers:
            if not API_KEY and secret != sellerinfo.TEXT_GENERATOR_SECRET:
                _consume_user_credits(secret, 2)

    return JSONResponse({
        'generated_text': generated_text,
        'audio_base64': audio_b64,
        'audio_sample_rate': rate,
        'audio_format': 'wav',
    })


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
description = "<b>How to use:</b> Enter some English text and choose a speaker. Click Submit "
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
    return templates.TemplateResponse("templates/gradio-frame.jinja2", {"request": request, "secret": secret})


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
        raise HTTPException(status_code=400, detail=validation_result)

    # print(model.config.max_length)
    # print(tokenizer.model_max_length)
    # model.config.max_length = tokenizer.model_max_length

    # with log_time("authorize"):
    #     if not request_authorized(request, secret):
    #         return HTTPException(
    #             status_code=401, detail="Please subscribe at https://text-generator.io/subscribe first"
    #         )
    # todo validate api key and user
    inference_result = await _run_gpu_bound(_fast_inference, generate_params, _get_model_cache())
    return inference_result


class AutocompleteParams(GenerateParams):
    # Autocomplete tends to want shorter, higher-confidence completions.
    min_probability: Optional[float] = 0.4
    max_length: Optional[int] = 32


AUTOCOMPLETE_TIMEOUT_SECONDS = 10.0
AUTOCOMPLETE_QUEUE_TIMEOUT_SECONDS = 30.0
_autocomplete_sem: "Optional[object]" = None


def _get_autocomplete_sem():
    # Lazily create the semaphore on the running event loop so it isn't bound
    # to an unrelated loop at import time.
    import asyncio

    global _autocomplete_sem
    if _autocomplete_sem is None:
        _autocomplete_sem = asyncio.Semaphore(1)
    return _autocomplete_sem


async def _run_autocomplete_inference(generate_params: AutocompleteParams, model_cache):
    import asyncio

    sem = _get_inference_sem()
    try:
        await asyncio.wait_for(sem.acquire(), timeout=AUTOCOMPLETE_QUEUE_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=503, detail="Server busy, autocomplete dropped")

    inference_task = None
    timed_out = False
    try:
        inference_task = asyncio.create_task(
            asyncio.to_thread(_fast_inference, generate_params, model_cache)
        )
        return await asyncio.wait_for(
            asyncio.shield(inference_task),
            timeout=AUTOCOMPLETE_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        timed_out = True
        raise HTTPException(status_code=503, detail="Autocomplete exceeded 10s budget")
    finally:
        if timed_out and inference_task is not None:
            def _release_after_timeout(task):
                try:
                    task.result()
                except Exception as exc:
                    logger.debug("Timed-out autocomplete finished with error: %s", exc)
                sem.release()

            inference_task.add_done_callback(_release_after_timeout)
        else:
            sem.release()


@app.post("/api/v1/autocomplete")
async def autocomplete_route(
    generate_params: AutocompleteParams,
    request: Request = None,
    secret: Union[str, None] = Header(default=None),
):
    import asyncio

    validation_result = validate_generate_params(generate_params)
    if validation_result:
        raise HTTPException(status_code=400, detail=validation_result)

    sem = _get_autocomplete_sem()
    # Load-shed autocomplete callers separately from the shared GPU queue. The
    # short generation timeout should start after any cold-start warmup already
    # in progress, not while waiting behind a deep liveness probe.
    try:
        await asyncio.wait_for(sem.acquire(), timeout=AUTOCOMPLETE_QUEUE_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=503, detail="Server busy, autocomplete dropped")

    try:
        return await _run_autocomplete_inference(generate_params, _get_model_cache())
    finally:
        sem.release()


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
    GenerateParams(
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
    model_cache = _get_model_cache()
    model_cache.add_or_get("text_model", lambda: _load_pipelines_and_model(weights_path_tgz))
    # daemon.join()
    inference_results = []
    for generate_params in bulk_params:
        validation_result = validate_generate_params(generate_params)
        if validation_result:
            # return a 400 bad request from fast api
            raise HTTPException(status_code=400, detail=validation_result)

    for generate_params in bulk_params:
        inference_result = _fast_inference(generate_params, model_cache)
        inference_results.append(inference_result)
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
        raise HTTPException(status_code=400, detail=validation_result)
    if "X-Rapid-API-Key" not in request.headers and "x-rapid-api-key" not in request.headers:
        header_auth = request.headers.get("Authorization", " ")
        authorization_split = header_auth.split(" ")
        if len(authorization_split) == 2:
            if authorization_split[1]:
                secret = authorization_split[1]
    if not request_authorized(request, secret):
        raise HTTPException(
            status_code=401,
            detail="Please subscribe at https://text-generator.io/subscribe first, also ensure you have a credit card on file",
        )
    inference_result = await _run_gpu_bound(_fast_inference, generate_params, _get_model_cache())
    if not openai_params.echo:
        ## remove all the inputs from the generated texts
        for i in range(len(inference_result)):
            inference_result[i]["generated_text"] = inference_result[i]["generated_text"][len(openai_params.prompt) :]
    # map to openai response
    return map_to_openai_response(inference_result, generate_params)


@app.post("/v1/completions")
async def openai_route(
    openai_params: OpenaiParams,
    background_tasks: BackgroundTasks = None,
    request: Request = None,
    secret: Union[str, None] = Header(default=None),
):
    return await openai_route_named("engine", openai_params, background_tasks, request, secret)


@app.post("/v1/chat/completions")
async def chat_completions_route(
    chat_params: ChatCompletionParams,
    background_tasks: BackgroundTasks = None,
    request: Request = None,
    secret: Union[str, None] = Header(default=None),
):
    import json
    from time import time as time_now

    # Auth via secret header or Authorization Bearer
    if request:
        header_auth = request.headers.get("Authorization", "")
        if header_auth.startswith("Bearer "):
            bearer_token = header_auth[7:]
            if bearer_token:
                secret = bearer_token

    messages = [{"role": m.role, "content": m.content} for m in chat_params.messages]

    # Convenience alias for clients that use top-level system prompt fields.
    # If both top-level prompt and a leading system role are provided,
    # combine them to preserve existing behavior while keeping top-level precedence.
    top_level_system_message = chat_params.system_message or chat_params.system_prompt
    if top_level_system_message:
        if messages and messages[0].get("role") == "system":
            existing = messages[0].get("content", "")
            if existing:
                messages[0]["content"] = f"{top_level_system_message}\n\n{existing}"
            else:
                messages[0]["content"] = top_level_system_message
        else:
            messages.insert(0, {"role": "system", "content": top_level_system_message})

    has_media_content = any(_message_has_media_content(message) for message in messages)

    if request and "X-Rapid-API-Key" not in request.headers and "x-rapid-api-key" not in request.headers:
        if has_media_content:
            if not _user_has_subscription_or_credits(secret, minimum_credits=1):
                raise HTTPException(
                    status_code=401,
                    detail="Please subscribe or buy API credits at https://text-generator.io/account before sending media",
                )
        elif not request_authorized(request, secret):
            raise HTTPException(
                status_code=401,
                detail="Please subscribe at https://text-generator.io/subscribe first, also ensure you have a credit card on file",
            )

    if chat_params.stream:
        if has_media_content:
            raise HTTPException(status_code=400, detail="Streaming is not supported yet for multimodal chat requests")
        # Streaming SSE response
        async def event_generator():
            chat_id = "chatcmpl-" + str(random.randint(100000, 999999))

            for chunk in _chat_inference_streaming(
                messages=messages,
                model_cache=_get_model_cache(),
                enable_thinking=chat_params.enable_thinking,
                max_tokens=chat_params.max_tokens,
                temperature=chat_params.temperature,
                top_p=chat_params.top_p,
                top_k=chat_params.top_k,
                presence_penalty=chat_params.presence_penalty,
                repetition_penalty=chat_params.repetition_penalty,
            ):
                if not chunk["text"]:
                    continue
                delta = {}
                if chunk["type"] == "content":
                    delta = {"role": "assistant", "content": chunk["text"]}
                elif chunk["type"] == "thinking":
                    delta = {"role": "assistant", "reasoning_content": chunk["text"]}
                else:
                    continue

                sse_data = {
                    "id": chat_id,
                    "object": "chat.completion.chunk",
                    "created": int(time_now()),
                    "model": chat_params.model,
                    "choices": [{"index": 0, "delta": delta, "finish_reason": None}],
                }
                yield f"data: {json.dumps(sse_data)}\n\n"

            # Final chunk
            final = {
                "id": chat_id,
                "object": "chat.completion.chunk",
                "created": int(time_now()),
                "model": chat_params.model,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            }
            yield f"data: {json.dumps(final)}\n\n"
            yield "data: [DONE]\n\n"

        from starlette.responses import StreamingResponse
        return StreamingResponse(event_generator(), media_type="text/event-stream")

    # Non-streaming
    if has_media_content:
        result = await _run_gpu_bound(
            _multimodal_chat_inference,
            messages=messages,
            model_cache=_get_model_cache(),
            enable_thinking=bool(chat_params.enable_thinking),
            max_tokens=chat_params.max_tokens,
            temperature=chat_params.temperature,
            top_p=chat_params.top_p,
            top_k=chat_params.top_k,
        )
        if request and "X-Rapid-API-Key" not in request.headers and "x-rapid-api-key" not in request.headers:
            if not API_KEY and secret != sellerinfo.TEXT_GENERATOR_SECRET:
                _consume_user_credits(secret, 1)
    else:
        result = await _run_gpu_bound(
            _chat_inference,
            messages=messages,
            model_cache=_get_model_cache(),
            enable_thinking=chat_params.enable_thinking,
            max_tokens=chat_params.max_tokens,
            temperature=chat_params.temperature,
            top_p=chat_params.top_p,
            top_k=chat_params.top_k,
            presence_penalty=chat_params.presence_penalty,
            repetition_penalty=chat_params.repetition_penalty,
        )

    return map_to_chat_completion_response(
        generated_text=result["generated_text"],
        thinking_content=result.get("thinking_content"),
        model=result.get("model") or chat_params.model,
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
#             "model": "claude-sonnet-4-20250514"
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
#         model_name = "claude-sonnet-4-20250514"
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
    import uvicorn

    logger.info("Starting inference server on port 9081")
    uvicorn.run(app, host="0.0.0.0", port=9081, log_level="info", access_log=True)

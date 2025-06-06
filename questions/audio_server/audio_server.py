#!/usr/bin/env python
import json
import os
import random
from tempfile import NamedTemporaryFile
from typing import Union

import torch
from fastapi import BackgroundTasks
from fastapi import Request, Header
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging
from questions.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
from starlette.responses import JSONResponse, Response

from questions.audio_server.audio_dl import request_get
from questions.db_models import User
from questions.gameon_utils import GameOnUtils
from questions.models import (
    GetUserRequest,
    AudioParams,
)
from questions.payments.payments import get_subscription_item_id_for_user_email
from questions.text_gen_pipeline import TextGenPipeline
from questions.utils import log_time

assert TextGenPipeline is not None  # needed to override

# pip install google-api-python-client google-cloud-storage google-auth-httplib2 google-auth-oauthlib

FACEBOOK_APP_ID = "138831849632195"
FACEBOOK_APP_SECRET = "93986c9cdd240540f70efaea56a9e3f2"

config = {}
config["webapp2_extras.sessions"] = dict(secret_key="93986c9cdd240540f70efaea56a9e3f2")

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

# about 10s
with log_time("load whisper model"):
    model = whisper.load_model("large")

    model.eval()

# @app.post("/files/")
# async def create_files(files: bytes = File()):
#     return {"file_sizes": [len(file) for file in files]}

languages = {"af_za": "Afrikaans", "am_et": "Amharic", "ar_eg": "Arabic", "as_in": "Assamese", "az_az": "Azerbaijani", "be_by": "Belarusian", "bg_bg": "Bulgarian", "bn_in": "Bengali", "bs_ba": "Bosnian", "ca_es": "Catalan", "cmn_hans_cn": "Chinese", "cs_cz": "Czech", "cy_gb": "Welsh", "da_dk": "Danish", "de_de": "German", "el_gr": "Greek", "en_us": "English", "es_419": "Spanish", "et_ee": "Estonian", "fa_ir": "Persian", "fi_fi": "Finnish", "fil_ph": "Tagalog", "fr_fr": "French", "gl_es": "Galician", "gu_in": "Gujarati", "ha_ng": "Hausa", "he_il": "Hebrew", "hi_in": "Hindi", "hr_hr": "Croatian", "hu_hu": "Hungarian", "hy_am": "Armenian", "id_id": "Indonesian", "is_is": "Icelandic", "it_it": "Italian", "ja_jp": "Japanese", "jv_id": "Javanese", "ka_ge": "Georgian", "kk_kz": "Kazakh", "km_kh": "Khmer", "kn_in": "Kannada", "ko_kr": "Korean", "lb_lu": "Luxembourgish", "ln_cd": "Lingala", "lo_la": "Lao", "lt_lt": "Lithuanian", "lv_lv": "Latvian", "mi_nz": "Maori", "mk_mk": "Macedonian", "ml_in": "Malayalam", "mn_mn": "Mongolian", "mr_in": "Marathi", "ms_my": "Malay", "mt_mt": "Maltese", "my_mm": "Myanmar", "nb_no": "Norwegian", "ne_np": "Nepali", "nl_nl": "Dutch", "oc_fr": "Occitan", "pa_in": "Punjabi", "pl_pl": "Polish", "ps_af": "Pashto", "pt_br": "Portuguese", "ro_ro": "Romanian", "ru_ru": "Russian", "sd_in": "Sindhi", "sk_sk": "Slovak", "sl_si": "Slovenian", "sn_zw": "Shona", "so_so": "Somali", "sr_rs": "Serbian", "sv_se": "Swedish", "sw_ke": "Swahili", "ta_in": "Tamil", "te_in": "Telugu", "tg_tj": "Tajik", "th_th": "Thai", "tr_tr": "Turkish", "uk_ua": "Ukrainian", "ur_pk": "Urdu", "uz_uz": "Uzbek", "vi_vn": "Vietnamese", "yo_ng": "Yoruba"}

print(
    f"Model is {'multilingual' if model.is_multilingual else 'English-only'} "
    f"and has {sum(np.prod(p.shape) for p in model.parameters()):,} parameters."
)
# expose best of?
options = {} # dict(beam_size=5, best_of=5) (makes it slower)
transcribe_options = dict(task="transcribe", **options)
translate_options = dict(task="translate", **options)

#%%
references = []
transcriptions = []
translations = []

# for audio, text in tqdm(dataset):
#     transcription = model.transcribe(audio, **transcribe_options)["text"]
#     translation = model.transcribe(audio, **translate_options)["text"]
# result = model.transcribe("/media/lee/78ca132e-d181-4406-aea5-3c9665f486cc/Videos/intro-bitbanknz.mp3") 40/6s

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/gameon/static", StaticFiles(directory="gameon/static"), name="gameon/static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# download gpt neo model and load it into memory

# DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
API_KEY = os.getenv("API_KEY", None)


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


def set_session_for_user(user):
    session_dict[user.secret] = user


@app.post("/api/get-user")
async def get_user(get_user_request: GetUserRequest, response: Response):
    email = get_user_request.email
    user = User.byEmail(email)  # todo fix vuln
    # create the user?
    set_session_for_user(user)

    # get if the user is subscribed to a plan in stripe
    subscription_item_id = get_subscription_item_id_for_user_email(user.email)
    user.is_subscribed = subscription_item_id is not None
    return JSONResponse(json.loads(json.dumps(user.to_dict(), cls=GameOnUtils.MyEncoder)))


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
        db_user.charges_monthly += int(quantity * 10)
        User.save(db_user)
        set_session_for_user(db_user)

    existing_user = existing_user or db_user

    subscription_item_id = get_subscription_item_id_for_user_email(existing_user.email)
    if not subscription_item_id:
        logger.info(
            f"no subscription item id for user: {existing_user.email} {existing_user.stripe_id}"
        )
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

def fast_audio_extract_inference(audio_params: AudioParams):
    audio_request = request_get(audio_params.audio_url)
    response = audio_request.result()
    if response.status_code != 200:
        raise HTTPException(
            status_code=500, detail=f"Failed to download audio file at {audio_params.audio_url}"
        )
    response.raw.decode_content = True
    audio_bytes = response.content
    with torch.inference_mode():
        opts = transcribe_options # dict(beam_size=5, best_of=5)
        if audio_params.translate_to_english:
            opts = translate_options
        # write to /dev/shm ... assume mp3
        tmp_file = NamedTemporaryFile(dir="/dev/shm", delete=True, suffix=".mp3")
        tmp_file.write(audio_bytes)
        result = model.transcribe(tmp_file.name, **opts)

        # clean data
        tmp_file.close()
        for segment in result['segments']:
            del segment['tokens']
        result['text'] = result['text'].strip()
        return result


@app.post("/api/v1/audio-extraction")
async def audio_extraction(
    feature_extract_params: AudioParams, # wav files or mp3 supported
    # audio_file: UploadFile,
    background_tasks: BackgroundTasks,
    request: Request,
    secret: Union[str, None] = Header(default=None),
):
    if not request_authorized(request, secret):
        return HTTPException(
            status_code=401, detail="Please subscribe at https://text-generator.io/subscribe first"
        )
    inference_result = fast_audio_extract_inference(feature_extract_params)
    if "X-Rapid-API-Key" not in request.headers:
        # todo fix
        seconds_taken = inference_result['segments'][-1]['end']
        # price of quantity is 1 for .01
        price = seconds_taken * 0.00005
        quantity = price // .01
        remainder = price % .01
        if random.random() < remainder * 100:
            quantity += 1
        if quantity:
            if not API_KEY:

               background_tasks.add_task(track_stripe_request_usage, secret=secret, quantity=int(quantity))
    return inference_result


def user_authorized(secret):
    existing_user = session_dict.get(secret)
    db_user = None
    if not existing_user:
        db_user = User.bySecret(secret)
        if not db_user:
            logger.error(f"user not found for secret: {secret}")

            return None
        set_session_for_user(db_user)

    existing_user = existing_user or db_user

    subscription_item_id = get_subscription_item_id_for_user_email(existing_user.email)
    return subscription_item_id


def request_authorized(request: Request, secret):
    # todo fix vuln
    if "X-Rapid-API-Key" in request.headers or "x-rapid-api-key" in request.headers:
        return True
    return user_authorized(secret)


# ### Bulk generate via csv file upload
# @app.post("/api/v1/generate-batch-csv")
# async def generate_batch_route(
#     background_tasks: BackgroundTasks,
#     request: Request,
#     secret: Union[str, None] = Header(default=None),
#         csv_file: UploadFile = File(default="csv file"),
#
# ):
#     global daemon
#     if not model:
#         # print(model.config.max_length)
#         # print(tokenizer.model_max_length)
#         # model.config.max_length = tokenizer.model_max_length
#         load_pipelines_and_model()
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


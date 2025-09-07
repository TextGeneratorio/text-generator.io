import logging
import math
import traceback
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from accelerate import Accelerator

# from accelerate.utils import is_tpu_available
from cachetools import TTLCache

from questions.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
import os

from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    GPT2TokenizerFast,
    GPTNeoForCausalLM,
    StoppingCriteriaList,
    pipeline,
    set_seed,
)

from questions import link_enricher
from questions.bert_embed import get_bert_embeddings_fast
from questions.constants import weights_path_tg, weights_path_tgc, weights_path_tgz
from questions.download_utils import download_model
from questions.fixtures import get_stop_reason, set_stop_reason
from questions.models import FeatureExtractParams, GenerateParams
from questions.perplexity import get_perplexity
from questions.post_process_results import post_process_results
from questions.stopping_criteria import MinProbCriteria, SentenceCriteria, StopSequencesCriteria
from questions.utils import debug, log_time

cuda_is_available = False
try:
    import torch

    torch._C._jit_set_profiling_executor(False)
    cuda_is_available = torch.cuda.is_available()
except ImportError:
    logger.info("no torch mode")


DEVICE = "cuda" if cuda_is_available else "cpu"

weights_to_model = {
    weights_path_tg: None,
    weights_path_tgz: None,
    weights_path_tgc: None,
}
weights_to_tokenizer = {
    weights_path_tg: None,
    weights_path_tgz: None,
    weights_path_tgc: None,
}
weights_to_generator = {
    weights_path_tg: None,
    weights_path_tgz: None,
    weights_path_tgc: None,
}
weights_to_name_key = {
    weights_path_tgz: "text_model",
    weights_path_tgc: "chat_model",
    weights_path_tg: "tg_text_model",
}
name_key_to_weights = {v: k for k, v in weights_to_name_key.items()}

# if is_tpu_available():
#     import torch_xla.core.xla_model as xm

# DEVICE = "tpu" if is_tpu_available() else DEVICE

# weights_path = "models/tg-1b3/"
# weights_path = "models/tg-2b5/"
# weights_path = "models/tg-6b3/" # latest model

weights_path = os.getenv("WEIGHTS_PATH", "models/tgz-7b1/")  # latest model
# weights_path = os.getenv("WEIGHTS_PATH", "models/tg-1b3/") # latest model

# if debug:
#     # small model locally for fasterness
#     weights_path = "models/tg-1b3/"


def load_model(weights_path):
    # download gpt neo model and load it into memory
    # download from gs://20-questions/gpt-neo-model.tar.gz
    # download artefact to disk
    # gsutil cp gs://20-questions/gpt-neo-model.tar.gz .
    # extract to disk
    # tar -xvf gpt-neo-model.tar.gz
    # load model
    if (Path("/" + weights_path) / "config.json").exists():
        weights_path = str(Path("/") / weights_path)

    # if (Path("/models")).exists(): # prefer to save in ramdisk
    #     weights_path = "/" + weights_path

    if not (Path(weights_path) / "config.json").exists():
        download_model(weights_path, weights_path)

    logger.info(f"loading model from {weights_path}")

    low_mem = True
    # model = GPT2LMHeadModel.from_pretrained('gpt2', low_cpu_mem_usage=low_mem, pad_token_id=tokenizer.eos_token_id)
    if "gpt-neo" in weights_path:
        tokenizer = GPT2TokenizerFast.from_pretrained(weights_path)
        model = GPTNeoForCausalLM.from_pretrained(
            weights_path, pad_token_id=tokenizer.eos_token_id, low_cpu_mem_usage=low_mem
        )
    else:
        tokenizer = AutoTokenizer.from_pretrained(weights_path, padding_side="left", trust_remote_code=True)

        model = AutoModelForCausalLM.from_pretrained(
            weights_path,
            low_cpu_mem_usage=low_mem,
            device_map="auto",  # torch_dtype=torch.bfloat16,
            trust_remote_code=True,
            pad_token_id=tokenizer.eos_token_id,
        )
    # elif "tg" in weights_path:
    #     tokenizer = BloomTokenizerFast.from_pretrained(weights_path)

    #     model = BloomForCausalLM.from_pretrained(
    #         weights_path, low_cpu_mem_usage=low_mem, pad_token_id=tokenizer.eos_token_id
    #     )
    # else:
    #     tokenizer = AutoTokenizer.from_pretrained(weights_path, )
    #     model = AutoModelForCausalLM.from_pretrained(weights_path, device_map="auto", torch_dtype=torch.bfloat16)

    full_vocab_tokens = list(range(tokenizer.vocab_size))
    # dont generate the pad token which is the eos_token_id which causes stopping!
    full_vocab_tokens.pop(2)
    weights_to_full_vocab_tokens[weights_path] = full_vocab_tokens
    logger.info("model loaded")
    create_tokens_with_prefix_dict(weights_path, tokenizer.get_vocab())
    # model.to(DEVICE)
    # quantize dynamic
    if DEVICE == "cuda":
        # model.bfloat16() # works for some new gpus instead of half()
        # model.to(DEVICE, non_blocking=True)
        accelerator = Accelerator(mixed_precision="bf16")
        model = model.bfloat16()

        # device_map = infer_auto_device_map(model, max_memory={0: "20GiB"})
        # model = dispatch_model(model, device_map, offload_dir="/dev/shm")
        # model = accelerator.prepare_model(model)

        logger.info("Quantizing model to bf16 cuda")
    elif DEVICE == "tpu":
        # model.bfloat16() # works for some new gpus instead of half()
        # model.to(DEVICE, non_blocking=True)
        accelerator = Accelerator(mixed_precision="bf16", rng_types=["tpu"])
        model = accelerator.prepare_model(model)

        logger.info("Quantizing model to bf16 tpu")
    else:
        # set 1 thread, this makes it take longer /use less cpus
        # num cpus + 2
        torch.set_num_threads(6)
        # if "tg" in weights_path:

        # make sure its full precision to quantize instead of from half p
        # this may take up lots of memory :(
        model.float()
        # model.forward = torch.cuda.amp.autocast(dtype=torch.bfloat16)(model.forward)
        # model.bfloat16()
        # logger.info("Quantizing model to bf16cpu")

        # accelerator = Accelerator(mixed_precision="bf16", cpu=True)
        #
        # accelerator.prepare_model(model)
        # model = torch.nn.parallel.DistributedDataParallel(model, {})

        # todo currently causes quality issues w tg
        model = torch.quantization.quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8, inplace=True)
        logger.info("Quantizing model to 8bit")

    model.eval()
    logger.info("Model loaded")
    return tokenizer, model


weights_to_tokens_with_prefix_dict = {}


def create_tokens_with_prefix_dict(weights_path, vocab: Dict[str, int]) -> Dict[str, List[int]]:
    tokens_with_prefix_dict = defaultdict(list)
    for word, token in vocab.items():
        for i in range(1, len(word) + 1):
            subword = word[:i]
            tokens_with_prefix_dict[subword].append(token)
    weights_to_tokens_with_prefix_dict[weights_path] = tokens_with_prefix_dict


def all_first_and_last_token(tokenized_text):
    return tokenized_text[:-1], tokenized_text[-1]


weights_to_full_vocab_tokens = {}


def run_feature_extractor(feature_extract_params: FeatureExtractParams, model_cache):
    input_text = feature_extract_params.text
    with log_time("link_enrichment"):
        input_text = link_enricher.enrich_links_remove_links(input_text)
    return get_bert_embeddings_fast([input_text], model_cache)[0]


def inference(generate_params: GenerateParams, weights_path: str = None, model_cache=None):
    global weights_to_generator
    global weights_to_tokens_with_prefix_dict
    global weights_to_tokenizer

    tokenizer = weights_to_tokenizer.get(weights_path)
    tokens_with_prefix_dict = weights_to_tokens_with_prefix_dict.get(weights_path)
    if generate_params.seed:
        set_seed(generate_params.seed)
    # todo longer inference
    generate_params.max_length = min(generate_params.max_length, 600)
    if generate_params.temperature == 0:
        generate_params.temperature = 1
    starting_ignored_prefix = ""
    input_text = generate_params.text

    if len(generate_params.text) > 1000:
        input_text = generate_params.text[-1000:]
        starting_ignored_prefix = generate_params.text[:-1000]
    original_input_text = input_text
    with log_time("link_enrichment"):
        input_text = link_enricher.enrich_links(input_text)
    stopping_criteria_list = []
    if generate_params.max_sentences:
        stopping_criteria_list.append(SentenceCriteria(tokenizer, input_text, generate_params.max_sentences))
    if generate_params.min_probability != 0:
        stopping_criteria_list.append(MinProbCriteria(generate_params.min_probability))
    if generate_params.stop_sequences:
        stopping_criteria_list.append(StopSequencesCriteria(tokenizer, input_text, generate_params.stop_sequences))

    # reduce the text to 1000 characters so that inference works
    # TODO long sentences are not handled well
    # todo generate min_length then the rest with stopping criteria
    results = []
    if debug:
        logger.info(input_text)
    tokenized_text = tokenizer.encode(input_text)
    # todo handle short/empty sequence?
    prefix_tokens, prefix_last_token = all_first_and_last_token(tokenized_text)

    last_token_text = tokenizer.decode([prefix_last_token])
    input_prefix = input_text[
        : -len(last_token_text)
    ]  # this is a more accurate way to remove the last token as encode/decode can change the text
    token_lookup_text = last_token_text.replace(" ", "Ġ")
    initial_valid_tokens = tokens_with_prefix_dict[token_lookup_text]
    prefix_allowed_tokens_fn = None
    if initial_valid_tokens:

        def prefix_allowed_tokens_fn(batch_num: int, input_tokens: List[int]) -> List[int]:
            if len(input_tokens) == len(prefix_tokens):
                return initial_valid_tokens
            return weights_to_full_vocab_tokens.get(weights_path)

    else:
        # todo check if this is needed
        def prefix_allowed_tokens_fn(batch_num: int, input_tokens: List[int]) -> List[int]:
            return weights_to_full_vocab_tokens.get(weights_path)

    # TODO If there are no valid tokens that means that the last word should be treated as a full word
    if not initial_valid_tokens:
        input_prefix += last_token_text

    tokenized_nelements = len(tokenized_text)
    generator = weights_to_generator[weights_path]
    for i in range(generate_params.number_of_results):
        # TODO batching, done in a loop because of stopping criteria
        set_stop_reason("max_length")
        max_length = tokenized_nelements + generate_params.max_length + 1

        try:
            output = generator(
                input_prefix,
                max_length=max_length,
                # min_length=generate_params.min_length,
                temperature=generate_params.temperature,
                top_k=generate_params.top_k,
                top_p=generate_params.top_p,
                do_sample=True,
                num_return_sequences=1,
                # length_penalty=1.0,
                # no_repeat_ngram_size=2,
                repetition_penalty=generate_params.repetition_penalty,
                output_scores=True,
                stopping_criteria=StoppingCriteriaList(stopping_criteria_list),
                # handle_long_generation='hole', # todo fix long sequence generation, this fails fast
                clean_up_tokenization_spaces=True,
                use_cache=True,
                return_dict_in_generate=True,
                # typical_p=.1,
                prefix_allowed_tokens_fn=prefix_allowed_tokens_fn,
            )
        except Exception as e:
            logger.info(e)
            traceback.print_exc()
            model_cache.unload_all_but_current_model_save_mem()
            try:
                output = generator(
                    input_prefix,
                    max_length=max_length,
                    # min_length=generate_params.min_length,
                    temperature=generate_params.temperature,
                    top_k=generate_params.top_k,
                    top_p=generate_params.top_p,
                    do_sample=True,
                    num_return_sequences=1,
                    # length_penalty=1.0,
                    # no_repeat_ngram_size=2,
                    repetition_penalty=generate_params.repetition_penalty,
                    output_scores=True,
                    stopping_criteria=StoppingCriteriaList(stopping_criteria_list),
                    # handle_long_generation='hole', # todo fix long sequence generation, this fails fast
                    clean_up_tokenization_spaces=True,
                    use_cache=True,
                    return_dict_in_generate=True,
                    # typical_p=.1,
                    prefix_allowed_tokens_fn=prefix_allowed_tokens_fn,
                )
            except Exception as e:
                logger.info(e)
                traceback.print_exc()

                weights_to_model[weights_path] = model_cache.add_or_get(
                    "tg_text_model", lambda: load_pipelines_and_model(weights_path)
                )
                generator = weights_to_generator[weights_path]
                output = generator(
                    input_prefix,
                    max_length=max_length,
                    # min_length=generate_params.min_length,
                    temperature=generate_params.temperature,
                    top_k=generate_params.top_k,
                    top_p=generate_params.top_p,
                    do_sample=True,
                    num_return_sequences=1,
                    # length_penalty=1.0,
                    # no_repeat_ngram_size=2,
                    repetition_penalty=generate_params.repetition_penalty,
                    output_scores=True,
                    stopping_criteria=StoppingCriteriaList(stopping_criteria_list),
                    # handle_long_generation='hole', # todo fix long sequence generation, this fails fast
                    clean_up_tokenization_spaces=True,
                    use_cache=True,
                    return_dict_in_generate=True,
                    # typical_p=.1,
                    prefix_allowed_tokens_fn=prefix_allowed_tokens_fn,
                )
                # last change restart
            # if 'cuda' in str(e).lower():
            # logger.info("restarting to fix cuda issues")
            # os.system("/usr/bin/bash kill -SIGHUP `pgrep gunicorn`")
            # os.system("kill -1 `pgrep gunicorn`")
        result = output[0] or {}
        result["stop_reason"] = get_stop_reason()
        # todo do min edit distance so that it starts with initial_valid_tokens to fix bug?
        ## retry if max_length and it didnt actually generate max length?
        # old pad token stopping fix
        # if result['stop_reason'] == "max_length":
        #     # check if it really did stop because of max length
        #     # TODO override postprocess pipeline to save logits/not duplicate re tokenization
        #     generated_text_token_count = len(tokenizer.encode(result['generated_text']))
        #     generated_count = generated_text_token_count - tokenized_nelements
        #     generated_closeness_ratio = generated_count / (generate_params.max_length + 1)
        #     if generated_closeness_ratio < .2:
        #         # regenerate without using prefix allowed tokens, likely this caused an issue where nothing was possible to match the prefix and the prefix iteself perhaps is a token or unlikely
        #         # try a different network where its more likely to not generate a eos_token_id
        #         # if you set a eos_token_id=3 youll notice it generates longer as its generating the eos token here
        #         # eos token is the pad token 2, we could disallow this until it gets close to maxlen
        current_result = result["generated_text"][len(input_prefix) :]
        if not current_result.startswith(last_token_text) and initial_valid_tokens:
            logger.info("fixing bad starting bug via retry")
            set_stop_reason("max_length")
            max_length = tokenized_nelements + generate_params.max_length + 1

            output = generator(
                input_text,
                max_length=max_length,
                # min_length=generate_params.min_length,
                temperature=generate_params.temperature,
                top_k=generate_params.top_k,
                top_p=generate_params.top_p,
                do_sample=True,
                num_return_sequences=1,
                # length_penalty=1.0,
                # no_repeat_ngram_size=2,
                repetition_penalty=generate_params.repetition_penalty,
                output_scores=True,
                stopping_criteria=StoppingCriteriaList(stopping_criteria_list),
                # handle_long_generation='hole', # todo fix long sequence generation, this fails fast
                clean_up_tokenization_spaces=True,
                use_cache=True,
                return_dict_in_generate=True,
                # typical_p=.1,
            )
            result = output[0] or {}
            result["stop_reason"] = get_stop_reason()
        results.append(result)
        # logger.info(result)

    decoded_results = [result["generated_text"] for result in results]
    # decoded_results = post_process_results_fix_bad_starting_bug(
    #     decoded_results, initial_valid_tokens, input_text, original_input_text, tokenizer
    # )

    proccesed_results = post_process_results(decoded_results, generate_params, input_text, original_input_text)
    ## count the amount of bytes taken by the decoded proccesed_results
    byte_count = 0
    for result in proccesed_results:
        byte_count += len(result)
    logger.info(f"Byte count: {byte_count}")
    # TODO  save to database

    final_results = []
    for result, processed_result in zip(results, proccesed_results):
        result["generated_text"] = starting_ignored_prefix + processed_result
        final_results.append(result)
    return final_results


# loading = False

# compilation
# import torch._dynamo
# torch._dynamo.config.suppress_errors = True # try its best to compile even if it fails


def load_pipelines_and_model(weights_path):
    global weights_to_model
    global weights_to_generator
    global weights_to_tokenizer
    if DEVICE == "tpu":
        xm.xla_device()
    model = weights_to_model.get(weights_path)
    tokenizer = weights_to_tokenizer.get(weights_path)
    if not model:
        tokenizer, model = load_model(weights_path)
        # dontneed to compile
        # model = torch.compile(model)
    # sometimes we already have the model and it may have been swapped out so ensure its on the device
    model.to(DEVICE)
    del weights_to_model[weights_path]
    del weights_to_generator[weights_path]
    del weights_to_tokenizer[weights_path]
    # gc? todo do we neeed to redo the generator? if its there?

    weights_to_model[weights_path] = model
    weights_to_generator[weights_path] = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,  # device=pipeline_device
    )
    # move pipeline to gpu
    # weights_to_generator[weights_path].to(DEVICE)
    weights_to_tokenizer[weights_path] = tokenizer
    # feature_extractor = pipeline(
    #     "feature-extraction", model=model, tokenizer=tokenizer, device=pipeline_device
    # )
    # loading = True
    return model


tg_avg_pplx = 35.194010416666664
tgz_avg_pplx = 56.034505208333336
current_model_loaded_name = "tgz"
model_name_to_avg_pplx = {
    "tgz": 56.034505208333336,
    "tg": 35.194010416666664,
}


def is_nan_or_inf(number):
    return math.isnan(number) or math.isinf(number)


def ensure_best_model_loaded(generate_params, model_cache) -> str:
    global current_model_loaded_name
    global weights_to_model
    global weights_to_tokenizer
    """
    picks the highest perplexity model to be loaded if the text falls below that models average pplx
    """
    instruct_model = weights_to_model.get(weights_path_tgz)
    tokenizer = weights_to_tokenizer.get(weights_path_tgz)
    instruct_perplexity = get_perplexity(instruct_model, tokenizer, generate_params.text, 50000)
    model_current_avg = model_name_to_avg_pplx[current_model_loaded_name]
    if instruct_perplexity < model_current_avg:
        # this model is okay to go on this string
        logger.info("using instruct model, better than avg")
        return weights_path_tgz
    # load other tg model if the first one isn't good enough
    weights_to_model[weights_path_tg] = model_cache.add_or_get(
        "tg_text_model", lambda: load_pipelines_and_model(weights_path_tg)
    )
    tg_model = weights_to_model[weights_path_tg]
    new_perplexity = get_perplexity(tg_model, tokenizer, generate_params.text, 50000)
    # tg does best on really unusual inputs
    if is_nan_or_inf(new_perplexity) or is_nan_or_inf(instruct_perplexity):
        logger.info("using tg for nan or inf perplexity string")
        return weights_path_tg
    new_model_current_avg = model_name_to_avg_pplx["tg"]
    new_model_pplx_score = new_perplexity - new_model_current_avg  # todo divide by std
    logger.info(new_perplexity)
    current_model_pplx_score = instruct_perplexity - model_current_avg
    logger.info(instruct_perplexity)
    if current_model_pplx_score <= new_model_pplx_score:
        # current model was better anyway
        logger.info("using instruct model, better than other model")
        weights_to_model[weights_path_tgz] = model_cache.add_or_get(
            "text_model", lambda: load_pipelines_and_model(weights_path_tgz)
        )
        return weights_path_tgz
    else:
        logger.info("using tg model")
        return weights_path_tg


# ttl cache with 10min expiration
prefix_cache = TTLCache(maxsize=10000, ttl=600)


def fast_inference(generate_params: GenerateParams, model_cache=None):
    with torch.no_grad():
        with log_time("inference"):
            best_weights_path = weights_path_tgz
            if model_cache is not None:
                prefix = generate_params.text[:6]
                best_weights_path = prefix_cache.get(prefix)
                if generate_params.min_probability is not None and generate_params.min_probability > 0.05:
                    # if the min probability is less than 50% we want to use the non instruct model for autocomplete allways
                    best_weights_path = weights_path_tg
                # if generate_params.model == "chat":
                #     # chat is always tgc model
                #     best_weights_path = weights_path_tgc
                #     # unload all the other models?
                #     weights_to_model[weights_path_tgz] = None
                #     weights_to_model[weights_path_tg] = None
                #     weights_to_generator[weights_path_tgz] = None
                #     weights_to_generator[weights_path_tg] = None
                if generate_params.model == "chat":  # tmp fix tmp issues with chat model
                    generate_params.model = "multilingual"
                if (
                    generate_params.model == "any"
                    or generate_params.model == "fastest"
                    or generate_params.model == "best"
                ):
                    # any is allways what's loaded in memory to be the fastest
                    if model_cache.most_recent_name:
                        best_weights_path = name_key_to_weights.get(model_cache.most_recent_name, weights_path_tgz)
                    else:
                        best_weights_path = weights_path_tg
                if generate_params.model == "instruct":
                    # instruct is always tgz model
                    best_weights_path = weights_path_tgz
                if generate_params.model == "multilingual":
                    # multilingual is always tg model
                    best_weights_path = weights_path_tg
                if best_weights_path:
                    # model cache hit
                    model_name_key = weights_to_name_key.get(best_weights_path, "tg_text_model")
                    weights_to_model[best_weights_path] = model_cache.add_or_get(
                        model_name_key, lambda: load_pipelines_and_model(best_weights_path)
                    )
                    return inference(generate_params, best_weights_path, model_cache)

                # load tgz
                weights_to_model[weights_path_tgz] = model_cache.add_or_get(
                    "text_model", lambda: load_pipelines_and_model(weights_path_tgz)
                )
                logger.info("loaded main model")
                # daemon.join()

                # test pplx to see if it should fallback to non instruct models
                with log_time("ensure best model loaded:"):
                    best_weights_path = ensure_best_model_loaded(generate_params, model_cache)
                    prefix_cache[prefix] = best_weights_path

            return inference(generate_params, best_weights_path)


def fast_feature_extract_inference(feature_extract_params: FeatureExtractParams, model_cache):
    with torch.inference_mode():
        with log_time("feature extract inference"):
            return run_feature_extractor(feature_extract_params, model_cache)

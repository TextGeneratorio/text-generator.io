import math
from typing import List

from nltk import sent_tokenize
from loguru import logger

from questions.models import GenerateParams
from questions.fixtures import set_stop_reason, get_stop_reason
from questions.post_process_results import post_process_results
from questions.constants import weights_path_tgz
from questions.utils import log_time
from questions.inference_server.model_cache import ModelCache

try:
    from vllm import LLM, SamplingParams
    VLLM_AVAILABLE = True
except Exception:  # pragma: no cover - vllm may not be installed
    LLM = None
    SamplingParams = None
    VLLM_AVAILABLE = False


def load_vllm_model(model_path: str = weights_path_tgz):
    if not VLLM_AVAILABLE:
        raise RuntimeError("vllm is not installed")
    return LLM(model=model_path)


def _apply_custom_stop(text: str, logprobs: List[float], generate_params: GenerateParams) -> str:
    """Apply custom stopping conditions on generated text."""
    cumulative_prob = 1.0
    output = ""
    for token_text, logprob in zip(text.split(), logprobs):
        output += token_text + " "
        if generate_params.min_probability and logprob is not None:
            cumulative_prob *= math.exp(logprob)
            if cumulative_prob < generate_params.min_probability:
                set_stop_reason("min_probability")
                return output.strip()
        if generate_params.max_sentences:
            if len(sent_tokenize(output)) > generate_params.max_sentences:
                set_stop_reason("max_sentences")
                return output.strip()
    return output.strip()


def fast_vllm_inference(generate_params: GenerateParams, model_cache: ModelCache = None):
    """Run inference with vLLM and apply custom stopping criteria."""
    if not VLLM_AVAILABLE:
        raise RuntimeError("vllm is not installed")

    llm = None
    if model_cache is not None:
        llm = model_cache.add_or_get("vllm_model", lambda: load_vllm_model())
    else:
        llm = load_vllm_model()

    sampling_params = SamplingParams(
        temperature=generate_params.temperature,
        top_p=generate_params.top_p,
        top_k=generate_params.top_k,
        max_tokens=generate_params.max_length,
        stop=generate_params.stop_sequences or None,
        repetition_penalty=generate_params.repetition_penalty,
    )

    with log_time("vllm_generate"):
        outputs = llm.generate([generate_params.text], sampling_params)

    results = []
    for output in outputs:
        candidate = output.outputs[0]
        generated = _apply_custom_stop(candidate.text, candidate.logprobs, generate_params)
        full_text = generate_params.text + generated
        results.append({"generated_text": full_text, "stop_reason": get_stop_reason()})

    processed = post_process_results(
        [r["generated_text"] for r in results],
        generate_params,
        generate_params.text,
        generate_params.text,
    )

    final = []
    for result, processed_text in zip(results, processed):
        result["generated_text"] = processed_text
        final.append(result)
    return final

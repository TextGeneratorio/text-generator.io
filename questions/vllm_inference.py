import math
from typing import List

try:
    from vllm import LLM, SamplingParams
    from vllm.utils import logits_to_probs
    VLLM_AVAILABLE = True
except Exception:
    from typing import Any
    LLM = Any  # type: ignore
    SamplingParams = Any  # type: ignore
    logits_to_probs = None  # type: ignore
    VLLM_AVAILABLE = False

from nltk.tokenize import sent_tokenize

from questions.models import GenerateParams
from questions.fixtures import set_stop_reason

VLLM_MODEL = None


def load_vllm(model_path: str):
    global VLLM_MODEL
    if VLLM_MODEL is None:
        if not VLLM_AVAILABLE:
            raise RuntimeError("vLLM is not installed")
        VLLM_MODEL = LLM(model=model_path, dtype="auto")
    return VLLM_MODEL


def vllm_inference(generate_params: GenerateParams, model_path: str) -> List[dict]:
    if not VLLM_AVAILABLE:
        raise RuntimeError("vLLM is not installed")
    llm = load_vllm(model_path)

    sampling_params = SamplingParams(
        n=generate_params.number_of_results,
        temperature=generate_params.temperature,
        top_p=generate_params.top_p,
        top_k=generate_params.top_k,
        max_tokens=generate_params.max_length,
        stop=generate_params.stop_sequences,
        logprobs=1,
    )

    results = []
    outputs = llm.generate([generate_params.text], sampling_params)
    output = outputs[0]
    for seq in output.outputs:
        text = seq.text
        logprobs = seq.logprobs or []
        stop_reason = "max_length"

        if generate_params.min_probability:
            cumulative = 1.0
            cut_idx = None
            for i, lp in enumerate(logprobs):
                cumulative *= math.exp(lp)
                if cumulative < generate_params.min_probability:
                    cut_idx = i
                    stop_reason = "min_probability"
                    break
            if cut_idx is not None:
                words = text.split()
                text = " ".join(words[: cut_idx + 1])

        if generate_params.max_sentences:
            sentences = sent_tokenize(text)
            if len(sentences) > generate_params.max_sentences:
                text = " ".join(sentences[: generate_params.max_sentences])
                stop_reason = "max_sentences"

        results.append({"generated_text": text, "stop_reason": stop_reason})
    return results

import traceback

import vertexai
from loguru import logger
from vertexai.preview.language_models import TextGenerationModel
from vertexai.preview.language_models import ChatModel, InputOutputTextPair

#  pip install google-cloud-aiplatform
# not done yet as this isn't in prod?
from questions.extrautils.cache import cache
from questions.nlp_utils import replace_bad_words, replace_good_words, dirty_context

from questions.utils import log_time

project_id = "netwrck"
location = "us-central1"
vertexai.init(project=project_id, location=location)

# ## timeout 6s
# timeout = 6
# # set timeout
# vertexai.set_timeout(timeout)
model_name = "text-bison@001"
model = TextGenerationModel.from_pretrained(model_name)


# if tuned_model_name:
#     model = model.get_tuned_model(tuned_model_name)
def predict_large_language_model_sample(
    temperature: float,
    max_decode_steps: int,
    top_p: float,
    top_k: int,
    content: str,
):
    """Predict using a Large Language Model."""
    response = model.predict(
        content,
        temperature=temperature,
        max_output_tokens=max_decode_steps,
        top_k=top_k,
        top_p=top_p,
    )
    return response.text


@cache.memoize()
def predict_palm_unsafe(prompt):
    return predict_large_language_model_sample(0.2, 256, 0.8, 40, prompt)


def predict_palm(prompt):
    try:
        with log_time("predict_palm"):
            logger.info(f"palm prompt: {prompt}")
            safeprompt, replaced_map = replace_bad_words(prompt)
            # if replaced_map:
            #     context = dirty_context(context)
            unsafe = predict_palm_unsafe(safeprompt)
            if replaced_map:
                unsafe = replace_good_words(unsafe, replaced_map)
            logger.info(f"palm generated: {unsafe}")

        return unsafe
    except Exception as e:
        logger.error(e)
        traceback.print_exc()
        return ""


def predict_large_language_model_sample_chat(
    prompt: str,
    context: str,
    pairs: list,
    temperature: float,
    max_output_tokens: int,
    top_p: float,
    top_k: int,
):
    """Predict using a Large Language Model."""
    chat_model_name = "chat-bison@001"

    chat_model = ChatModel.from_pretrained(chat_model_name)
    parameters = {
        "temperature": temperature,
        "max_output_tokens": max_output_tokens,
        "top_p": top_p,
        "top_k": top_k,
    }

    chat = chat_model.start_chat(context=context, examples=pairs)
    response = chat.send_message(prompt, **parameters)
    return response.text


# pairs = [InputOutputTextPair(
#     input_text='''hey hows it going''',
#     output_text='''doing nothing staying at home all day'''
# )]
# context = '''hey hows it going'''


# predict_large_language_model_sample_chat(prompt, context, pairs, "chat-bison@001", 0.2, 256, 0.8, 40)


@cache.memoize()
def chat_palm_unsafe(prompt, context, pairs):
    return predict_large_language_model_sample_chat(prompt, context, pairs, 0.2, 256, 0.8, 40)


def chat_palm(prompt, context, pairs):
    try:
        with log_time("chat_palm"):
            logger.info(f"palm prompt: {prompt}")
            # replace context with safe words
            total_replacement_map = {}
            safecontext, context_replaced_map = replace_bad_words(context)
            # replace all pairs
            for pair in pairs:
                safeprompt, replaced_map = replace_bad_words(pair.input_text)
                pair.input_text = safeprompt
                total_replacement_map.update(replaced_map)
                safeprompt, replaced_map = replace_bad_words(pair.output_text)
                pair.output_text = safeprompt
                total_replacement_map.update(replaced_map)
            total_replacement_map.update(context_replaced_map)
            safeprompt, replaced_map = replace_bad_words(prompt)
            total_replacement_map.update(replaced_map)
            if total_replacement_map:
                context = dirty_context(safecontext)
                total_replacement_map['desire'] = 'intimacy'
                total_replacement_map['sexually'] = 'intimately'
            unsafe = chat_palm_unsafe(safeprompt, context, pairs)
            if total_replacement_map:
                unsafe = replace_good_words(unsafe, total_replacement_map)
            logger.info(f"palm generated: {unsafe}")

        return unsafe
    except Exception as e:
        logger.error(e)
        return ""


def get_input_output_pairs(pairs):
    if not pairs:
        return []

    io_pairs = []
    if len(pairs) % 2 != 0:
        pairs = pairs[:-1]
    # return JSONResponse({"error": "examples must be even"})
    for i in range(0, len(pairs), 2):
        io_pairs.append(
            InputOutputTextPair(
                input_text=pairs[i],
                output_text=pairs[i + 1],
            )
        )
    return io_pairs

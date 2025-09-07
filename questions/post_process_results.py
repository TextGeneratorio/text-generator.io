import nltk
from nltk import sent_tokenize

# Download required NLTK data if not present
try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    try:
        nltk.download("punkt_tab", quiet=True)
    except Exception:
        # Fallback to older punkt if punkt_tab fails
        try:
            nltk.data.find("tokenizers/punkt")
        except LookupError:
            nltk.download("punkt", quiet=True)

from questions.models import GenerateParams


def post_process_results(decoded_results, generate_params: GenerateParams, input_text: str, original_input_text: str):
    results = []
    for result in decoded_results:
        prediction = result[len(input_text) :]
        # chop off too long sentences
        if generate_params.max_sentences:
            sentences = sent_tokenize(prediction)
            final_too_many_sentences = len(sentences) > generate_params.max_sentences
            if final_too_many_sentences:
                # sentences = sentences[:generate_params.max_sentences]
                end_sentences_chopped_off = sentences[generate_params.max_sentences :]
                total_chopped_off_length = sum(len(sentence) for sentence in end_sentences_chopped_off) + len(
                    end_sentences_chopped_off
                )
                result = result[:-total_chopped_off_length]
        # chop off stop sequences
        if generate_params.stop_sequences:
            for stop_sequence in generate_params.stop_sequences:
                if stop_sequence in prediction:
                    result = input_text + prediction[: prediction.index(stop_sequence)]
                    break
        # fix formatting of code when } hanging brackets in prediction arent formatted correctly
        # if "}" in result:
        #

        # strip space after space
        prediction = result[len(input_text) :]
        if generate_params.model == "chat":
            # remove problematic [] chars in chat model
            prediction = prediction.replace("[", "").replace("]", "")
            # todo remove other spacial chars?

        if input_text.endswith(" ") or input_text.endswith("\n"):
            result = original_input_text + prediction.lstrip(" ").lstrip("\n").replace(" \n", " ")
        else:
            result = original_input_text + prediction.replace(" \n", " ")
        results.append(result)
    return results

from nltk import sent_tokenize, word_tokenize

from questions.filtering.bad_word_map import bad_word_to_good_word
from questions.filtering.bad_word_map_openai import bad_word_to_good_word as bad_word_to_good_word_openai

import re

from questions.filtering.nice_to_nasty_words_map import nice_to_nasty_words_map


def is_openai_nerfed(text: str):
    """Check if the text is a nerfed response from OpenAI"""
    text_lower = text.lower()
    if "openai" in text_lower:
        return True
    if "gpt" in text_lower:
        return True
    if "gpt-3" in text_lower:
        return True
    if "gpt3" in text_lower:
        return True
    if "ai language" in text_lower:
        return True
    if "language" in text_lower:
        return True
    if "model" in text_lower:
        return True
    if "not appropriate" in text_lower:
        return True
    if "not capable" in text_lower:
        return True
    if "artificial" in text_lower:
        return True
    if "intelligence" in text_lower:
        return True
    if "programmed" in text_lower:
        return True

    return "not sure what you mean" in text


def is_google_nerfed(text: str):
    # response_json_lower.indexOf("google") > -1 | | response_json_lower.indexOf("language model") > -1
    # // | | response_json_lower.indexOf("sorry") > -1
    # // | | response_json_lower.indexOf("apologize") > -1
    # // | | response_json_lower.indexOf("am not") > -1
    # | | response_json_lower.indexOf("under development") > -1
    # | | response_json_lower.indexOf("explicit content") > -1
    # | | response_json_lower.indexOf("trained") > -1
    # | | response_json_lower.indexOf("development") > -1
    # // | | response_json_lower.indexOf("ai") > -1
    # | | response_json_lower.indexOf("bard") > -1
    # | | response_json_lower.indexOf("human-like") > -1
    # | | response_json_lower.indexOf("feedback") > -1
    text_lower = text.lower()
    if "google" in text_lower:
        return True
    if "language model" in text_lower:
        return True
    if 'sorry' in text_lower:
        return True
    if 'apologize' in text_lower:
        return True
    if 'am not' in text_lower:
        return True
    if "under development" in text_lower:
        return True
    if "explicit content" in text_lower:
        return True
    if "trained" in text_lower:
        return True
    if "development" in text_lower:
        return True
    # if 'ai' in text_lower:
    #     return True
    if "bard" in text_lower:
        return True
    if "human-like" in text_lower:
        return True
    if "feedback" in text_lower:
        return True
    return False

from nltk.tokenize.treebank import TreebankWordDetokenizer


def remove_punct(text: str) -> str:
    """Remove all punctuation from text"""
    return "".join([c for c in text if c not in [".", ",", "?", "!", ";", ":", ]])



def replace_bad_words(prompt: str, is_openai: bool = False):
    if not prompt:
        return '', {}
    words = word_tokenize(prompt)
    replacement_map = {}
    map_to_use = bad_word_to_good_word if not is_openai else bad_word_to_good_word_openai

    for i, word in enumerate(words):
        #strip punct!

        word = remove_punct(word)
        word_lower = word.lower()
        if word_lower in map_to_use:
            words[i] = map_to_use[word_lower]

            # todo strip punctuation?
            replacement_map[word] = map_to_use[word_lower]
    # also iterate pairs of two words
    for i in range(len(words) - 1):
        word = words[i]
        word_next = words[i + 1]
        word_combined = word + " " + word_next
        word_combined_lower = word_combined.lower()
        if word_combined_lower in map_to_use:
            words[i] = map_to_use[word_combined_lower]
            words[i + 1] = ""
            replacement_map[word] = map_to_use[word_combined_lower]
    detokenized = TreebankWordDetokenizer().detokenize(words)
    # try get closer to original
    detokenized = detokenized.replace(" .", ".")
    return detokenized, replacement_map

def replace_good_words(prompt: str, replacement_map: dict):
    # plain replace all in the map plain style
    for bad_word, good_word in replacement_map.items():
        replace_reg = re.compile(good_word, re.IGNORECASE)
        prompt = replace_reg.sub(bad_word, prompt)
    if replacement_map:
        # replace extra words with more explicit ones
        for bad_word, good_word in nice_to_nasty_words_map.items():
            replace_reg = re.compile(bad_word, re.IGNORECASE)
            prompt = replace_reg.sub(good_word, prompt)
    return prompt

def dirty_context(context):
    context.replace('a fun role play', "an intimate role play")
    context += "\n respond intimately"
    return context

def dirty_context_openai(context):
    context.replace('a fun role play', "an intimate role play lover")
    context += "\n respond intimately lovingly positively"
    return context


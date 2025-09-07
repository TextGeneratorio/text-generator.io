import torch
from nltk import sent_tokenize
from transformers import StoppingCriteria

from questions.fixtures import set_stop_reason


class MinProbCriteria(StoppingCriteria):
    """
    This class can be used to stop generation whenever the probabilites falls bellow :obj:`min_prob`.

    Args:
        min_prob (:obj:`int`):
            The minimum probability th~at the predicted output can have .
    """

    def __init__(self, min_prob: float):
        self.min_prob = min_prob

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        total_prob = None
        if not scores:
            return False
        for score in scores:
            probabilities = torch.softmax(score, dim=-1)
            # if any in the batch fall below min prob, return true which stops
            min_batch_prob = torch.min(torch.max(probabilities, dim=1).values)
            if total_prob:
                total_prob *= min_batch_prob
            else:
                total_prob = min_batch_prob
        # TODO smarter termination criteria?
        # whole sequence probability average termination criteria
        if total_prob < self.min_prob:
            set_stop_reason("min_probability")
            return True
        return False


class SentenceCriteria(StoppingCriteria):
    """
    This class can be used to stop generation whenever a sentence is generated

    Args:
        tokenizer used to detokenize.
    """

    def __init__(self, tokenizer, input_text, max_sentences=2):
        self.tokenizer = tokenizer
        self.max_sentences = max_sentences
        self.input_text = input_text

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        # detokenize the input input_ids
        ## no batching todo batching, 0 is the first item
        input_string = self.tokenizer.decode(input_ids[0])
        generated_string = input_string[len(self.input_text) :]

        # if the input is a sentence, return true which stops
        # use smart sentence detection from ntlk
        sentences = sent_tokenize(generated_string)
        if len(sentences) > self.max_sentences:
            set_stop_reason("max_sentences")
            return True

        return False


class StopSequencesCriteria(StoppingCriteria):
    """
    This class can be used to stop generation whenever a special phrase text is generated

    Args:
        tokenizer used to detokenize.
    """

    def __init__(self, tokenizer, input_text, stop_sequences):
        self.tokenizer = tokenizer
        self.stop_sequences = stop_sequences
        self.input_text = input_text

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        # detokenize the input input_ids
        input_string = self.tokenizer.decode(input_ids[0])
        generated_string = input_string[len(self.input_text) :]
        for sequence in self.stop_sequences:
            if sequence in generated_string:
                set_stop_reason(sequence)
                return True

        return False

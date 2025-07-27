import torch
from tqdm import tqdm

from questions.utils import log_time

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def get_perplexity(model, tokenizer, text, stride=512):
    """
    Get perplexity of a text using a model and tokenizer
    use a large stride to avoid doing too much computation
    """
    with torch.no_grad():
        with log_time("get_perplexity"):
            input_ids = tokenizer.encode(text, return_tensors="pt").to(DEVICE)
            max_length = 512 # model.config.n_positions is not set for bloom models only gpt2
            seq_len = input_ids.size(1)

            nlls = []
            prev_end_loc = 0
            for begin_loc in tqdm(range(0, seq_len, stride)):
                end_loc = min(begin_loc + max_length, seq_len)
                trg_len = end_loc - prev_end_loc  # may be different from stride on last loop
                input_ids = input_ids[:, begin_loc:end_loc].to(DEVICE)
                target_ids = input_ids.clone().to(DEVICE)
                target_ids[:, :-trg_len] = -100

                outputs = model(input_ids, labels=target_ids)

                # loss is calculated using CrossEntropyLoss which averages over input tokens.
                # Multiply it with trg_len to get the summation instead of average.
                # We will take average over all the tokens to get the true average
                # in the last step of this example.
                neg_log_likelihood = outputs.loss * trg_len

                nlls.append(neg_log_likelihood)

                prev_end_loc = end_loc
                if end_loc == seq_len:
                    break

            ppl = torch.exp(torch.stack(nlls).sum() / end_loc)
            return ppl.item()


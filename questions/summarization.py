import torch
import nltk
from nltk import sent_tokenize

# Download required NLTK data if not present
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    try:
        nltk.download('punkt_tab', quiet=True)
    except Exception:
        # Fallback to older punkt if punkt_tab fails
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)

from transformers import pipeline
import logging
from questions.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

from questions.inference_server.model_cache import DEVICE
from questions.utils import log_time

summarizer = None
def load_summarizer():
    global summarizer
    logger.info("Loading summarizer")
    if not summarizer:
        summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6", device=0 if DEVICE == 'cuda' else -1)
    # eval
    summarizer.model.eval()
    if DEVICE == "cuda":
        with log_time("summarizer to cuda"):
            summarizer.model.to(DEVICE)
        with log_time("summarizer to bf16"):
            summarizer.model = summarizer.model.bfloat16()

        # with log_time("bert to gpu"):
        #     distilbert.to(DEVICE)
    # elif DEVICE == "cpu":
    #     logger.error("no GPU available, performance may be very slow")
    #     logger.error("consider using a GPU or many fast CPUs if you need to do this")
    #     summarizer.model.to(DEVICE)
    logger.info("Loaded summarizer")
    return summarizer.model, summarizer
# classification = summarizer("James Joseph Norton  is an American comedian, radio personality, actor, author, and television and podcast host. Norton has been the co-host of the podcast UFC Unfiltered with Matt Serra and the morning radio show Jim Norton & Sam Roberts on SiriusXM Radio since 2016, and The Chip Chipperson Podacast since 2017. He gained initial prominence as third mic on the radio show Opie and Anthony, with Gregg \"Opie\" Hughes and Anthony Cumia, from 2001 to 2014. After becoming a stand-up comedian in 1990, Norton spent his early years developing his act. His appearances on The Louie Show caught the attention of comedian Andrew Dice Clay in 1997, who chose Norton to open for him for his shows. In 2000, Norton made his debut on Opie and Anthony and joined the show as a third mic in 2001 which increased his national exposure. He went on to have a recurring role on the sitcom Lucky Louie and featured as a regular panellist on Tough Crowd with Colin Quinn. Since he joined SiriusXM with Opie and Anthony in 2004, Norton hosted Opie with Jim Norton from 2014 to 2016, and The Jim Norton Advice Show. Since 2003, Norton has released four comedy albums and seven comedy specials, including three on Epix and one on Netflix. In 2014, Norton hosted The Jim Norton Show, a talk show on Vice.")

# print(classification[0]['summary_text'].strip().replace(" .", "."))
# classification = summarizer("Paris is the capital and most populous city of France, with an estimated population of 2,175,601 residents as of 2018, in an area of more than 105 square kilometres (41 square miles). The City of Paris is the centre and seat of government of the region and province of Île-de-France, or Paris Region, which has an estimated population of 12,174,880, or about 18 percent of the population of France as of 2017.")
# print(classification)
## [{ "summary_text": " Paris is the capital and most populous city of France..." }]


def get_extractive_summary(text: str, model_cache, max_length: int=0, retries=4) -> str:
    """
    Summarize a text using extractive summarization
    try not generate longer than max_length text
    """
    # if there are over 3k lines, middle out the lines?
    if len(text.split()) > 3000:
        lines = text.split("\n")
        # text should be first 1k and last 2k lines
        text = "\n".join(lines[:1000] + lines[-2000:])
    summarizer_model, summarizer = model_cache.add_or_get("summarizer", load_summarizer)
    return get_extractive_summary_inner(summarizer, text, max_length, retries)

def get_extractive_summary_inner(summarizer, text: str, max_length: int = 0, retries=4) -> str:
    text = text.strip()[0:2048 * 100] # max cap on length
    # global summarizer
    # if not summarizer:
    #     load_summarizer()
    with torch.inference_mode():
        # chunk into N sentences then if 1 doesnt fit then further into chunks of 1024 tokens
        sentences = sent_tokenize(text)
        max_len = 2048 # todo make sure this is actually under the token size?
        chunks = []
        chunk = ""
        for sentence in sentences:
            if len(chunk) + len(sentence) < max_len:
                chunk += sentence
            else:
                chunks.append(chunk)
                chunk = sentence
        chunks.append(chunk)
        summaries = []
        # for chunk in chunks:
        #     try:
        #         summary = summarizer(chunk)[0]['summary_text'].strip().replace(" .", ".")
        #     except Exception as e:
        #         # logger.error(f"Error summarizing chunk: {chunk}")
        #         logger.error(e)
        #         continue
        #     summaries.append(summary)

        # batched execution up to 30 in a batch - this is fairly aggressive?
        batch_size = 10
        all_summaries = []
        for i in range(0, len(chunks), batch_size):
            # current_chunks = chunks[i:i + batch_size]
            # try:
            #     summaries = summarizer(current_chunks)
            #     summaries = [summary['summary_text'].strip().replace(" .", ".") for summary in summaries]
            #     # ensure each summary is smaller than the current chunk
            #     small_summaries = []
            #     for chunk, summary in zip(current_chunks, summaries):
            #         if len(summary) < len(chunk):
            #             small_summaries.append(summary)
            #         else:
            #             # logger.error(f"Summary is too long: {len(summary)} > {len(chunk)}")
            #             small_summaries.append(chunk)
            #     all_summaries.extend(small_summaries)
            # except Exception as e:
            #     logger.error(e)
                # fallback to slow iteration?
            for chunk in chunks:
                try:
                    summary = summarizer(chunk)[0]['summary_text'].strip().replace(" .", ".")
                except Exception as e:
                    # logger.error(f"Error summarizing chunk: {chunk}")
                    logger.error(e)
                    continue
                # ensure each summary is smaller than the current chunk
                if len(summary) < len(chunk):
                    small_summary = summary
                else:
                    # logger.error(f"Summary is too long: {len(summary)} > {len(chunk)}")
                    small_summary = chunk
                summaries.append(small_summary)


        # remove all duplicates - maintain ordering
        summaries = list(dict.fromkeys(summaries))
        final_summary = "\n".join(summaries)
        if max_length > 0 and len(final_summary) > max_length:
            # logger.info(f"Generated summary is too long: {len(final_summary)} > {max_length}")
            # try again with a smaller max_length
            if retries > 0:
                return get_extractive_summary_inner(summarizer, text, max_length=max_length, retries=retries - 1)
        return final_summary

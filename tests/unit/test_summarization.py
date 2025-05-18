from questions.inference_server.inference_server import MODEL_CACHE
from questions.summarization import get_extractive_summary
from questions.utils import log_time

text = """
    # classification = summarizer("James Joseph Norton  is an American comedian, radio personality, actor, author, and television and podcast host. Norton has been the co-host of the podcast UFC Unfiltered with Matt Serra and the morning radio show Jim Norton & Sam Roberts on SiriusXM Radio since 2016, and The Chip Chipperson Podacast since 2017. He gained initial prominence as third mic on the radio show Opie and Anthony, with Gregg \"Opie\" Hughes and Anthony Cumia, from 2001 to 2014. After becoming a stand-up comedian in 1990, Norton spent his early years developing his act. His appearances on The Louie Show caught the attention of comedian Andrew Dice Clay in 1997, who chose Norton to open for him for his shows. In 2000, Norton made his debut on Opie and Anthony and joined the show as a third mic in 2001 which increased his national exposure. He went on to have a recurring role on the sitcom Lucky Louie and featured as a regular panellist on Tough Crowd with Colin Quinn. Since he joined SiriusXM with Opie and Anthony in 2004, Norton hosted Opie with Jim Norton from 2014 to 2016, and The Jim Norton Advice Show. Since 2003, Norton has released four comedy albums and seven comedy specials, including three on Epix and one on Netflix. In 2014, Norton hosted The Jim Norton Show, a talk show on Vice.")

# print(classification[0]['summary_text'].strip().replace(" .", "."))
# classification = summarizer("Paris is the capital and most populous city of France, with an estimated population of 2,175,601 residents as of 2018, in an area of more than 105 square kilometres (41 square miles). The City of Paris is the centre and seat of government of the region and province of Île-de-France, or Paris Region, which has an estimated population of 12,174,880, or about 18 percent of the population of France as of 2017.")
# print(classification)
## [{ "summary_text": " Paris is the capital and most populous city of France..." }]

"""


def test_summarization():
    summary = get_extractive_summary(text, MODEL_CACHE)
    assert summary.strip() != ""

    with log_time("inf time"):
        summary2 = get_extractive_summary(text, MODEL_CACHE)
    assert summary2.strip() != ""

    # print(get_extractive_summary(text *
    #                              45, MODEL_CACHE))


def test_summarization_max_length():
    summary = get_extractive_summary(text *
                                     145, MODEL_CACHE, max_length=1024)
    assert summary.strip() != ""
    assert len(summary) <= 1024

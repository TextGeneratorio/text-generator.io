from transformers import GPT2LMHeadModel, GPT2Tokenizer, GPT2TokenizerFast, BloomTokenizerFast, BloomForCausalLM
import logging
from questions.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

import torch

from questions.perplexity import get_perplexity

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

texts = """
I have several masked language models (mainly Bert, Roberta, Albert, Electra). I also have a dataset of sentences. How can I get the perplexity of each sentence?

From the huggingface documentation here they mentioned that perplexity "is not well defined for masked language models like BERT", though I still see people somehow calculate it.

For example in this SO question they calculated it using the function

def score(model, tokenizer, sentence,  mask_token_id=103):
  tensor_input = tokenizer.encode(sentence, return_tensors='pt')
  repeat_input = tensor_input.repeat(tensor_input.size(-1)-2, 1)
  mask = torch.ones(tensor_input.size(-1) - 1).diag(1)[:-2]
  masked_input = repeat_input.masked_fill(mask == 1, 103)
  labels = repeat_input.masked_fill( masked_input != 103, -100)
  loss,_ = model(masked_input, masked_lm_labels=labels)
  result = np.exp(loss.item())
  return result

score(model, tokenizer, '我爱你') # returns 45.63794545581973
However, when I try to use the code I get TypeError: forward() got an unexpected keyword argument 'masked_lm_labels'.

I tried it with a couple of my models:

from transformers import pipeline, BertForMaskedLM, BertForMaskedLM, AutoTokenizer, RobertaForMaskedLM, AlbertForMaskedLM, ElectraForMaskedLM
import torch

1)
tokenizer = AutoTokenizer.from_pretrained("bioformers/bioformer-cased-v1.0")
model = BertForMaskedLM.from_pretrained("bioformers/bioformer-cased-v1.0")
2)
tokenizer = AutoTokenizer.from_pretrained("sultan/BioM-ELECTRA-Large-Generator")
model = ElectraForMaskedLM.from_pretrained("sultan/BioM-ELECTRA-Large-Generator")
This SO question also used the masked_lm_labels as an input and it seemed to work somehow.

nlppytorchhuggingface-transformersbert-language-modeltransformer-model
Share
Improve this question
Follow
asked Dec 23, 2021 at 15:50
Penguin's user avatar
Penguin
1,41022 gold badges1313 silver badges3535 bronze badges
Add a comment
1 Answer
Sorted by:

Highest score (default)

9


There is a paper Masked Language Model Scoring that explores pseudo-perplexity from masked language models and shows that pseudo-perplexity, while not being theoretically well justified, still performs well for comparing "naturalness" of texts.

As for the code, your snippet is perfectly correct but for one detail: in recent implementations of Huggingface BERT, masked_lm_labels are renamed to simply labels, to make interfaces of various models more compatible. I have also replaced the hard-coded 103 with the generic tokenizer.mask_token_id. So the snippet below should work:

from transformers import AutoModelForMaskedLM, AutoTokenizer
import torch
import numpy as np

model_name = 'cointegrated/rubert-tiny'
model = AutoModelForMaskedLM.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

def score(model, tokenizer, sentence):
    tensor_input = tokenizer.encode(sentence, return_tensors='pt')
    repeat_input = tensor_input.repeat(tensor_input.size(-1)-2, 1)
    mask = torch.ones(tensor_input.size(-1) - 1).diag(1)[:-2]
    masked_input = repeat_input.masked_fill(mask == 1, tokenizer.mask_token_id)
    labels = repeat_input.masked_fill( masked_input != tokenizer.mask_token_id, -100)
    with torch.inference_mode():
        loss = model(masked_input, labels=labels).loss
    return np.exp(loss.item())

print(score(sentence='London is the capital of Great Britain.', model=model, tokenizer=tokenizer)) 
# 4.541251105675365
print(score(sentence='London is the capital of South America.', model=model, tokenizer=tokenizer)) 
# 6.162017238332462
You can try this code in Google Colab by running this gist.

Share
Improve this answer
Follow
edited Dec 25, 2021 at 21:51
answered Dec 25, 2021 at 21:46
David Dale's user avatar
David Dale
10.4k3838 silver badges6969 bronze badges
This is great!! Thanks a lot. One question, this method seems to be very slow (I haven't found another one) and takes about 1.5 minutes for each of my sentences in my dataset (they're quite long). Any idea on how to make this faster? I suppose moving it to the GPU will help or somehow load multiple sentences and get multiple scores? Though I'm not too familiar with huggingface and how to do that – 
Penguin
 Dec 26, 2021 at 12:22 
1
To use GPU, call model.cuda() after the model initialization, and replace model(masked_input, labels=labels) with model(masked_input.cuda(), labels=labels.cuda()). This will do the trick. But beware that most BERT-like models do not support texts longer than 512 tokens (~2000 characters), and that long texts eat up lots of GPU memory. And consider investing some time in learning pytorch and specifically the transformers library, because debugging neural networks on GPU requires some experience. – 
David Dale
 Dec 26, 2021 at 13:53
Thanks a lot again!! This cuts it down from 1.5 min to 3 seconds : ) – 
Penguin
 Dec 26, 2021 at 14:49
@DavidDale how does this scale to a set of sentences (say a test set)? Should you take average over perplexity value of individual sentences? or first average the loss value over sentences and then exponentiate? – 
dnivog
 May 27 at 6:19
1
@dnivog the exact aggregation method depends on your goal. Typically, averaging occurs before exponentiation (which corresponds to the geometric average of exponentiated losses). The rationale is that we consider individual sentences as statistically independent, and so their joint probability is the product of their individual probability. Thus, by computing the geometric average of individual perplexities, we in some sense spread this joint probability evenly across sentences. – 
David Dale
 May 27 at 10:39
Show 1 more comment
Your Answer
Sign up or log in
Post as a guest
Name
Email
Required, but never shown

By clicking “Post Your Answer”, you agree to our terms of service, privacy policy and cookie policy

Not the answer you're looking for? Browse other questions tagged nlppytorchhuggingface-transformersbert-language-modeltransformer-model or ask your own question.
.
ਹੇ ਮੈਨੂੰ ਉਮੀਦ ਹੈ ਕਿ ਅਸੀਂ ਮਿਲ ਸਕਦੇ ਹਾਂ
"""


def plot_distribution(perplexities, name):
    import matplotlib.pyplot as plt
    plt.hist(perplexities, bins=500)
    plt.show()
    # save plot
    plt.savefig(f'perplexity_distribution{name.replace("/", "-")}.png')


# def test_get_perplexity():
#     model = BloomForCausalLM.from_pretrained("models/SmolLM-1.7B")
#     # convert to half
#     model.half()

#     model.to(DEVICE)
#     tokenizer = BloomTokenizerFast.from_pretrained("models/SmolLM-1.7B")
#     test_text = "This is a test"
#     perplexity = get_perplexity(model, tokenizer, test_text, stride=51200)
#     logger.info(perplexity)
#     assert perplexity > 0
#     unusual_text = "483kjqkjnsfgu8vsafdkln8y9sfgdsafd"
#     u_perplexity = get_perplexity(model, tokenizer, unusual_text, stride=51200)
#     assert u_perplexity > perplexity
#     logger.info(u_perplexity)

#     # print distribution of perplexity over the texts
#     texts_split = [texts[i:i + 512] for i in range(0, len(texts), 512)]
#     perplexities = [get_perplexity(model, tokenizer, text, stride=51200) for text in texts_split]
#     logger.info(perplexities)
#     # graph the distribution
#     plot_distribution(perplexities, "models/tg-7b1") # gpt2 is 85 distill is 95 bloomz is 99
#     logger.info(f"average perplexity: {sum(perplexities) / len(perplexities)}")

#     # test with a different model.
#     model = BloomForCausalLM.from_pretrained("models/tg-7b1")
#     model.half()
#     model.to(DEVICE)
#     tokenizer = BloomTokenizerFast.from_pretrained("models/tg-7b1")
#     perplexities = [get_perplexity(model, tokenizer, text, stride=51200) for text in texts_split]
#     logger.info(perplexities)
#     # graph the distribution
#     plot_distribution(perplexities, "models/tg-7b1")
#     # log average
#     logger.info(f"average perplexity: {sum(perplexities) / len(perplexities)}")

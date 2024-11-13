from transformers import AutoModel, AutoTokenizer
import torch.nn as nn
import torch

from questions.perplexity import DEVICE
from questions.utils import log_time
from loguru import logger

class FeatureExtractModel(nn.Module):
    def __init__(self, checkpoint, freeze=False, device="cuda"):
        super().__init__()
        with log_time("bert load"):
            self.model = AutoModel.from_pretrained(checkpoint)
        hidden_sz = self.model.config.hidden_size
        # set device cuda or cpu
        self.device = device
        # freeze model
        if freeze:
            for layer in self.model.parameters():
                layer.requires_grad = False

    def forward(self, x, attention_mask=None):

        x = x.to(self.device)
        # pooler_output(seq,dim)
        with torch.no_grad():
            model_out = self.model(x["input_ids"], x["attention_mask"], return_dict=True)

        embds = model_out.last_hidden_state  # model_out[0][:,0]
        mean_pool = embds.sum(axis=1) / x["attention_mask"].sum(axis=1).unsqueeze(axis=1)
        return mean_pool


checkpoint = "models/distilbert-base-uncased"
distilbert = None
def get_distilbert():
    global distilbert
    with log_time("bert load"):
        if not distilbert:
            distilbert = FeatureExtractModel(checkpoint, freeze=True)

    distilbert.eval()
    if DEVICE == "cuda":
        with log_time("bert to bf16"):
            distilbert.bfloat16()

        with log_time("bert to gpu"):
            distilbert.to(DEVICE)
    elif DEVICE == "cpu":
        logger.error("no GPU available, performance may be very slow")
        logger.error("consider using a GPU or many fast CPUs if you need to do this")
        distilbert.to(DEVICE)
    return distilbert

tokenizer = AutoTokenizer.from_pretrained(checkpoint)


final_sentences = [
    "def factorial(n):\n\tif n == 0:\n    \treturn 1\n\treturn factorial(n - 1) * n\n",
    "write a function to return factorial of a number",
    "write a function to print a number twice",
    "def print_twice(x):\n\tprint(x)\n\tprint(x)\n",
    "electrical testing of a switchboard with hand holding a red wire",
    "cat and dog laying on the floor",
    "https://images2.minutemediacdn.com/image/upload/c_fill,w_1080,ar_16:9,f_auto,q_auto,g_auto/shape%2Fcover%2Fsport%2F516438-istock-637689912-981f23c58238ea01a6147d11f4c81765.jpg",
    "https://static.text-generator.io/static/img/Screenshot%20from%202022-09-12%2010-08-50.png",
]


def get_bert_embeddings(sentences, model_cache):
    """
    returns 768 size tensor
    """
    distilbert = model_cache.add_or_get("distilbert", get_distilbert)
    final_embeddings = list()
    all_embeddings = []

    batch_sz = 200  # batch_size
    for idx in range(0, len(sentences), batch_sz):
        batch_sentences = sentences[idx: idx + batch_sz]
        for sent in batch_sentences:
            tokens = tokenizer(
                sent[:511], # can only do 512 tokens - likely can get away with less todo do this cutoff later after tokenization
                truncation="longest_first",
                return_tensors="pt",
                return_attention_mask=True,
                padding=True,
            )
            embeddings = distilbert(tokens)
            final_embeddings.extend(embeddings)
            all_embeddings = torch.stack(final_embeddings)
    return all_embeddings.cpu().float().numpy().tolist()


def get_bert_embeddings_fast(sentences, model_cache):
    with torch.inference_mode():
        with log_time("bert embed"):
            return get_bert_embeddings(sentences, model_cache)


if __name__ == "__main__":
    embeddings = get_bert_embeddings_fast(final_sentences)

    print(embeddings)
    print(embeddings[0])

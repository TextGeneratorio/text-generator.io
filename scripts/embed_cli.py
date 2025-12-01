import sys

from questions.bert_embed import get_bert_embeddings_fast
from questions.inference_server.model_cache import ModelCache


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: embed_cli.py <sentence1> [sentence2 ...]")
        return
    cache = ModelCache()
    embeddings = get_bert_embeddings_fast(sys.argv[1:], cache)
    for emb in embeddings:
        print(emb)


if __name__ == "__main__":
    main()

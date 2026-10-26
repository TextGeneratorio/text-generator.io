from functools import lru_cache
import re
import string
import unicodedata
from typing import Dict, Iterable, List, Optional

import numpy as np
from sklearn.neighbors import NearestNeighbors

from questions import prompt_fixtures


_model = None


class _FallbackSentenceTransformer:
    is_fallback = True
    _dim = 64
    _bigram_offset = 36
    _bigram_dim = _dim - _bigram_offset

    def encode(
        self,
        texts: str | Iterable[str],
        *,
        convert_to_numpy: bool = False,
        normalize_embeddings: bool = False,
    ):
        single_input = isinstance(texts, str)
        items = [texts] if single_input else list(texts)
        vectors = np.array([self._encode_single(item) for item in items], dtype=float)

        if normalize_embeddings:
            vectors = np.array([normalize_embedding(vector) for vector in vectors])

        result = vectors[0] if single_input else vectors
        if convert_to_numpy:
            return result
        return result

    def _encode_single(self, text: str) -> np.ndarray:
        if not text:
            return np.zeros(self._dim, dtype=float)

        normalized = unicodedata.normalize("NFKD", text)
        lowered = normalized.lower()
        vector = np.zeros(self._dim, dtype=float)
        length = max(len(lowered), 1)

        for char in lowered:
            if "a" <= char <= "z":
                vector[ord(char) - ord("a")] += 1.0

        vector[:26] /= length
        vector[26] = sum(char.isdigit() for char in lowered) / length
        vector[27] = sum(char.isspace() for char in lowered) / length
        vector[28] = sum(char in string.punctuation for char in lowered) / length
        vector[29] = sum(unicodedata.category(char).startswith("M") for char in normalized) / length
        vector[30] = sum(char in "aeiou" for char in lowered) / length
        vector[31] = 1.0 if "logo" in lowered else 0.0
        vector[32] = 1.0 if "video" in lowered or "motion" in lowered else 0.0
        vector[33] = 1.0 if "email" in lowered or "brief" in lowered else 0.0
        vector[34] = 1.0 if "photo" in lowered or "portrait" in lowered else 0.0
        vector[35] = min(len(set(lowered.split())), 12) / 12.0

        alnum_chars = [char for char in lowered if char.isalnum()]
        bigram_count = max(len(alnum_chars) - 1, 1)
        for index in range(len(alnum_chars) - 1):
            a, b = alnum_chars[index], alnum_chars[index + 1]
            hashed = (ord(a) * 257 + ord(b)) % self._bigram_dim
            vector[self._bigram_offset + hashed] += 1.0

        vector[self._bigram_offset :] /= bigram_count

        if not np.any(vector):
            vector[0] = 1.0

        return vector


def load_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer

            _model = SentenceTransformer("sentence-transformers/static-retrieval-mrl-en-v1")
        except Exception:
            _model = _FallbackSentenceTransformer()
    return _model


def normalize_embedding(embedding: np.ndarray) -> np.ndarray:
    if not isinstance(embedding, np.ndarray):
        embedding = np.array(embedding)
    norm = np.sqrt(np.sum(embedding * embedding))
    return embedding / norm if norm > 0 else embedding


@lru_cache(maxsize=4096)
def get_embedding(text: str) -> np.ndarray:
    model = load_model()
    embedding = model.encode(text)
    if hasattr(embedding, "numpy"):
        embedding = embedding.numpy()
    elif not isinstance(embedding, np.ndarray):
        embedding = np.array(embedding)
    return normalize_embedding(embedding)


def get_embeddings(texts: List[str]) -> np.ndarray:
    if not texts:
        return np.zeros((0, 1), dtype=float)

    model = load_model()
    try:
        embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        if not isinstance(embeddings, np.ndarray):
            embeddings = np.array(embeddings)
        return embeddings
    except Exception:
        vectors = [get_embedding(text) for text in texts]
        max_dim = max(vector.shape[0] for vector in vectors)
        output = np.zeros((len(vectors), max_dim), dtype=float)
        for index, vector in enumerate(vectors):
            output[index, : vector.shape[0]] = vector
        return output


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


class PromptSearchIndex:
    def __init__(self, prompts: List[Dict[str, object]]):
        self.prompts = prompts
        self._search_docs = [str(prompt["search_text"]) for prompt in prompts]
        self._embeddings = get_embeddings(self._search_docs)
        self._neighbors = None
        if len(self.prompts) > 0:
            self._neighbors = NearestNeighbors(
                n_neighbors=len(self.prompts),
                algorithm="ball_tree",
                metric="euclidean",
            )
            self._neighbors.fit(self._embeddings)

    def _matches_filters(
        self,
        prompt: Dict[str, object],
        *,
        category_slug: Optional[str] = None,
        model_slug: Optional[str] = None,
        prompt_type_slug: Optional[str] = None,
    ) -> bool:
        if category_slug and prompt["category_slug"] != category_slug:
            return False
        if model_slug and prompt["model_slug"] != model_slug:
            return False
        if prompt_type_slug:
            if prompt_type_slug == "free":
                return bool(prompt["is_free"])
            if prompt["modality"] != prompt_type_slug:
                return False
        return True

    def _lexical_bonus(self, query: str, prompt: Dict[str, object]) -> float:
        query_tokens = _tokenize(query)
        if not query_tokens:
            return 0.0

        title = str(prompt["title"]).lower()
        summary = str(prompt["summary"]).lower()
        search_text = str(prompt["search_text"]).lower()
        bonus = 0.0

        overlap = len(query_tokens & _tokenize(search_text))
        bonus += overlap * 0.12

        if query.lower() in title:
            bonus += 0.8
        elif query.lower() in summary:
            bonus += 0.45

        return bonus

    def search(
        self,
        query: str,
        *,
        limit: int = 24,
        category_slug: Optional[str] = None,
        model_slug: Optional[str] = None,
        prompt_type_slug: Optional[str] = None,
    ) -> List[Dict[str, object]]:
        if not self.prompts:
            return []

        filtered_indices = [
            index
            for index, prompt in enumerate(self.prompts)
            if self._matches_filters(
                prompt,
                category_slug=category_slug,
                model_slug=model_slug,
                prompt_type_slug=prompt_type_slug,
            )
        ]

        if not filtered_indices:
            return []

        normalized_query = query.strip()
        if not normalized_query:
            prompts = [dict(self.prompts[index]) for index in filtered_indices]
            prompts.sort(key=lambda prompt: (prompt["featured"], prompt["popularity"]), reverse=True)
            return prompts[:limit]

        query_embedding = get_embedding(normalized_query)
        distances, indices = self._neighbors.kneighbors([query_embedding], n_neighbors=len(self.prompts))
        filtered_lookup = set(filtered_indices)
        ranked = []

        for distance, index in zip(distances[0], indices[0]):
            if int(index) not in filtered_lookup:
                continue
            prompt = dict(self.prompts[int(index)])
            bonus = self._lexical_bonus(normalized_query, prompt)
            score = float((2.0 - float(distance)) + bonus + (0.15 if prompt["featured"] else 0.0))
            prompt["semantic_distance"] = round(float(distance), 6)
            prompt["score"] = round(score, 6)
            ranked.append(prompt)

        ranked.sort(key=lambda prompt: (prompt["score"], prompt["featured"], prompt["popularity"]), reverse=True)
        return ranked[:limit]


@lru_cache(maxsize=1)
def get_prompt_search_index() -> PromptSearchIndex:
    return PromptSearchIndex(prompt_fixtures.get_all_prompts())


def search_prompts(
    query: str,
    *,
    limit: int = 24,
    category_slug: Optional[str] = None,
    model_slug: Optional[str] = None,
    prompt_type_slug: Optional[str] = None,
) -> List[Dict[str, object]]:
    return get_prompt_search_index().search(
        query,
        limit=limit,
        category_slug=category_slug,
        model_slug=model_slug,
        prompt_type_slug=prompt_type_slug,
    )

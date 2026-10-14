
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer


MODEL_NAME = "intfloat/multilingual-e5-small"


@lru_cache(maxsize=1)
def get_embedding_model():
    """Load model once and reuse it."""
    return SentenceTransformer(MODEL_NAME)


def search_chunks(
    query: str,
    chunks: list[dict],
    top_k: int = 3,
) -> list[dict]:
    """
    Find document chunks most relevant to a query.

    Returns chunks ranked by cosine similarity.
    """
    if not query.strip():
        raise ValueError("Pertanyaan tidak boleh kosong.")

    if top_k <= 0:
        raise ValueError("top_k harus lebih besar dari 0.")

    valid_chunks = [
        chunk for chunk in chunks
        if chunk.get("text", "").strip()
    ]

    if not valid_chunks:
        return []

    model = get_embedding_model()

    passage_texts = [
        "passage: " + chunk["text"]
        for chunk in valid_chunks
    ]

    query_text = "query: " + query

    passage_embeddings = model.encode(
        passage_texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )

    query_embedding = model.encode(
        [query_text],
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )

    scores = (query_embedding @ passage_embeddings.T)[0]

    ranked_results = []

    for index, score in enumerate(scores):
        result = valid_chunks[index].copy()
        result["score"] = float(score)
        ranked_results.append(result)

    ranked_results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return ranked_results[:top_k]

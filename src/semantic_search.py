
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer


MODEL_NAME = "intfloat/multilingual-e5-small"


@lru_cache(maxsize=1)
def get_embedding_model():
    """Memuat model embedding sekali dan menggunakannya kembali."""
    return SentenceTransformer(MODEL_NAME)


def search_chunks(
    query: str,
    chunks: list[dict],
    top_k: int = 5,
    min_score: float = 0.45,
) -> list[dict]:
    """
    Mencari chunks yang paling relevan dengan pertanyaan.

    Hasil diurutkan berdasarkan cosine similarity.
    min_score adalah ambang awal, bukan persentase akurasi.
    """

    if not query or not query.strip():
        raise ValueError("Pertanyaan tidak boleh kosong.")

    if top_k <= 0:
        raise ValueError("top_k harus lebih besar dari 0.")

    valid_chunks = [
        chunk
        for chunk in chunks
        if chunk.get("text", "").strip()
    ]

    if not valid_chunks:
        return []

    model = get_embedding_model()

    passage_texts = [
        "passage: " + chunk["text"].strip()
        for chunk in valid_chunks
    ]

    query_embedding = model.encode(
        ["query: " + query.strip()],
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )

    passage_embeddings = model.encode(
        passage_texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
        batch_size=32,
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

    # Jangan mengirim konteks dengan skor terlalu rendah.
    relevant_results = [
        item
        for item in ranked_results
        if item["score"] >= min_score
    ]

    return relevant_results[:top_k]

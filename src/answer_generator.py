
import re

from src.semantic_search import get_embedding_model, search_chunks


def split_sentences(text: str) -> list[str]:
    """
    Memecah teks menjadi kalimat-kalimat sederhana.
    """
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())

    return [
        sentence.strip()
        for sentence in sentences
        if len(sentence.strip().split()) >= 5
    ]


def generate_answer(
    query: str,
    chunks: list[dict],
    top_k: int = 3,
) -> dict:
    """
    Membuat jawaban ekstraktif dari kalimat-kalimat dokumen.
    Tidak menggunakan LLM generatif.
    """

    if not query.strip():
        raise ValueError("Pertanyaan tidak boleh kosong.")

    # Tahap 1: cari chunks yang relevan.
    retrieved_chunks = search_chunks(
        query=query,
        chunks=chunks,
        top_k=5,
    )

    if not retrieved_chunks:
        return {
            "answer": "Tidak ditemukan teks yang relevan.",
            "sources": [],
        }

    # Tahap 2: ambil kalimat dari chunks yang ditemukan.
    candidates = []

    for chunk in retrieved_chunks:
        sentences = split_sentences(chunk["text"])

        for sentence in sentences:
            candidates.append({
                "text": sentence,
                "page": chunk["page"],
                "chunk_id": chunk["chunk_id"],
            })

    if not candidates:
        return {
            "answer": "Tidak ditemukan kalimat yang dapat digunakan.",
            "sources": [],
        }

    # Tahap 3: bandingkan pertanyaan dengan setiap kalimat.
    model = get_embedding_model()

    query_embedding = model.encode(
        ["query: " + query],
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )

    sentence_embeddings = model.encode(
        ["passage: " + item["text"] for item in candidates],
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )

    scores = (
        query_embedding @ sentence_embeddings.T
    )[0]

    # Tahap 4: urutkan kalimat berdasarkan kemiripan.
    ranked_sentences = []

    for index, score in enumerate(scores):
        item = candidates[index].copy()
        item["score"] = float(score)
        ranked_sentences.append(item)

    ranked_sentences.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    # Hindari menampilkan kalimat duplikat.
    selected = []
    seen = set()

    for item in ranked_sentences:
        normalized = item["text"].lower()

        if normalized in seen:
            continue

        seen.add(normalized)
        selected.append(item)

        if len(selected) >= top_k:
            break

    if not selected:
        return {
            "answer": "Tidak ditemukan jawaban yang dapat digunakan.",
            "sources": [],
        }

    # Tahap 5: susun jawaban dari kalimat asli dokumen.
    answer = " ".join(
        item["text"] for item in selected
    )

    sources = [
        {
            "page": item["page"],
            "chunk_id": item["chunk_id"],
            "text": item["text"],
            "score": item["score"],
        }
        for item in selected
    ]

    return {
        "answer": answer,
        "sources": sources,
    }

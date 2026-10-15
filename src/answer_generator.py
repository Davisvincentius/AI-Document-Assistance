
import streamlit as st
from google import genai
from google.genai import types

from src.semantic_search import search_chunks


def generate_answer(
    query: str,
    chunks: list[dict],
    top_k: int = 3,
) -> dict:
    """
    Mencari bagian PDF yang relevan, lalu menggunakan Gemini
    untuk menyusun jawaban berdasarkan konteks dokumen.
    """

    if not query or not query.strip():
        raise ValueError("Pertanyaan tidak boleh kosong.")

    # 1. Cari bagian dokumen yang relevan.
    retrieved_chunks = search_chunks(
    query=query,
    chunks=chunks,
    top_k=8,
    min_score=0.45,
)

    if not retrieved_chunks:
        return {
            "answer": "Tidak ditemukan teks yang relevan dalam dokumen.",
            "sources": [],
        }

    # 2. Siapkan konteks dan sumber halaman untuk Gemini.
    context_parts = []
    sources = []
    seen_chunks = set()

    for chunk in retrieved_chunks:
        chunk_id = chunk.get("chunk_id")
        page = chunk.get("page")
        text = chunk.get("text", "").strip()

        if not text:
            continue

        context_parts.append(
            f"[Halaman {page} | Chunk {chunk_id}]\n{text}"
        )

        # Satu sumber untuk setiap chunk yang unik.
        if chunk_id not in seen_chunks:
            seen_chunks.add(chunk_id)
            source = {
                "page": page,
                "chunk_id": chunk_id,
                "text": text,
            }

            # Pertahankan skor jika tersedia dari semantic search.
            if "score" in chunk:
                source["score"] = float(chunk["score"])

            sources.append(source)

    if not context_parts:
        return {
            "answer": "Tidak ditemukan teks yang dapat digunakan.",
            "sources": [],
        }

    context = "\n\n---\n\n".join(context_parts)

    # 3. Ambil API key dari Streamlit Secrets.
    api_key = st.secrets.get("GEMINI_API_KEY")

    if not api_key:
        return {
            "answer": (
                "Gemini belum dikonfigurasi. "
                "Tambahkan GEMINI_API_KEY pada Streamlit Cloud Secrets."
            ),
            "sources": sources,
        }

    # 4. Buat client Gemini.
    client = genai.Client(api_key=api_key)
       
        prompt = f"""
        Kamu adalah asisten akademik yang menjawab pertanyaan berdasarkan
        dokumen PDF yang diberikan.
        
        PERTANYAAN:
        {query}
        
        KONTEKS DOKUMEN:
        {context}
        
        ATURAN MENJAWAB:
        1. Jawab pertanyaan secara langsung dan jelas dalam bahasa Indonesia.
        2. Tulis jawaban sebagai satu paragraf yang runtut.
        3. Jangan menyalin atau mengulang judul, subjudul, atau kalimat
           yang sama dari konteks.
        4. Abaikan kata header seperti METODOLOGI jika hanya merupakan
           judul bagian, bukan bagian dari jawaban.
        5. Gabungkan informasi yang saling berkaitan tanpa pengulangan.
        6. Untuk pertanyaan tentang metode, sebutkan nama metode dan
           jelaskan cara penggunaannya jika tersedia dalam konteks.
        7. Jangan menambahkan fakta yang tidak didukung dokumen.
        8. Sertakan nomor halaman sumber dalam format [Halaman N].
        9. Jika informasi tidak cukup, jelaskan keterbatasannya.
        
        Berikan hanya jawaban akhir yang sudah rapi, bukan analisis
        atau pengulangan konteks.
        """

        PERTANYAAN:
        {query}
        
        KONTEKS DOKUMEN:
        {context}
        
        TULIS JAWABAN:
        """

    # 5. Minta Gemini menyusun jawaban.
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
            ),
        )

        answer = (response.text or "").strip()

        if not answer:
            answer = "Gemini tidak menghasilkan jawaban. Silakan coba lagi."

    except Exception:
        # Hindari menampilkan detail internal atau API key
        # kepada pengguna aplikasi.
        return {
            "answer": (
                "Terjadi kendala saat menghubungi Gemini. "
                "Periksa konfigurasi API key, kuota API, dan log aplikasi."
            ),
            "sources": sources,
        }

    # 6. Kembalikan jawaban dan sumber ke Streamlit.
    return {
        "answer": answer,
        "sources": sources,
    }

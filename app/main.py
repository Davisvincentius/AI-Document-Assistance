
import sys
from pathlib import Path

# Menambahkan folder utama project ke Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pymupdf

from src.pdf_processor import extract_text_from_pdf, render_pdf_page
from src.text_chunker import chunk_pages
from src.semantic_search import search_chunks
from src.answer_generator import generate_answer


st.set_page_config(
    page_title="AI Document Assistant",
    page_icon="📄",
    layout="wide",
)

st.title("AI Document Assistant")
st.write(
    "Upload dokumen PDF untuk mengekstrak dan melihat isi dokumen."
)

uploaded_file = st.file_uploader(
    "Pilih dokumen PDF",
    type=["pdf"],
)

if uploaded_file is not None:
    pdf_bytes = uploaded_file.getvalue()

    try:
        pages = extract_text_from_pdf(pdf_bytes)
        chunks = chunk_pages(
                    pages,
                    chunk_size=150,
                    overlap=30,
                )
        
        
        if not pages:
            st.warning("Dokumen tidak memiliki halaman.")
        else:
            total_chars = sum(
                len(page["text"]) for page in pages
            )

            st.success(
                f"PDF berhasil diproses: {len(pages)} halaman."
            )

            st.metric("Total halaman", len(pages))
            st.metric("Total karakter", total_chars)
            st.divider()
            st.subheader("Text Chunks")

            st.write(f"Total chunks: {len(chunks)}")

            for chunk in chunks:
                with st.expander(
                    f"Chunk {chunk['chunk_id']} — Halaman {chunk['page']}"
                ):
                    st.write(chunk["text"])
                        
            st.divider()
            st.subheader("💬 AI QNA")

            st.write(
                "Ajukan pertanyaan dan dapatkan jawaban "
                "berdasarkan isi dokumen."
            )

            user_question = st.text_input(
                "Pertanyaan untuk AI:",
                placeholder="Contoh: Apa tujuan utama penelitian ini?",
                key="qa_question",
            )

            if st.button(
                "✨ Buat Jawaban",
                key="qa_button",
            ):
                if not user_question.strip():
                    st.warning(
                        "Masukkan pertanyaan terlebih dahulu."
                    )

                else:
                    try:
                        with st.spinner(
                            "Sedang menyusun jawaban dari dokumen..."
                        ):
                            qa_result = generate_answer(
                                query=user_question,
                                chunks=chunks,
                                top_k=3,
                            )

                        st.markdown("### Jawaban")

                        st.write(qa_result["answer"])

                        st.markdown("### 📚 Sumber Jawaban")

                        if qa_result["sources"]:
                            for source in qa_result["sources"]:
                                with st.expander(
                                    f"Halaman {source['page']} "
                                    f"— Kemiripan "
                                    f"{source['score'] * 100:.1f}%"
                                ):
                                    st.write(source["text"])
                        else:
                            st.info(
                                "Tidak ada sumber yang ditemukan."
                            )

                        st.caption(
                            "Jawaban disusun dari kalimat dokumen. "
                            "Periksa sumber untuk memastikan konteksnya."
                        )

                    except Exception as error:
                        st.error(
                            f"Gagal membuat jawaban: {error}"
                        )


            
        for page in pages:
            with st.expander(
                f"Halaman {page['page']}",
                expanded=page["page"] == 1,
            ):
                st.image(
                    render_pdf_page(pdf_bytes, page["page"]),
                    caption=f"Preview halaman {page['page']}",
                    use_container_width=True,
                )

                st.divider()

                st.subheader("Teks hasil ekstraksi")

                if page["text"]:
                    st.text(page["text"])
                else:
                    st.info(
                        "Tidak ada teks yang dapat diekstrak "
                        "dari halaman ini."
                    )
                    

    except Exception as error:
        st.error(f"Gagal memproses PDF: {error}")

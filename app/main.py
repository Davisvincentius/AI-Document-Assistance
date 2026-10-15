
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
        from src.text_chunker import CHUNKER_VERSION
        st.caption(f"Chunker version: {CHUNKER_VERSION}")
        
        # DEBUG SEMANTIC SEARCH
        with st.expander("🔍 Debug Semantic Search"):
            debug_question = st.text_input(
                "Pertanyaan untuk menguji pencarian",
                key="debug_search_question",
            )
        
            if st.button("Uji Retrieval"):
                if not debug_question.strip():
                    st.warning("Masukkan pertanyaan terlebih dahulu.")
                else:
                    results = search_chunks(
                        query=debug_question,
                        chunks=chunks,
                        top_k=5,
                    )
        
                    if not results:
                        st.info("Tidak ditemukan hasil yang relevan.")
                    else:
                        for result in results:
                            score = result.get("score", 0)
        
                            st.markdown(
                                f"**Halaman {result['page']} — "
                                f"Skor {score:.3f}**"
                            )
                            st.write(result["text"])
                            st.divider()

        
        
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
                        
                        # Tampilkan jawaban AI sebagai satu paragraf.
                        st.write(qa_result["answer"])
                        
                        st.markdown("### 📚 Sumber Jawaban")
                        
                        if qa_result["sources"]:
                            # Kelompokkan semua sumber berdasarkan halaman PDF.
                            sources_by_page = {}
                        
                            for source in qa_result["sources"]:
                                page = source.get("page")
                                text = source.get("text", "").strip()
                        
                                if page not in sources_by_page:
                                    sources_by_page[page] = []
                        
                                # Hindari menampilkan teks sumber yang sama dua kali.
                                if text and text not in sources_by_page[page]:
                                    sources_by_page[page].append(text)
                        
                            # Tampilkan satu kotak untuk setiap halaman.
                            for page in sorted(
                                sources_by_page,
                                key=lambda value: value or 0,
                            ):
                                with st.expander(f"📄 Halaman {page}"):
                                    for text in sources_by_page[page]:
                                        st.write(text)
                        
                        else:
                            st.info("Tidak ada sumber yang ditemukan.")
                        
                        st.caption(
                            "Jawaban dibuat berdasarkan konteks dokumen. "
                            "Periksa sumber halaman untuk memverifikasi informasi."
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

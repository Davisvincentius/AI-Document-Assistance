
import fitz
import pymupdf

def extract_text_from_pdf(pdf_bytes: bytes) -> list[dict]:
    """Extract text from every page of a PDF."""
    

    pages = []

    with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text").strip()

            pages.append({
                "page": page_number,
                "text": text,
            })

    return pages


def render_pdf_page(pdf_bytes: bytes, page_number: int) -> bytes:
    """Render one PDF page as a PNG image."""

    with pymupdf.open(
        stream=pdf_bytes,
        filetype="pdf",
    ) as document:

        if page_number < 1 or page_number > len(document):
            raise ValueError("Nomor halaman tidak valid.")

        page = document[page_number - 1]

        pixmap = page.get_pixmap(
            matrix=pymupdf.Matrix(1.5, 1.5),
            alpha=False,
        )

        return pixmap.tobytes("png")




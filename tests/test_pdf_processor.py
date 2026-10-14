
import fitz

from src.pdf_processor import extract_text_from_pdf


def test_extract_text_from_pdf():
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Hello AI Engineer")

    pdf_bytes = document.tobytes()
    document.close()

    result = extract_text_from_pdf(pdf_bytes)

    assert len(result) == 1
    assert result[0]["page"] == 1
    assert "Hello AI Engineer" in result[0]["text"]

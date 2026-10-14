
import pytest

from src.text_chunker import chunk_pages



def test_chunk_pages_with_overlap():
    pages = [
        {
            "page": 1,
            "text": "satu dua tiga empat lima enam tujuh delapan",
        }
    ]

    result = chunk_pages(
        pages,
        chunk_size=4,
        overlap=1,
    )

    assert len(result) == 3

    assert result[0]["text"] == "satu dua tiga empat"
    assert result[1]["text"] == "empat lima enam tujuh"
    assert result[2]["text"] == "tujuh delapan"

    assert result[0]["page"] == 1
    assert result[2]["page"] == 1


def test_empty_page_returns_no_chunks():
    pages = [{"page": 1, "text": ""}]

    assert chunk_pages(pages) == []


def test_invalid_overlap_raises_error():
    pages = [{"page": 1, "text": "satu dua tiga"}]

    with pytest.raises(ValueError):
        chunk_pages(
            pages,  
            chunk_size=3,
            overlap=3,
        )

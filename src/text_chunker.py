
import re


REFERENCE_HEADINGS = {
    "daftar pustaka",
    "daftar referensi",
    "referensi",
    "references",
    "bibliography",
}


def normalize_line(line: str) -> str:
    """Membersihkan spasi berlebih pada satu baris."""
    return " ".join(line.split())


def is_reference_heading(line: str) -> bool:
    """Mendeteksi judul bagian referensi."""
    normalized = re.sub(r"[^a-zA-Z\s]", "", line)
    normalized = " ".join(normalized.lower().split())
    return normalized in REFERENCE_HEADINGS


def split_paragraphs(text: str) -> list[str]:
    """
    Memisahkan teks berdasarkan baris kosong.
    Baris yang terpotong karena layout PDF digabung kembali.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    raw_paragraphs = re.split(r"\n\s*\n+", text)
    paragraphs = []

    for paragraph in raw_paragraphs:
        lines = [
            normalize_line(line)
            for line in paragraph.splitlines()
            if normalize_line(line)
        ]

        if lines:
            paragraphs.append(" ".join(lines))

    return paragraphs


def split_long_paragraph(
    paragraph: str,
    chunk_size: int,
    overlap: int,
) -> list[str]:
    """
    Membagi paragraf yang terlalu panjang menjadi beberapa chunk.
    Paragraf pendek tidak dipotong.
    """
    words = paragraph.split()

    if len(words) <= chunk_size:
        return [paragraph]

    chunks = []
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))

        if end == len(words):
            break

        start = end - overlap

    return chunks


def chunk_pages(
    pages: list[dict],
    chunk_size: int = 150,
    overlap: int = 30,
) -> list[dict]:
    """
    Membuat chunks berdasarkan paragraf dan mempertahankan
    nomor halaman. Bagian referensi tidak ikut diproses.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size harus lebih besar dari 0.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "overlap harus >= 0 dan lebih kecil dari chunk_size."
        )

    chunks = []
    next_chunk_id = 1
    inside_references = False

    for page in pages:
        text = page.get("text", "")
        page_number = page["page"]

        if inside_references:
            break

        paragraphs = split_paragraphs(text)

        for paragraph in paragraphs:
            lines = paragraph.splitlines()

            # Periksa juga setiap baris untuk mendeteksi judul referensi.
            if is_reference_heading(paragraph):
                inside_references = True
                break

            if any(is_reference_heading(line) for line in lines):
                inside_references = True
                break

            # Abaikan paragraf kosong.
            if not paragraph.strip():
                continue

            pieces = split_long_paragraph(
                paragraph=paragraph,
                chunk_size=chunk_size,
                overlap=overlap,
            )

            for piece in pieces:
                chunks.append({
                    "chunk_id": next_chunk_id,
                    "page": page_number,
                    "text": piece,
                })

                next_chunk_id += 1

        if inside_references:
            break

    return chunks

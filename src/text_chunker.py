
import re


REFERENCE_HEADINGS = {
    "daftar pustaka",
    "daftar referensi",
    "referensi",
    "references",
    "bibliography",
}


def is_reference_heading(line: str) -> bool:
    """Check whether a line marks the start of references."""
    normalized = re.sub(r"[^a-zA-Z\s]", "", line)
    normalized = " ".join(normalized.lower().split())

    return normalized in REFERENCE_HEADINGS


def chunk_pages(
    pages: list[dict],
    chunk_size: int = 150,
    overlap: int = 30,
) -> list[dict]:
    """
    Split PDF text into word-based chunks.
    Exclude the bibliography section when a recognized
    reference heading is found.
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
        text = page["text"]
        kept_lines = []

        for line in text.splitlines():
            if is_reference_heading(line):
                inside_references = True
                break

            if not inside_references:
                kept_lines.append(line)

        # Jika bagian referensi sudah dimulai pada halaman
        # sebelumnya, halaman berikutnya tidak ikut dicari.
        if inside_references and not kept_lines:
            continue

        cleaned_text = " ".join(kept_lines)
        words = cleaned_text.split()
        start = 0

        while start < len(words):
            end = min(start + chunk_size, len(words))

            chunks.append({
                "chunk_id": next_chunk_id,
                "page": page["page"],
                "text": " ".join(words[start:end]),
            })

            next_chunk_id += 1

            if end == len(words):
                break

            start = end - overlap

        if inside_references:
            break

    return chunks

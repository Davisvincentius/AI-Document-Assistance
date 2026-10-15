
import re
CHUNKER_VERSION = "2026-10-15-v2"

REFERENCE_HEADINGS = {
    "daftar pustaka",
    "daftar referensi",
    "referensi",
    "references",
    "bibliography",
}

# Judul bagian yang umum ditemukan dalam jurnal akademik.
SECTION_NAMES = (
    r"abstract|abstrak|"
    r"introduction|pendahuluan|"
    r"background|latar belakang|"
    r"related work|literature review|tinjauan pustaka|"
    r"methodology|method|methods|metodologi|metode|"
    r"materials and methods|"
    r"results and discussion|hasil dan pembahasan|"
    r"results|findings|hasil|temuan|"
    r"discussion|pembahasan|"
    r"conclusion|conclusions|kesimpulan|"
    r"limitations|keterbatasan|"
    r"future work|pekerjaan selanjutnya|"
    r"acknowledgments|acknowledgements|ucapan terima kasih|"
    r"references|bibliography|daftar pustaka|daftar referensi"
)

# Judul bernomor, misalnya "1. Introduction" atau "2.1 Data Understanding".
NUMBERED_HEADING = re.compile(
    rf"(?<!\w)(\d{{1,2}}(?:\.\d{{1,2}})*\.?\s+"
    rf"(?:{SECTION_NAMES}))(?:\s*[:.]?\s*)",
    re.IGNORECASE,
)

# Label abstrak dan kata kunci, termasuk jika menyatu dengan teks.
LABEL_HEADING = re.compile(
    r"(?<!\w)(Abstract|Abstrak|Keywords|Key words|Kata kunci)"
    r"\s*:\s*",
    re.IGNORECASE,
)

# Judul bagian tanpa nomor. Hanya dideteksi pada awal baris.
LINE_HEADING = re.compile(
    rf"^\s*(?:{SECTION_NAMES})\s*:?\s*$",
    re.IGNORECASE,
)


def normalize_text(text: str) -> str:
    """Membersihkan spasi tanpa menghilangkan batas paragraf."""
    text = text.replace("\u00a0", " ").replace("\u00ad", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = [
        re.sub(r"[ \t]+", " ", line).strip()
        for line in text.splitlines()
    ]

    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def is_reference_heading(line: str) -> bool:
    """Mendeteksi judul daftar referensi."""
    normalized = re.sub(r"[^a-zA-Z\s]", "", line)
    normalized = " ".join(normalized.lower().split())
    return normalized in REFERENCE_HEADINGS


def split_sections(text: str) -> list[str]:
    """
    Memisahkan teks pada penanda bagian jurnal.
    Judul bernomor dapat dideteksi meskipun menempel
    pada akhir paragraf sebelumnya.
    """
    text = normalize_text(text)

    if not text:
        return []

    # Pisahkan label Abstract/Keywords jika menempel pada teks.
    text = LABEL_HEADING.sub(
        lambda match: "\n\n" + match.group(1) + ": ",
        text,
    )

    # Pastikan judul bernomor dimulai di bagian baru.
    text = NUMBERED_HEADING.sub(
        lambda match: "\n\n" + match.group(1).strip() + " ",
        text,
    )

    sections = []

    for block in re.split(r"\n\s*\n+", text):
        block = block.strip()

        if not block:
            continue

        # Jika blok berisi judul pada awal baris tersendiri,
        # pertahankan sebagai bagian terpisah.
        lines = block.splitlines()

        if len(lines) > 1 and LINE_HEADING.match(lines[0]):
            heading = lines[0].strip()
            body = " ".join(line.strip() for line in lines[1:] if line.strip())

            sections.append(
                f"{heading} {body}".strip() if body else heading
            )
        else:
            sections.append(" ".join(lines).strip())

    return sections


def split_long_text(
    text: str,
    chunk_size: int,
    overlap: int,
) -> list[str]:
    """Membagi teks panjang dengan overlap antar-chunk."""
    words = text.split()

    if len(words) <= chunk_size:
        return [text]

    pieces = []
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        pieces.append(" ".join(words[start:end]))

        if end == len(words):
            break

        start = end - overlap

    return pieces


def chunk_pages(
    pages: list[dict],
    chunk_size: int = 150,
    overlap: int = 30,
) -> list[dict]:
    """
    Membuat chunks dengan mendeteksi bagian jurnal terlebih dahulu.
    Format output tetap: chunk_id, page, text.
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
        page_text = normalize_text(page.get("text", ""))

        if not page_text or inside_references:
            break

        sections = split_sections(page_text)

        for section in sections:
            lines = section.splitlines()

            # Hentikan pemrosesan saat daftar referensi dimulai.
            if any(is_reference_heading(line) for line in lines):
                inside_references = True
                break

            # Periksa juga judul referensi yang menempel
            # pada teks setelah pemisahan bagian.
            first_line = lines[0].strip() if lines else section.strip()

            if is_reference_heading(first_line):
                inside_references = True
                break

            for piece in split_long_text(
                section,
                chunk_size=chunk_size,
                overlap=overlap,
            ):
                chunks.append({
                    "chunk_id": next_chunk_id,
                    "page": page["page"],
                    "text": piece,
                })
                next_chunk_id += 1

        if inside_references:
            break

    return chunks


import re
import pymupdf


def clean_extracted_text(text: str) -> str:
    """Membersihkan spasi dan karakter yang tidak diperlukan."""

    text = text.replace("\u00a0", " ")
    text = text.replace("\u00ad", "")

    # Rapikan spasi pada setiap baris tanpa menghapus
    # seluruh pemisah baris.
    lines = [
        re.sub(r"[ \t]+", " ", line).strip()
        for line in text.splitlines()
    ]

    # Hapus baris kosong berulang.
    cleaned_lines = []
    previous_blank = False

    for line in lines:
        if not line:
            if not previous_blank:
                cleaned_lines.append("")
            previous_blank = True
        else:
            cleaned_lines.append(line)
            previous_blank = False

    return "\n".join(cleaned_lines).strip()


def extract_text_from_pdf(pdf_bytes: bytes) -> list[dict]:
    """
    Mengekstrak teks per halaman menggunakan blok teks.
    Blok diurutkan berdasarkan posisi atas lalu kiri.
    """

    pages = []

    with pymupdf.open(
        stream=pdf_bytes,
        filetype="pdf",
    ) as document:

        for page_number, page in enumerate(document, start=1):
            blocks = page.get_text("blocks", sort=True)

            text_blocks = []

            for block in blocks:
                # Format blok PyMuPDF:
                # x0, y0, x1, y1, text, block_no, block_type
                if len(block) < 7:
                    continue

                block_text = block[4].strip()
                block_type = block[6]

                # Abaikan blok gambar, bukan teks.
                if block_type != 0 or not block_text:
                    continue

                text_blocks.append(block_text)

            raw_text = "\n\n".join(text_blocks)
            text = clean_extracted_text(raw_text)

            pages.append({
                "page": page_number,
                "text": text,
            })

    return pages


def render_pdf_page(
    pdf_bytes: bytes,
    page_number: int,
) -> bytes:
    """Merender satu halaman PDF menjadi gambar PNG."""

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

import re
from models.documents import Document


def clean_text(text: str) -> str:
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove leading/trailing spaces
    return text.strip()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50):
    chunks = []
    # Keep headings attached to their section so retrieval retains the article's
    # argument structure. Split only oversized sections as a secondary limit.
    sections = re.split(r"(?m)(?=^##\s+)", text.strip())
    for section in sections:
        section = clean_text(section)
        if not section:
            continue
        heading_match = re.match(r"^(##\s+[^.]+?)(?:\s+|$)(.*)$", section)
        heading = heading_match.group(1) if heading_match else ""
        body = section[len(heading):].strip() if heading else section
        if len(section) <= chunk_size:
            chunks.append(section)
            continue
        start = 0
        while start < len(body):
            end = start + chunk_size - len(heading) - 1
            piece = body[start:end]
            chunks.append(f"{heading}\n{piece}" if heading else piece)
            start += max(1, chunk_size - len(heading) - overlap)

    return chunks


def process_document(document: Document):
    cleaned_content = clean_text(document.content)

    chunks = chunk_text(cleaned_content)

    return chunks

import re
from models.documents import Document


def clean_text(text: str) -> str:
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove leading/trailing spaces
    return text.strip()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50):
    text = clean_text(text)

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        chunk = text[start:end]
        chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def process_document(document: Document):
    cleaned_content = clean_text(document.content)

    chunks = chunk_text(cleaned_content)

    return chunks
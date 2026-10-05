from pydantic import BaseModel
from typing import Optional


class Document(BaseModel):
    title: str
    content: str


class DocumentURL(BaseModel):
    url: str


class QARequest(BaseModel):
    question: str
    url: Optional[str] = None
    title: Optional[str] = None
    context: Optional[str] = None


class QAResponse(BaseModel):
    answer: str

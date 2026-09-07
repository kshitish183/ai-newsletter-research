from pydantic import BaseModel
from typing import Optional


class Document(BaseModel):
    title: str
    content: str


class DocumentURL(BaseModel):
    url: str

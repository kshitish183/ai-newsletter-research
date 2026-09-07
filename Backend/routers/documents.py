from article_analyzer import analyze_article
from models.article import ArticleAnalysis
from fastapi import APIRouter, HTTPException
from models.documents import Document, DocumentURL
from services.scrapper import scrape_article

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


@router.post("/url")
def add_document_from_url(document: DocumentURL) -> Document:
    try:
        return scrape_article(document.url)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("/analyze")
def analyze_document(document: DocumentURL) -> ArticleAnalysis:
    try:
        return analyze_article(document.url)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

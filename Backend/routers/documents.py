from fastapi import APIRouter, HTTPException
from article_analyzer import analyze_article, answer_article_question
from models.article import ArticleAnalysis
from models.documents import Document, DocumentURL, QARequest, QAResponse
from services.scrapper import scrape_article

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


@router.post("/url")
def add_document_from_url(document: DocumentURL) -> Document:
    try:
        data = scrape_article(document.url)
        return Document(**data)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("/analyze")
def analyze_document(document: DocumentURL) -> ArticleAnalysis:
    try:
        return analyze_article(document.url)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("/ask")
def ask_question_route(qa: QARequest) -> QAResponse:
    try:
        answer = answer_article_question(
            question=qa.question,
            url=qa.url,
            title=qa.title,
            context=qa.context
        )
        return QAResponse(answer=answer)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

import logging
from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool
from article_analyzer import analyze_article, answer_article_question
from models.article import ArticleAnalysis
from models.documents import Document, DocumentURL, QARequest, QAResponse, Citation
from services.scrapper import scrape_article

logger = logging.getLogger("routers.documents")

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


@router.post("/url")
async def add_document_from_url(document: DocumentURL) -> Document:
    try:
        data = await run_in_threadpool(scrape_article, document.url)
        return Document(**data)
    except ValueError as e:
        logger.warning(f"Validation error in add_document_from_url: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Internal server error in add_document_from_url: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process article URL due to an internal error.")


@router.post("/analyze")
async def analyze_document(document: DocumentURL) -> ArticleAnalysis:
    try:
        analysis = await run_in_threadpool(analyze_article, document.url)
        return analysis
    except ValueError as e:
        logger.warning(f"Validation error in analyze_document: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Internal server error in analyze_document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to analyze document due to an internal error.")


@router.post("/ask")
async def ask_question_route(qa: QARequest) -> QAResponse:
    try:
        res = await run_in_threadpool(
            answer_article_question,
            question=qa.question,
            url=qa.url,
            title=qa.title,
            context=qa.context
        )
        if isinstance(res, dict):
            citations_data = [
                Citation(**c) if isinstance(c, dict) else c
                for c in res.get("citations", [])
            ]
            return QAResponse(answer=res.get("answer", ""), citations=citations_data)
        return QAResponse(answer=str(res), citations=[])
    except ValueError as e:
        logger.warning(f"Validation error in ask_question_route: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Internal server error in ask_question_route: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process question due to an internal error.")


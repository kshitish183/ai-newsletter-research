import os
import time
import uuid
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from routers.documents import router as documents_router

load_dotenv()

# Configure structured logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("api_server")

app = FastAPI(
    title="AI Knowledge Library API"
)

raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,https://my-newsletter.web.app")
origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id_and_log(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    start_time = time.time()
    
    # Store request_id in state for endpoints
    request.state.request_id = request_id
    
    logger.info(f"[{request_id}] START {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
        logger.info(f"[{request_id}] END {request.method} {request.url.path} - Status: {response.status_code} - {process_time:.2f}ms")
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.error(f"[{request_id}] FAILED {request.method} {request.url.path} after {process_time:.2f}ms - Exception: {e}", exc_info=True)
        raise e


app.include_router(documents_router)


@app.get("/")
async def root():
    return {
        "message": "AI Knowledge Library API is running!"
    }


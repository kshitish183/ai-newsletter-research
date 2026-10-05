import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.documents import router as documents_router

load_dotenv()

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

app.include_router(documents_router)


@app.get("/")
async def root():
    return {
        "message": "AI Knowledge Library API is running!"
    }

from fastapi import FastAPI
from routers.documents import router as documents_router


app = FastAPI(
    title="AI Knowledge Library API"
)


app.include_router(documents_router)

@app.get("/")
async def root():
    return {
        "message": "AI Knowledge Library API is running!"
    }

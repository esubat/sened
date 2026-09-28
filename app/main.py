from fastapi import FastAPI

from app.api.router import router as api_router

app = FastAPI(
    title="Sened API",
    description="A RAG API for working with documents",
    version="1.0.0",
)


app.include_router(api_router)

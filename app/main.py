from fastapi import FastAPI

app = FastAPI(
    title="Sened API",
    description="A RAG API for working with documents",
    version="1.0.0",
)


@app.get("/")
async def root():
    return {"message": "Hello from Sened!"}

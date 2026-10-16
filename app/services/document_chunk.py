import asyncio
import uuid
from dataclasses import dataclass

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.services import embedding as embedding_service


@dataclass(frozen=True)
class ChunkMatch:
    chunk: DocumentChunk
    distance: float


async def replace_document_chunks(
    db: AsyncSession, document_id: uuid.UUID, chunks: list[str]
) -> list[DocumentChunk]:
    """Embed chunks and store them, replacing any the document already has."""

    embeddings = await asyncio.to_thread(embedding_service.embed_texts, chunks)

    await db.execute(
        delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
    )
    document_chunks = [
        DocumentChunk(
            document_id=document_id,
            chunk_index=index,
            content=content,
            embedding=vector,
        )
        for index, (content, vector) in enumerate(zip(chunks, embeddings, strict=True))
    ]
    db.add_all(document_chunks)
    await db.commit()
    return document_chunks


async def search_chunks(
    db: AsyncSession,
    user: User,
    query: str,
    limit: int = 5,
    document_id: uuid.UUID | None = None,
) -> list[ChunkMatch]:
    """Return the user's chunks most similar to the query, closest first."""
    query_embedding = await asyncio.to_thread(embedding_service.embed_text, query)

    distance = DocumentChunk.embedding.cosine_distance(query_embedding)
    stmt = (
        select(DocumentChunk, distance.label("distance"))
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(Document.user_id == user.id)
        .order_by(distance)
        .limit(limit)
    )
    if document_id is not None:
        stmt = stmt.where(DocumentChunk.document_id == document_id)

    # Continue scanning after filtering to ensure enough matching chunks.
    await db.execute(text("SET LOCAL hnsw.iterative_scan = strict_order"))
    result = await db.execute(stmt)
    return [ChunkMatch(chunk=chunk, distance=dist) for chunk, dist in result]

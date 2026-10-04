import uuid

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import storage
from app.models.document import Document, DocumentStatus
from app.models.user import User
from app.schemas.document import DocumentCreateRequest, DocumentUpdateRequest
from app.services.upload import ensure_owned


class DocumentNotFoundError(Exception):
    pass


class DocumentAlreadyExistsError(Exception):
    pass


class DocumentFileNotUploadedError(Exception):
    pass


async def create_document(
    db: AsyncSession, user: User, data: DocumentCreateRequest
) -> Document:
    ensure_owned(user, data.storage_key)

    metadata = await storage.get_object_metadata(data.storage_key)
    if metadata is None:
        raise DocumentFileNotUploadedError("File has not been uploaded")

    new_document = Document(
        user_id=user.id,
        filename=data.filename,
        storage_key=data.storage_key,
        mime_type=metadata.content_type,
        size=metadata.size,
    )
    db.add(new_document)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise DocumentAlreadyExistsError("A document for this file already exists")
    await db.refresh(new_document)
    return new_document


async def get_user_documents(db: AsyncSession, user: User) -> list[Document]:
    stmt = (
        select(Document)
        .where(Document.user_id == user.id)
        .order_by(Document.created_at.desc())
    )
    result = await db.scalars(stmt)
    return list(result)


async def get_document_by_id(
    db: AsyncSession, user: User, document_id: uuid.UUID
) -> Document | None:
    stmt = select(Document).where(
        Document.id == document_id, Document.user_id == user.id
    )
    return await db.scalar(stmt)


async def update_document_status(
    db: AsyncSession, document_id: uuid.UUID, new_status: DocumentStatus
) -> Document | None:
    updated_document = await db.scalar(
        update(Document)
        .where(Document.id == document_id)
        .values(status=new_status)
        .returning(Document)
    )
    await db.commit()
    return updated_document


async def update_document(
    db: AsyncSession, user: User, document_id: uuid.UUID, data: DocumentUpdateRequest
) -> Document:
    document = await get_document_by_id(db, user, document_id)
    if document is None:
        raise DocumentNotFoundError("Document not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(document, field, value)
    await db.commit()
    await db.refresh(document)
    return document


async def delete_document(db: AsyncSession, user: User, document_id: uuid.UUID) -> None:
    document = await get_document_by_id(db, user, document_id)
    if document is None:
        raise DocumentNotFoundError("Document not found")

    storage_key = document.storage_key
    await db.delete(document)
    await db.commit()
    await storage.delete_object(storage_key)

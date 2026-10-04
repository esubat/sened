import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies.auth import CurrentUser
from app.api.dependencies.database import DbSession
from app.schemas.document import (
    DocumentCreateRequest,
    DocumentResponse,
    DocumentUpdateRequest,
)
from app.services import document as document_service
from app.services import upload as upload_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    data: DocumentCreateRequest, db: DbSession, current_user: CurrentUser
):
    try:
        return await document_service.create_document(db, current_user, data)
    except upload_service.ForbiddenKeyError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except document_service.DocumentFileNotUploadedError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except document_service.DocumentAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("", response_model=list[DocumentResponse])
async def list_documents(db: DbSession, current_user: CurrentUser):
    return await document_service.get_user_documents(db, current_user)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID, db: DbSession, current_user: CurrentUser
):
    document = await document_service.get_document_by_id(db, current_user, document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    return document


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: uuid.UUID,
    data: DocumentUpdateRequest,
    db: DbSession,
    current_user: CurrentUser,
):
    try:
        return await document_service.update_document(
            db, current_user, document_id, data
        )
    except document_service.DocumentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID, db: DbSession, current_user: CurrentUser
):
    try:
        await document_service.delete_document(db, current_user, document_id)
    except document_service.DocumentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies.auth import CurrentUser
from app.schemas.upload import (
    PresignedDownloadResponse,
    PresignedUrlRequest,
    PresignedUrlResponse,
)
from app.services import upload as upload_service

router = APIRouter(prefix="/uploads", tags=["uploads"])

ObjectKey = Annotated[str, Query(min_length=1, max_length=1024)]


@router.post(
    "/presigned-url",
    response_model=PresignedUrlResponse,
    status_code=status.HTTP_200_OK,
)
async def create_presigned_url(data: PresignedUrlRequest, current_user: CurrentUser):
    return upload_service.create_presigned_upload_url(current_user, data)


@router.get(
    "/download-url",
    response_model=PresignedDownloadResponse,
    status_code=status.HTTP_200_OK,
)
async def create_download_url(key: ObjectKey, current_user: CurrentUser):
    try:
        return upload_service.create_presigned_download_url(current_user, key)
    except upload_service.ForbiddenKeyError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(key: ObjectKey, current_user: CurrentUser):
    try:
        await upload_service.delete_file(current_user, key)
    except upload_service.ForbiddenKeyError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

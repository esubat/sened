import re
import uuid

from app.core import storage
from app.core.config import settings
from app.models.user import User
from app.schemas.upload import (
    PresignedDownloadResponse,
    PresignedUrlRequest,
    PresignedUrlResponse,
)


class ForbiddenKeyError(Exception):
    pass


def _safe_filename(filename: str) -> str:
    name = filename.replace("\\", "/").rsplit("/", 1)[-1]
    return re.sub(r"[^A-Za-z0-9._-]", "_", name) or "file"


def _user_prefix(user: User) -> str:
    return f"users/{user.id}/"


def _ensure_owned(user: User, key: str) -> None:
    if not key.startswith(_user_prefix(user)):
        raise ForbiddenKeyError("You do not have access to this file")


def create_presigned_upload_url(
    user: User, data: PresignedUrlRequest
) -> PresignedUrlResponse:
    key = f"{_user_prefix(user)}{uuid.uuid4()}-{_safe_filename(data.filename)}"
    expires_in = settings.s3_presigned_url_expire_seconds
    upload_url = storage.presign_upload(key, data.content_type, expires_in)
    return PresignedUrlResponse(upload_url=upload_url, key=key, expires_in=expires_in)


def create_presigned_download_url(user: User, key: str) -> PresignedDownloadResponse:
    _ensure_owned(user, key)
    expires_in = settings.s3_presigned_url_expire_seconds
    download_url = storage.presign_download(key, expires_in)
    return PresignedDownloadResponse(download_url=download_url, expires_in=expires_in)


async def delete_file(user: User, key: str) -> None:
    _ensure_owned(user, key)
    await storage.delete_object(key)

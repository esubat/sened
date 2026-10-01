from pydantic import BaseModel, Field


class PresignedUrlRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=255)


class PresignedUrlResponse(BaseModel):
    upload_url: str
    key: str
    expires_in: int


class PresignedDownloadResponse(BaseModel):
    download_url: str
    expires_in: int

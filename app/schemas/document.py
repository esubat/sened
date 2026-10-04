import uuid
from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.document import DocumentStatus


class DocumentCreateRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    storage_key: str = Field(min_length=1, max_length=1024)


class DocumentUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str | None = Field(default=None, min_length=1, max_length=255)

    @model_validator(mode="after")
    def reject_explicit_nulls(self) -> Self:
        null_fields = [
            name for name in self.model_fields_set if getattr(self, name) is None
        ]
        if null_fields:
            raise ValueError(f"Fields cannot be null: {', '.join(sorted(null_fields))}")
        return self


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    storage_key: str
    mime_type: str
    size: int
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime

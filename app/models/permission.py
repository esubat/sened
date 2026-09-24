import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .role import Role


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    roles: Mapped[list[Role]] = relationship(
        secondary="role_permissions", back_populates="permissions"
    )

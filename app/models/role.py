import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, String, Table, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .permission import Permission

if TYPE_CHECKING:
    from .user import User

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id",
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "permission_id",
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    permissions: Mapped[list[Permission]] = relationship(
        secondary=role_permissions, back_populates="roles"
    )
    users: Mapped[list[User]] = relationship(
        secondary="user_roles", back_populates="roles"
    )

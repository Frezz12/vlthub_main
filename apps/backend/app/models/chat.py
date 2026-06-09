import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="room", cascade="all, delete-orphan", order_by="ChatMessage.created_at"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    room_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("chat_rooms.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    version_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("versions.id", ondelete="SET NULL"), nullable=True)
    reply_to_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("chat_messages.id", ondelete="SET NULL"), nullable=True)
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    reactions: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    room: Mapped["ChatRoom"] = relationship(back_populates="messages")
    user: Mapped["User"] = relationship(lazy="joined")
    version: Mapped["Version | None"] = relationship(lazy="joined")
    reply_to: Mapped["ChatMessage | None"] = relationship(lazy="joined", remote_side="ChatMessage.id")

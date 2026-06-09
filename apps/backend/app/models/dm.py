import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSON, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DirectMessageRoom(Base):
    __tablename__ = "direct_message_rooms"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user1_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    user2_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_message_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    deleted_by: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user1: Mapped["User"] = relationship("User", foreign_keys=[user1_id], lazy="joined")
    user2: Mapped["User"] = relationship("User", foreign_keys=[user2_id], lazy="joined")
    messages: Mapped[list["DirectMessage"]] = relationship(
        back_populates="room", cascade="all, delete-orphan", order_by="DirectMessage.created_at"
    )


class DirectMessage(Base):
    __tablename__ = "direct_messages"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    room_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("direct_message_rooms.id", ondelete="CASCADE"), nullable=False)
    sender_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    reply_to_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("direct_messages.id", ondelete="SET NULL"), nullable=True)
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    reactions: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    file_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    file_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    room: Mapped["DirectMessageRoom"] = relationship(back_populates="messages")
    sender: Mapped["User"] = relationship("User", lazy="joined")
    reply_to: Mapped["DirectMessage | None"] = relationship("DirectMessage", remote_side="DirectMessage.id", lazy="joined")

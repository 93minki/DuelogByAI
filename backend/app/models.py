import enum
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

JSONType = JSON().with_variant(JSONB(), "postgresql")


def utcnow() -> datetime:
    return datetime.now(UTC)


class DebateStatus(str, enum.Enum):
    running = "running"
    completed = "completed"
    stopped = "stopped"
    failed = "failed"


class Speaker(str, enum.Enum):
    moderator = "moderator"
    pro = "pro"
    con = "con"


class Phase(str, enum.Enum):
    opening_remarks = "opening_remarks"  # 사회자 개회
    moderation = "moderation"  # 사회자 라운드 안내 / 최종 발언 안내
    opening = "opening"  # 1라운드 입론
    rebuttal = "rebuttal"  # 2라운드 이후 반박
    closing = "closing"  # 최종 발언


def _enum(cls: type[enum.Enum]) -> SAEnum:
    return SAEnum(cls, native_enum=False, length=20, validate_strings=True)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Debate(Base):
    __tablename__ = "debates"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    topic_raw: Mapped[str] = mapped_column(Text)
    proposition: Mapped[str | None] = mapped_column(Text, default=None)
    pro_stance: Mapped[str | None] = mapped_column(Text, default=None)
    con_stance: Mapped[str | None] = mapped_column(Text, default=None)
    status: Mapped[DebateStatus] = mapped_column(
        _enum(DebateStatus), default=DebateStatus.running, index=True
    )
    current_round: Mapped[int] = mapped_column(Integer, default=0)
    total_rounds: Mapped[int | None] = mapped_column(Integer, default=None)
    jev_result: Mapped[dict[str, Any] | None] = mapped_column(JSONType, default=None)
    error: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    turns: Mapped[list["Turn"]] = relationship(
        back_populates="debate",
        order_by="Turn.seq",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    sources: Mapped[list["Source"]] = relationship(
        order_by="Source.number", cascade="all, delete-orphan", passive_deletes=True
    )
    summary: Mapped["Summary | None"] = relationship(
        cascade="all, delete-orphan", passive_deletes=True, uselist=False
    )


class Turn(Base):
    __tablename__ = "turns"
    __table_args__ = (UniqueConstraint("debate_id", "seq"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    debate_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("debates.id", ondelete="CASCADE"), index=True
    )
    seq: Mapped[int] = mapped_column(Integer)
    round: Mapped[int] = mapped_column(Integer)  # 0 = 개회, 1..5, 99 = 최종 발언
    phase: Mapped[Phase] = mapped_column(_enum(Phase))
    speaker: Mapped[Speaker] = mapped_column(_enum(Speaker))
    content: Mapped[str] = mapped_column(Text)
    search_queries: Mapped[list[str]] = mapped_column(JSONType, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    debate: Mapped[Debate] = relationship(back_populates="turns")


class Source(Base):
    __tablename__ = "sources"
    __table_args__ = (
        UniqueConstraint("debate_id", "number"),
        UniqueConstraint("debate_id", "url"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    debate_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("debates.id", ondelete="CASCADE"), index=True
    )
    number: Mapped[int] = mapped_column(Integer)
    url: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text, default="")
    published_date: Mapped[str | None] = mapped_column(String(64), default=None)
    author: Mapped[str | None] = mapped_column(Text, default=None)
    excerpt: Mapped[str] = mapped_column(Text, default="")


class Summary(Base):
    __tablename__ = "summaries"

    debate_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("debates.id", ondelete="CASCADE"), primary_key=True
    )
    pro_summary: Mapped[str] = mapped_column(Text)
    con_summary: Mapped[str] = mapped_column(Text)
    final_summary: Mapped[dict[str, Any]] = mapped_column(JSONType)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

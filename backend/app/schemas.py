import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import DebateStatus, Phase, Speaker

TOPIC_MIN = 2
TOPIC_MAX = 200
PASSWORD_MIN = 8


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    created_at: datetime


class DebateCreate(BaseModel):
    topic: str

    @field_validator("topic")
    @classmethod
    def check_topic(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v) < TOPIC_MIN:
            raise ValueError(f"주제는 {TOPIC_MIN}자 이상 입력해 주세요.")
        if len(v) > TOPIC_MAX:
            raise ValueError(f"주제는 {TOPIC_MAX}자 이하로 입력해 주세요.")
        return v


class DebateListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    topic_raw: str
    proposition: str | None
    status: DebateStatus
    current_round: int
    total_rounds: int | None
    created_at: datetime
    completed_at: datetime | None


class TurnOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    seq: int
    round: int
    phase: Phase
    speaker: Speaker
    content: str
    search_queries: list[str]


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    number: int
    url: str
    title: str
    published_date: str | None
    author: str | None
    excerpt: str


class SummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pro_summary: str
    con_summary: str
    final_summary: dict[str, Any]


class DebateDetail(DebateListItem):
    pro_stance: str | None
    con_stance: str | None
    error: str | None
    turns: list[TurnOut]
    sources: list[SourceOut]
    summary: SummaryOut | None

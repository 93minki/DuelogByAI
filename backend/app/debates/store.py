"""그래프 실행 중 결과를 DB에 저장한다. 노드가 재실행돼도 결과가 같도록(idempotent) 작성한다."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import Debate, DebateStatus, Phase, Source, Speaker, Summary, Turn
from app.text import clean_deep, clean_text


class DebateStore:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._sessions = session_factory

    async def save_framing(
        self, debate_id: str, proposition: str, pro_stance: str, con_stance: str
    ) -> None:
        async with self._sessions() as s:
            debate = await s.get(Debate, uuid.UUID(debate_id))
            if debate is None:
                return
            debate.proposition = clean_text(proposition)
            debate.pro_stance = clean_text(pro_stance)
            debate.con_stance = clean_text(con_stance)
            await s.commit()

    async def save_turn(
        self, debate_id: str, turn: dict[str, Any], new_sources: list[dict[str, Any]]
    ) -> None:
        did = uuid.UUID(debate_id)
        turn = clean_deep(turn)
        new_sources = clean_deep(new_sources)
        async with self._sessions() as s:
            existing_numbers = set(
                await s.scalars(select(Source.number).where(Source.debate_id == did))
            )
            for src in new_sources:
                if src["number"] in existing_numbers:
                    continue
                s.add(Source(debate_id=did, **src))

            row = await s.scalar(select(Turn).where(Turn.debate_id == did, Turn.seq == turn["seq"]))
            if row is None:
                row = Turn(debate_id=did, seq=turn["seq"])
                s.add(row)
            row.round = turn["round"]
            row.phase = Phase(turn["phase"])
            row.speaker = Speaker(turn["speaker"])
            row.content = turn["content"]
            row.search_queries = list(turn.get("search_queries", []))
            await s.commit()

    async def set_round(
        self, debate_id: str, current_round: int, total_rounds: int | None = None
    ) -> None:
        async with self._sessions() as s:
            debate = await s.get(Debate, uuid.UUID(debate_id))
            if debate is None:
                return
            debate.current_round = current_round
            if total_rounds is not None:
                debate.total_rounds = total_rounds
            await s.commit()

    async def save_summary(self, debate_id: str, summary: dict[str, Any]) -> None:
        did = uuid.UUID(debate_id)
        summary = clean_deep(summary)
        async with self._sessions() as s:
            row = await s.get(Summary, did)
            if row is None:
                row = Summary(debate_id=did)
                s.add(row)
            row.pro_summary = summary["pro_summary"]
            row.con_summary = summary["con_summary"]
            row.final_summary = summary["final_summary"]
            await s.commit()

    async def set_status(
        self, debate_id: str, status: DebateStatus, error: str | None = None
    ) -> None:
        async with self._sessions() as s:
            debate = await s.get(Debate, uuid.UUID(debate_id))
            if debate is None:
                return
            debate.status = status
            debate.error = error
            if status != DebateStatus.running:
                debate.completed_at = datetime.now(UTC)
            await s.commit()

    async def running_debates(self) -> list[tuple[str, str]]:
        async with self._sessions() as s:
            rows = await s.execute(
                select(Debate.id, Debate.topic_raw).where(Debate.status == DebateStatus.running)
            )
            return [(str(i), t) for i, t in rows.all()]

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Literal, Protocol

from app.search.exa import SearchHit

Role = Literal["moderator", "debater", "summary"]


class DebateStoreProtocol(Protocol):
    async def save_framing(
        self, debate_id: str, proposition: str, pro_stance: str, con_stance: str
    ) -> None: ...

    async def save_turn(
        self, debate_id: str, turn: dict[str, Any], new_sources: list[dict[str, Any]]
    ) -> None: ...

    async def set_round(
        self, debate_id: str, current_round: int, total_rounds: int | None = None
    ) -> None: ...

    async def save_summary(self, debate_id: str, summary: dict[str, Any]) -> None: ...


@dataclass
class GraphDeps:
    """그래프 노드가 쓰는 외부 의존성. LangGraph runtime context로 전달되며 체크포인트에 저장되지 않는다."""

    llm: Callable[[Role], Any]  # 역할 -> 채팅 모델 (astream / bind_tools / with_structured_output)
    search: Callable[[str], Awaitable[list[SearchHit]]]
    emit: Callable[[str, dict[str, Any]], Awaitable[None]]
    store: DebateStoreProtocol
    max_search_calls: int = 20

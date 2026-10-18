"""테스트용 가짜 LLM / 검색 / 저장소."""

import asyncio
import itertools
from typing import Any

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, ToolMessage

from app.graph.nodes import DebateSummary, Framing, RoundDecision
from app.search.exa import SearchHit


class FakeChat:
    """astream / bind_tools / with_structured_output 만 흉내 낸다."""

    def __init__(self, world: "FakeWorld", tools: bool = False):
        self.world = world
        self.tools = tools

    def bind_tools(self, tools: list[Any], **kwargs: Any) -> "FakeChat":
        return FakeChat(self.world, tools=kwargs.get("tool_choice") != "none")

    def with_structured_output(self, schema: type) -> "FakeStructured":
        return FakeStructured(self.world, schema)

    async def astream(self, messages: list[Any]):
        self.world.calls += 1
        human = next(m for m in messages if isinstance(m, HumanMessage)).content
        system = messages[0].content
        is_debater = "토론자" in system
        tool_results = [m for m in messages if isinstance(m, ToolMessage)]

        if is_debater and self.tools and not tool_results:
            if self.world.skip_search_once and "[주의]" not in human:
                self.world.skip_search_once = False
                for piece in ["근거 없는 ", "주장입니다."]:
                    yield AIMessageChunk(content=piece)
                return
            yield AIMessage(
                content="",
                tool_calls=[{"name": "web_search", "args": {"query": "테스트 검색"}, "id": "call-1", "type": "tool_call"}],
            )
            return

        if is_debater and tool_results:
            number = tool_results[-1].content.split("]")[0].lstrip("[")
            text = f"근거가 있는 주장입니다[{number}]. 지어낸 출처는 지워집니다[999]."
        elif is_debater:
            text = "최종 발언입니다[1]."
        else:
            text = "사회자 발언입니다."
        if self.world.slow:
            await asyncio.sleep(0.01)
        for piece in [text[: len(text) // 2], text[len(text) // 2 :]]:
            yield AIMessageChunk(content=piece)


class FakeStructured:
    def __init__(self, world: "FakeWorld", schema: type):
        self.world = world
        self.schema = schema

    async def ainvoke(self, messages: list[Any]) -> Any:
        if self.schema is Framing:
            self.world.framing_calls += 1
            return Framing(
                proposition="사형제도를 폐지해야 한다", pro_stance="폐지해야 한다", con_stance="유지해야 한다"
            )
        if self.schema is RoundDecision:
            return RoundDecision(continue_debate=next(self.world.decisions), reason="테스트")
        if self.schema is DebateSummary:
            return DebateSummary(
                pro_summary="찬성 요약[1][999]",
                con_summary="반대 요약",
                overview="개요",
                key_issues=["쟁점"],
                agreements=[],
                disagreements=["대립"],
                open_questions=["질문"],
            )
        raise AssertionError(self.schema)


class FakeStore:
    def __init__(self, debate_id: str = "d1", topic: str = "사형제도"):
        self.framing: dict[str, Any] | None = None
        self.turns: dict[int, dict[str, Any]] = {}
        self.sources: dict[int, dict[str, Any]] = {}
        self.summary: dict[str, Any] | None = None
        self.rounds: list[tuple[int, int | None]] = []
        self.status: dict[str, Any] = {debate_id: ("running", None)}
        self.topics = {debate_id: topic}
        self.turn_saved = asyncio.Event()
        self.pause_after: int | None = None

    async def save_framing(self, debate_id, proposition, pro_stance, con_stance):
        self.framing = {"proposition": proposition, "pro_stance": pro_stance, "con_stance": con_stance}

    async def save_turn(self, debate_id, turn, new_sources):
        self.turns[turn["seq"]] = turn
        for s in new_sources:
            self.sources.setdefault(s["number"], s)
        if self.pause_after is not None and len(self.turns) >= self.pause_after:
            self.turn_saved.set()
            await asyncio.sleep(3600)  # 서버가 죽기 직전처럼 멈춘다

    async def set_round(self, debate_id, current_round, total_rounds=None):
        self.rounds.append((current_round, total_rounds))

    async def save_summary(self, debate_id, summary):
        self.summary = summary

    async def set_status(self, debate_id, status, error=None):
        self.status[debate_id] = (status.value, error)

    async def running_debates(self):
        return [(d, self.topics[d]) for d, (s, _) in self.status.items() if s == "running"]


class FakeWorld:
    def __init__(self, decisions: list[bool] | None = None):
        self.decisions = itertools.cycle(decisions or [False])
        self.skip_search_once = False
        self.slow = False
        self.calls = 0
        self.framing_calls = 0
        self.events: list[tuple[str, dict[str, Any]]] = []
        self._counter = itertools.count(1)

    def llm(self, role: str) -> FakeChat:
        return FakeChat(self)

    async def search(self, query: str) -> list[SearchHit]:
        n = next(self._counter)
        return [SearchHit(url=f"https://news.example.com/{n}", title=f"기사 {n}", text=f"본문 {n}")]

    async def emit(self, event: str, data: dict[str, Any]) -> None:
        self.events.append((event, data))

"""발언 한 번을 생성한다: (토론자라면) 웹 검색 도구 루프 → 최종 발언 토큰 스트리밍."""

from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import BaseMessage, ToolMessage
from pydantic import BaseModel, Field

from app.graph.deps import GraphDeps
from app.graph.sources import format_hits_for_model, register_hits


class web_search(BaseModel):  # noqa: N801 - 도구 이름이 곧 클래스 이름
    """웹에서 토론 근거 자료를 검색한다. 하나의 구체적인 검색어를 넣는다. 필요하면 여러 번 호출한다."""

    query: str = Field(description="검색어 (한국어 권장)")


SEARCH_LIMIT_NOTICE = "검색 한도에 도달했습니다. 지금까지 찾은 자료만으로 발언을 작성하세요."
SEARCH_ERROR_NOTICE = "검색 중 오류가 발생했습니다. 다른 검색어를 쓰거나 이미 찾은 자료로 발언하세요."


@dataclass
class SpeakResult:
    content: str
    sources: list[dict[str, Any]]
    added_sources: list[dict[str, Any]] = field(default_factory=list)
    queries: list[str] = field(default_factory=list)


def _text_of(message: Any) -> str:
    return str(getattr(message, "text", "") or "")


async def speak(
    deps: GraphDeps,
    *,
    seq: int,
    model: Any,
    messages: list[BaseMessage],
    sources: list[dict[str, Any]],
    allow_search: bool,
) -> SpeakResult:
    all_sources = list(sources)
    added: list[dict[str, Any]] = []
    queries: list[str] = []
    convo = list(messages)
    search_calls = 0
    tools_enabled = allow_search

    while True:
        if tools_enabled:
            runnable = model.bind_tools([web_search])
        elif allow_search:
            # 검색 한도 도달: 대화 기록에 도구 호출이 있으므로 도구 정의는 유지하고 호출만 막는다.
            runnable = model.bind_tools([web_search], tool_choice="none")
        else:
            runnable = model
        acc = None
        streamed = False
        async for chunk in runnable.astream(convo):
            acc = chunk if acc is None else acc + chunk
            delta = _text_of(chunk)
            if delta:
                streamed = True
                await deps.emit("token", {"seq": seq, "delta": delta})

        tool_calls = getattr(acc, "tool_calls", None) or []
        if not (tools_enabled and tool_calls):
            return SpeakResult(_text_of(acc).strip() if acc is not None else "", all_sources, added, queries)

        # 도구 호출 단계: 그 전에 흘러나온 텍스트는 발언이 아니므로 지운다.
        if streamed:
            await deps.emit("turn_reset", {"seq": seq})
        convo.append(acc)
        for call in tool_calls:
            if search_calls >= deps.max_search_calls:
                content = SEARCH_LIMIT_NOTICE
            else:
                search_calls += 1
                query = str((call.get("args") or {}).get("query", "")).strip()
                queries.append(query)
                await deps.emit("search", {"seq": seq, "query": query})
                try:
                    hits = await deps.search(query) if query else []
                    all_sources, new, numbered = register_hits(all_sources, hits)
                    added.extend(new)
                    content = format_hits_for_model(numbered)
                except Exception:  # 검색 실패는 발언 실패로 이어지지 않게 한다
                    content = SEARCH_ERROR_NOTICE
            convo.append(ToolMessage(content=content, tool_call_id=call["id"]))
        if search_calls >= deps.max_search_calls:
            tools_enabled = False

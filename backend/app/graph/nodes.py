from collections.abc import Callable
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.runtime import Runtime
from pydantic import BaseModel, Field

from app.graph import prompts
from app.graph.citations import clean_citations
from app.graph.deps import GraphDeps, Role
from app.graph.speaker import speak
from app.graph.state import CLOSING_ROUND, MAX_ROUNDS, MIN_ROUNDS, DebateState

NO_CITATION_RETRY_NOTE = (
    "직전 초안에는 검색 결과에 근거한 유효한 출처 번호 [n]이 하나도 없어 폐기되었다. "
    "반드시 web_search로 근거를 찾고, 근거를 찾은 주장에만 [n]을 붙여 다시 작성하라. "
    "근거를 찾지 못한 주장은 버리고 다른 주장을 선택하라."
)


class Framing(BaseModel):
    proposition: str = Field(description="찬반이 갈리는 한 문장 논제")
    pro_stance: str = Field(description="찬성 측이 옹호할 입장 한 문장")
    con_stance: str = Field(description="반대 측이 옹호할 입장 한 문장")


class RoundDecision(BaseModel):
    continue_debate: bool = Field(description="다음 라운드로 연장할지 여부")
    reason: str = Field(description="결정 이유 한 문장")


class DebateSummary(BaseModel):
    pro_summary: str
    con_summary: str
    overview: str
    key_issues: list[str]
    agreements: list[str]
    disagreements: list[str]
    open_questions: list[str]


async def _structured(deps: GraphDeps, role: Role, schema: type[BaseModel], system: str, user: str) -> Any:
    model = deps.llm(role).with_structured_output(schema)
    return await model.ainvoke([SystemMessage(system), HumanMessage(user)])


async def _turn(
    state: DebateState,
    deps: GraphDeps,
    *,
    speaker: str,
    phase: str,
    round_no: int,
    role: Role,
    system: str,
    user: Callable[[str | None], str],
    allow_search: bool = False,
    require_citation: bool = False,
) -> dict[str, Any]:
    seq = state["seq"]
    await deps.emit(
        "turn_start", {"seq": seq, "speaker": speaker, "round": round_no, "phase": phase}
    )

    sources = list(state.get("sources", []))
    added: list[dict[str, Any]] = []
    queries: list[str] = []
    retry_note: str | None = None
    attempts = 2 if require_citation else 1
    content = ""

    for attempt in range(attempts):
        result = await speak(
            deps,
            seq=seq,
            model=deps.llm(role),
            messages=[SystemMessage(system), HumanMessage(user(retry_note))],
            sources=sources,
            allow_search=allow_search,
        )
        sources = result.sources
        added.extend(result.added_sources)
        queries.extend(result.queries)
        content, used = clean_citations(result.content, {s["number"] for s in sources})
        ok = bool(content) and (used or not require_citation)
        if ok or attempt == attempts - 1:
            break
        await deps.emit("turn_reset", {"seq": seq})
        retry_note = NO_CITATION_RETRY_NOTE

    if not content:
        raise RuntimeError(f"발언 생성에 실패했습니다 (seq={seq}, speaker={speaker}).")

    turn = {
        "seq": seq,
        "round": round_no,
        "phase": phase,
        "speaker": speaker,
        "content": content,
        "search_queries": queries,
    }
    await deps.store.save_turn(state["debate_id"], turn, added)
    await deps.emit("turn_end", {"turn": turn, "sources": added})
    return {
        "seq": seq + 1,
        "transcript": [*state.get("transcript", []), turn],
        "sources": sources,
    }


async def frame_topic(state: DebateState, runtime: Runtime[GraphDeps]) -> dict[str, Any]:
    deps = runtime.context
    framing: Framing = await _structured(
        deps, "moderator", Framing, prompts.FRAMING_SYSTEM, prompts.framing_user(state["topic"])
    )
    update = framing.model_dump()
    await deps.store.save_framing(state["debate_id"], **update)
    await deps.emit("framed", update)

    framed_state: DebateState = {**state, **update}  # type: ignore[typeddict-item]
    turn_update = await _turn(
        framed_state,
        deps,
        speaker="moderator",
        phase="opening_remarks",
        round_no=0,
        role="moderator",
        system=prompts.MODERATOR_SYSTEM,
        user=lambda _: prompts.opening_remarks_user(framed_state),
    )
    return {**update, **turn_update}


async def moderator_round(state: DebateState, runtime: Runtime[GraphDeps]) -> dict[str, Any]:
    deps = runtime.context
    round_no = state["round"] + 1
    await deps.store.set_round(state["debate_id"], round_no)
    await deps.emit("round", {"round": round_no})
    turn_update = await _turn(
        state,
        deps,
        speaker="moderator",
        phase="moderation",
        round_no=round_no,
        role="moderator",
        system=prompts.MODERATOR_SYSTEM,
        user=lambda _: prompts.moderator_round_user(state, round_no, round_no > MIN_ROUNDS),
    )
    return {"round": round_no, **turn_update}


def _debater_node(side: str):
    async def node(state: DebateState, runtime: Runtime[GraphDeps]) -> dict[str, Any]:
        round_no = state["round"]
        return await _turn(
            state,
            runtime.context,
            speaker=side,
            phase="opening" if round_no == 1 else "rebuttal",
            round_no=round_no,
            role="debater",
            system=prompts.debater_system(state, side),
            user=lambda note: prompts.debater_user(state, side, round_no, note),
            allow_search=True,
            require_citation=True,
        )

    node.__name__ = f"{side}_speech"
    return node


pro_speech = _debater_node("pro")
con_speech = _debater_node("con")


async def round_check(state: DebateState, runtime: Runtime[GraphDeps]) -> dict[str, Any]:
    deps = runtime.context
    round_no = state["round"]
    if round_no < MIN_ROUNDS:
        return {"continue_debate": True}

    if round_no >= MAX_ROUNDS:
        decision = RoundDecision(continue_debate=False, reason="최대 라운드에 도달했습니다.")
    else:
        decision = await _structured(
            deps,
            "moderator",
            RoundDecision,
            prompts.ROUND_DECISION_SYSTEM,
            prompts.round_decision_user(state),
        )
    await deps.emit(
        "round_decision",
        {"round": round_no, "continue": decision.continue_debate, "reason": decision.reason},
    )
    if decision.continue_debate:
        return {"continue_debate": True}
    await deps.store.set_round(state["debate_id"], round_no, total_rounds=round_no)
    return {"continue_debate": False, "total_rounds": round_no}


def route_after_round(state: DebateState) -> str:
    return "moderator_round" if state.get("continue_debate") else "closing_intro"


async def closing_intro(state: DebateState, runtime: Runtime[GraphDeps]) -> dict[str, Any]:
    return await _turn(
        state,
        runtime.context,
        speaker="moderator",
        phase="moderation",
        round_no=CLOSING_ROUND,
        role="moderator",
        system=prompts.MODERATOR_SYSTEM,
        user=lambda _: prompts.closing_intro_user(state),
    )


def _closing_node(side: str):
    async def node(state: DebateState, runtime: Runtime[GraphDeps]) -> dict[str, Any]:
        return await _turn(
            state,
            runtime.context,
            speaker=side,
            phase="closing",
            round_no=CLOSING_ROUND,
            role="debater",
            system=prompts.debater_system(state, side, closing=True),
            user=lambda _: prompts.closing_user(state),
        )

    node.__name__ = f"{side}_closing"
    return node


pro_closing = _closing_node("pro")
con_closing = _closing_node("con")


async def summarize(state: DebateState, runtime: Runtime[GraphDeps]) -> dict[str, Any]:
    deps = runtime.context
    result: DebateSummary = await _structured(
        deps, "summary", DebateSummary, prompts.SUMMARY_SYSTEM, prompts.summary_user(state)
    )
    valid = {s["number"] for s in state.get("sources", [])}
    pro, _ = clean_citations(result.pro_summary, valid)
    con, _ = clean_citations(result.con_summary, valid)
    summary = {
        "pro_summary": pro,
        "con_summary": con,
        "final_summary": {
            "overview": result.overview,
            "key_issues": result.key_issues,
            "agreements": result.agreements,
            "disagreements": result.disagreements,
            "open_questions": result.open_questions,
        },
    }
    await deps.store.save_summary(state["debate_id"], summary)
    await deps.emit("summary", summary)
    return {"summary": summary}

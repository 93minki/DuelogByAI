from typing import Any, TypedDict

CLOSING_ROUND = 99
MIN_ROUNDS = 3
MAX_ROUNDS = 5


class DebateState(TypedDict, total=False):
    debate_id: str
    topic: str
    proposition: str
    pro_stance: str
    con_stance: str
    round: int  # 현재 라운드 (0 = 개회 전)
    total_rounds: int | None
    continue_debate: bool
    seq: int  # 다음 발언 순번
    transcript: list[dict[str, Any]]  # {seq, round, phase, speaker, content}
    sources: list[dict[str, Any]]
    summary: dict[str, Any] | None


def initial_state(debate_id: str, topic: str) -> DebateState:
    return {
        "debate_id": debate_id,
        "topic": topic,
        "round": 0,
        "total_rounds": None,
        "continue_debate": True,
        "seq": 0,
        "transcript": [],
        "sources": [],
        "summary": None,
    }

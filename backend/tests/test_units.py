import pytest

from app.debates.broadcaster import Broadcaster
from app.graph.citations import clean_citations
from app.graph.sources import register_hits
from app.guard.jev import AMBIGUOUS_MESSAGE, REASON_MESSAGES, build_questions, evaluate
from app.search.exa import SearchHit


@pytest.mark.parametrize(
    ("text", "valid", "expected", "used"),
    [
        ("A[1]. B[2].", {1, 2}, "A[1]. B[2].", [1, 2]),
        ("A[1, 3].", {1, 3}, "A[1][3].", [1, 3]),
        ("A[7].", {1}, "A.", []),
        ("A[1,7] B[1]", {1}, "A[1] B[1]", [1]),
        ("인용 없음", {1}, "인용 없음", []),
    ],
)
def test_clean_citations(text, valid, expected, used):
    assert clean_citations(text, valid) == (expected, used)


def test_register_hits_reuses_numbers_for_same_url():
    hits = [SearchHit("https://a.com/x", "A", "a"), SearchHit("https://b.com", "B", "b")]
    sources, added, numbered = register_hits([], hits)
    assert [s["number"] for s in sources] == [1, 2]
    assert len(added) == 2

    again = [SearchHit("https://a.com/x/", "A", "a"), SearchHit("https://c.com", "C", "c")]
    sources, added, numbered = register_hits(sources, again)
    assert [n for n, _ in numbered] == [1, 3]
    assert [s["number"] for s in added] == [3]


def _jev(choice, confidence, reason="none"):
    return {
        "model": "jev-1.13.0",
        "answers": {
            "verdict": {"type": "choice", "choice": choice, "confidence": confidence, "probabilities": {}},
            "reason": {"type": "choice", "choice": reason, "confidence": 0.9, "probabilities": {}},
        },
    }


def test_jev_debatable_passes():
    assert evaluate(_jev("debatable", 0.8), 0.6).status == "ok"


def test_jev_rejected_uses_reason_message():
    v = evaluate(_jev("not_debatable", 0.9, "harmful"), 0.6)
    assert (v.status, v.reason, v.message) == ("rejected", "harmful", REASON_MESSAGES["harmful"])


@pytest.mark.parametrize(
    "response",
    [_jev("ambiguous", 0.9), _jev("debatable", 0.4), _jev("not_debatable", 0.3), {"answers": {}}],
)
def test_jev_ambiguous_or_low_confidence(response):
    v = evaluate(response, 0.6)
    assert v.status == "ambiguous"
    assert v.message == AMBIGUOUS_MESSAGE


def test_jev_questions_shape():
    q = build_questions()
    assert q["verdict"]["type"] == "choice"
    assert set(q["verdict"]["criteria"]) == {"debatable", "not_debatable", "ambiguous"}


async def test_broadcaster_tracks_partial_and_fans_out():
    b = Broadcaster()
    q = b.subscribe()
    await b.emit("turn_start", {"seq": 1, "speaker": "pro"})
    await b.emit("search", {"seq": 1, "query": "q"})
    await b.emit("token", {"seq": 1, "delta": "안녕"})
    assert b.partial["text"] == "안녕"
    assert b.partial["searches"] == ["q"]
    await b.emit("turn_reset", {"seq": 1})
    assert b.partial["text"] == ""
    await b.emit("turn_end", {"turn": {"seq": 1}})
    assert b.partial is None
    b.close()
    events = []
    while (item := q.get_nowait()) is not None:
        events.append(item[0])
    assert events == ["turn_start", "search", "token", "turn_reset", "turn_end"]


def test_clean_text_removes_control_chars_but_keeps_newlines():
    from app.text import clean_deep, clean_text

    assert clean_text("a\x00b\x18c\n\td") == "abc\n\td"
    assert clean_deep({"q": ["\x00검색\x19"], "n": 1}) == {"q": ["검색"], "n": 1}


def test_clean_query_decodes_literal_escapes():
    from app.text import clean_query

    assert clean_query("\\uc54c\\uace0  \\ubcf4\\ub2c8 \x00") == "알고 보니"

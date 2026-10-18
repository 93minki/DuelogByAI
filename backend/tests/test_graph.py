import asyncio

from langgraph.checkpoint.memory import InMemorySaver

from app.debates.runner import DebateRunner
from app.graph.builder import build_graph
from app.graph.deps import GraphDeps
from app.graph.state import CLOSING_ROUND, initial_state
from tests.fakes import FakeStore, FakeWorld


async def run_debate(world: FakeWorld, store: FakeStore):
    graph = build_graph().compile(checkpointer=InMemorySaver())
    deps = GraphDeps(llm=world.llm, search=world.search, emit=world.emit, store=store)
    config = {"configurable": {"thread_id": "d1"}, "recursion_limit": 100}
    return await graph.ainvoke(initial_state("d1", "사형제도"), config, context=deps)


def speakers(store: FakeStore):
    return [(t["round"], t["speaker"], t["phase"]) for _, t in sorted(store.turns.items())]


async def test_default_three_rounds_then_closing_and_summary():
    world, store = FakeWorld(decisions=[False]), FakeStore()
    state = await run_debate(world, store)

    assert store.framing["proposition"] == "사형제도를 폐지해야 한다"
    expected = [(0, "moderator", "opening_remarks")]
    for r in (1, 2, 3):
        phase = "opening" if r == 1 else "rebuttal"
        expected += [(r, "moderator", "moderation"), (r, "pro", phase), (r, "con", phase)]
    expected += [
        (CLOSING_ROUND, "moderator", "moderation"),
        (CLOSING_ROUND, "pro", "closing"),
        (CLOSING_ROUND, "con", "closing"),
    ]
    assert speakers(store) == expected
    assert state["total_rounds"] == 3
    assert store.rounds[-1] == (3, 3)
    assert store.summary["pro_summary"] == "찬성 요약[1]"  # 존재하지 않는 [999] 제거
    assert store.summary["final_summary"]["disagreements"] == ["대립"]


async def test_debater_citations_are_validated_and_sources_numbered_globally():
    world, store = FakeWorld(), FakeStore()
    await run_debate(world, store)

    debater_turns = [t for t in store.turns.values() if t["speaker"] != "moderator" and t["phase"] != "closing"]
    for t in debater_turns:
        assert "[999]" not in t["content"]
        assert t["search_queries"] == ["테스트 검색"]
    assert sorted(store.sources) == list(range(1, len(debater_turns) + 1))
    assert any(e == "search" for e, _ in world.events)
    assert not any(e == "turn_reset" for e, _ in world.events)


async def test_moderator_can_extend_until_max_five_rounds():
    world, store = FakeWorld(decisions=[True]), FakeStore()
    state = await run_debate(world, store)
    assert state["total_rounds"] == 5
    decisions = [d for e, d in world.events if e == "round_decision"]
    assert [d["round"] for d in decisions] == [3, 4, 5]
    assert decisions[-1]["continue"] is False


async def test_extension_by_one_round():
    world, store = FakeWorld(decisions=[True, False]), FakeStore()
    state = await run_debate(world, store)
    assert state["total_rounds"] == 4


async def test_uncited_draft_is_discarded_and_regenerated():
    world, store = FakeWorld(), FakeStore()
    world.skip_search_once = True
    await run_debate(world, store)

    first_pro = store.turns[2]
    assert first_pro["speaker"] == "pro"
    assert "근거 없는" not in first_pro["content"]
    assert "[1]" in first_pro["content"]
    assert ("turn_reset", {"seq": 2}) in world.events


async def test_runner_resumes_from_checkpoint_after_server_restart():
    checkpointer = InMemorySaver()
    graph = build_graph().compile(checkpointer=checkpointer)
    world, store = FakeWorld(), FakeStore()

    store.pause_after = 5
    first = DebateRunner(
        graph=graph, checkpointer=checkpointer, store=store, llm=world.llm, search=world.search, max_search_calls=20
    )
    first.start("d1", "사형제도")
    await asyncio.wait_for(store.turn_saved.wait(), timeout=5)
    await first.shutdown()  # 서버 종료: 상태는 running 그대로
    assert store.status["d1"][0] == "running"

    store.pause_after = None
    second = DebateRunner(
        graph=graph, checkpointer=checkpointer, store=store, llm=world.llm, search=world.search, max_search_calls=20
    )
    await second.recover()
    await second.wait("d1")

    assert store.status["d1"] == ("completed", None)
    assert len(store.turns) == 13
    assert sorted(store.turns) == list(range(13))
    assert world.framing_calls == 1  # 처음부터 다시 시작하지 않고 체크포인트에서 이어 갔다


async def test_runner_stop_marks_debate_stopped():
    checkpointer = InMemorySaver()
    graph = build_graph().compile(checkpointer=checkpointer)
    world, store = FakeWorld(), FakeStore()
    store.pause_after = 3
    runner = DebateRunner(
        graph=graph, checkpointer=checkpointer, store=store, llm=world.llm, search=world.search, max_search_calls=20
    )
    runner.start("d1", "사형제도")
    await asyncio.wait_for(store.turn_saved.wait(), timeout=5)
    assert await runner.stop("d1") is True
    assert store.status["d1"] == ("stopped", None)
    assert store.summary is None
    assert not runner.is_running("d1")

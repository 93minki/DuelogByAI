import uuid

from sqlalchemy import select

from app.guard.jev import TopicVerdict
from app.models import Debate, DebateStatus, Phase, Speaker, Turn
from tests.conftest import make_client


async def test_signup_login_me_logout(client):
    r = await client.post("/api/auth/signup", json={"email": "A@Example.com", "password": "password123"})
    assert r.status_code == 201
    assert r.json()["email"] == "a@example.com"
    assert (await client.get("/api/auth/me")).status_code == 200

    assert (await client.post("/api/auth/logout")).status_code == 204
    client.cookies.clear()
    assert (await client.get("/api/auth/me")).status_code == 401

    r = await client.post("/api/auth/login", json={"email": "a@example.com", "password": "wrong-pass"})
    assert r.status_code == 401
    r = await client.post("/api/auth/login", json={"email": "a@example.com", "password": "password123"})
    assert r.status_code == 200
    assert (await client.get("/api/auth/me")).status_code == 200


async def test_signup_validation_and_duplicate(client):
    assert (await client.post("/api/auth/signup", json={"email": "x@example.com", "password": "short"})).status_code == 422
    assert (await client.post("/api/auth/signup", json={"email": "nope", "password": "password123"})).status_code == 422
    assert (await client.post("/api/auth/signup", json={"email": "x@example.com", "password": "password123"})).status_code == 201
    assert (await client.post("/api/auth/signup", json={"email": "x@example.com", "password": "password123"})).status_code == 409


async def test_debates_require_login(client):
    assert (await client.get("/api/debates")).status_code == 401
    assert (await client.post("/api/debates", json={"topic": "사형제도 폐지"})).status_code == 401


async def test_create_debate_starts_runner(authed, app):
    r = await authed.post("/api/debates", json={"topic": "  사형제도를   폐지해야 한다  "})
    assert r.status_code == 201
    body = r.json()
    assert body["topic_raw"] == "사형제도를 폐지해야 한다"
    assert body["status"] == "running"
    assert app.state.runner.started == [(body["id"], "사형제도를 폐지해야 한다")]

    listed = (await authed.get("/api/debates")).json()
    assert [d["id"] for d in listed] == [body["id"]]


async def test_topic_length_validation(authed, app):
    assert (await authed.post("/api/debates", json={"topic": "가"})).status_code == 422
    assert (await authed.post("/api/debates", json={"topic": "가" * 201})).status_code == 422
    assert app.state.judge.calls == []


async def test_rejected_and_ambiguous_topics_do_not_create(authed, app):
    app.state.judge.verdict = TopicVerdict("rejected", "factual", "사실 질문입니다.")
    r = await authed.post("/api/debates", json={"topic": "물의 끓는점은 몇 도인가"})
    assert r.status_code == 422
    assert r.json()["detail"] == {"status": "rejected", "reason": "factual", "message": "사실 질문입니다."}

    app.state.judge.verdict = TopicVerdict("ambiguous", None, "구체적으로")
    r = await authed.post("/api/debates", json={"topic": "요즘 사회 문제"})
    assert r.json()["detail"]["status"] == "ambiguous"

    assert (await authed.get("/api/debates")).json() == []
    assert app.state.runner.started == []


async def test_only_one_running_debate(authed):
    assert (await authed.post("/api/debates", json={"topic": "사형제도를 폐지해야 한다"})).status_code == 201
    assert (await authed.post("/api/debates", json={"topic": "기본소득을 도입해야 한다"})).status_code == 409


async def test_daily_limit(authed, session_factory, monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "daily_debate_limit", 2)
    for i in range(2):
        r = await authed.post("/api/debates", json={"topic": f"주제 번호 {i} 를 도입해야 한다"})
        assert r.status_code == 201
        async with session_factory() as s:
            d = await s.get(Debate, uuid.UUID(r.json()["id"]))
            d.status = DebateStatus.completed
            await s.commit()
    r = await authed.post("/api/debates", json={"topic": "세 번째 주제를 도입해야 한다"})
    assert r.status_code == 429


async def test_detail_ownership_stop_and_delete(authed, app, session_factory):
    debate_id = (await authed.post("/api/debates", json={"topic": "사형제도를 폐지해야 한다"})).json()["id"]
    async with session_factory() as s:
        s.add(Turn(debate_id=uuid.UUID(debate_id), seq=0, round=0, phase=Phase.opening_remarks,
                   speaker=Speaker.moderator, content="개회", search_queries=[]))
        await s.commit()

    detail = (await authed.get(f"/api/debates/{debate_id}")).json()
    assert detail["turns"][0]["content"] == "개회"
    assert detail["summary"] is None

    async with make_client(app) as other:
        await other.post("/api/auth/signup", json={"email": "other@example.com", "password": "password123"})
        assert (await other.get(f"/api/debates/{debate_id}")).status_code == 404
        assert (await other.delete(f"/api/debates/{debate_id}")).status_code == 404

    r = await authed.post(f"/api/debates/{debate_id}/stop")
    assert r.status_code == 200
    assert r.json()["status"] == "stopped"
    assert (await authed.post(f"/api/debates/{debate_id}/stop")).status_code == 409

    assert (await authed.delete(f"/api/debates/{debate_id}")).status_code == 204
    assert (await authed.get(f"/api/debates/{debate_id}")).status_code == 404
    assert app.state.runner.deleted == [debate_id]
    async with session_factory() as s:
        remaining = await s.scalars(select(Turn).where(Turn.debate_id == uuid.UUID(debate_id)))
        assert remaining.all() == []


async def test_stream_of_finished_debate_sends_snapshot(authed):
    debate_id = (await authed.post("/api/debates", json={"topic": "사형제도를 폐지해야 한다"})).json()["id"]
    await authed.post(f"/api/debates/{debate_id}/stop")
    async with authed.stream("GET", f"/api/debates/{debate_id}/stream") as r:
        assert r.status_code == 200
        text = "".join([chunk async for chunk in r.aiter_text()])
    assert "event: snapshot" in text
    assert '"status":"stopped"' in text.replace(" ", "")

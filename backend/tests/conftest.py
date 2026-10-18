from collections.abc import AsyncIterator

import httpx
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db import Base, get_session
from app.guard.jev import TopicVerdict
from app.main import create_app


class FakeRunner:
    def __init__(self) -> None:
        self.started: list[tuple[str, str]] = []
        self.stopped: list[str] = []
        self.deleted: list[str] = []

    def start(self, debate_id: str, topic: str, *, resume: bool = False) -> None:
        self.started.append((debate_id, topic))

    def broadcaster(self, debate_id: str):
        return None

    async def stop(self, debate_id: str) -> bool:
        self.stopped.append(debate_id)
        return False

    async def delete_thread(self, debate_id: str) -> None:
        self.deleted.append(debate_id)


class FakeJudge:
    def __init__(self) -> None:
        self.verdict = TopicVerdict("ok", raw={"model": "jev-test"})
        self.calls: list[str] = []

    async def __call__(self, topic: str) -> TopicVerdict:
        self.calls.append(topic)
        return self.verdict


@pytest.fixture
async def session_factory():
    engine = create_async_engine(
        "sqlite+aiosqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest.fixture
def app(session_factory):
    app = create_app(with_lifespan=False)

    async def override_session() -> AsyncIterator:
        async with session_factory() as s:
            yield s

    app.dependency_overrides[get_session] = override_session
    app.state.runner = FakeRunner()
    app.state.judge = FakeJudge()
    return app


def make_client(app) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


@pytest.fixture
async def client(app) -> AsyncIterator[httpx.AsyncClient]:
    async with make_client(app) as c:
        yield c


@pytest.fixture
async def authed(client) -> httpx.AsyncClient:
    r = await client.post("/api/auth/signup", json={"email": "user@example.com", "password": "password123"})
    assert r.status_code == 201
    return client

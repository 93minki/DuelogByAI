import logging
from contextlib import asynccontextmanager
from functools import partial

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.auth.router import router as auth_router
from app.config import Settings, get_settings
from app.db import SessionLocal
from app.debates.router import router as debates_router
from app.debates.runner import DebateRunner
from app.debates.store import DebateStore
from app.graph.builder import build_graph
from app.graph.deps import Role
from app.guard.jev import JevClient, judge_topic
from app.search.exa import ExaSearcher

logging.basicConfig(level=logging.INFO)


def make_llm_factory(settings: Settings):
    models = {
        "moderator": settings.openai_model_moderator,
        "debater": settings.openai_model_debater,
        "summary": settings.openai_model_summary,
    }
    cache: dict[str, ChatOpenAI] = {}

    def factory(role: Role) -> ChatOpenAI:
        if role not in cache:
            cache[role] = ChatOpenAI(
                model=models[role], api_key=settings.openai_api_key, streaming=True, max_retries=3
            )
        return cache[role]

    return factory


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    pool = AsyncConnectionPool(
        conninfo=settings.checkpoint_db_url,
        max_size=10,
        open=False,
        kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
    )
    await pool.open()
    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()

    jev = JevClient(settings.typesafe_api_key, settings.typesafe_base_url, settings.jev_model)
    searcher = ExaSearcher(settings.exa_api_key, settings.exa_num_results)
    runner = DebateRunner(
        graph=build_graph().compile(checkpointer=checkpointer),
        checkpointer=checkpointer,
        store=DebateStore(SessionLocal),
        llm=make_llm_factory(settings),
        search=searcher.search,
        max_search_calls=settings.max_search_calls_per_turn,
    )
    app.state.runner = runner
    app.state.judge = partial(judge_topic, jev, min_confidence=settings.jev_min_confidence)

    await runner.recover()
    try:
        yield
    finally:
        await runner.shutdown()
        await jev.aclose()
        await pool.close()


def create_app(*, with_lifespan: bool = True) -> FastAPI:
    app = FastAPI(title="Duelog API", lifespan=lifespan if with_lifespan else None)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(auth_router)
    app.include_router(debates_router)

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

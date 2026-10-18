"""토론 그래프를 백그라운드 태스크로 실행하고, 중단·복구를 관리한다."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from app.debates.broadcaster import Broadcaster
from app.debates.store import DebateStore
from app.graph.deps import GraphDeps, Role
from app.graph.state import initial_state
from app.models import DebateStatus
from app.search.exa import SearchHit

logger = logging.getLogger(__name__)

FAILURE_MESSAGE = "토론 진행 중 오류가 발생했습니다. 잠시 후 새 토론을 시작해 주세요."


class DebateRunner:
    def __init__(
        self,
        *,
        graph: Any,
        checkpointer: Any,
        store: DebateStore,
        llm: Callable[[Role], Any],
        search: Callable[[str], Awaitable[list[SearchHit]]],
        max_search_calls: int,
    ):
        self._graph = graph
        self._checkpointer = checkpointer
        self._store = store
        self._llm = llm
        self._search = search
        self._max_search_calls = max_search_calls
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._broadcasters: dict[str, Broadcaster] = {}
        self._stop_requested: set[str] = set()

    def is_running(self, debate_id: str) -> bool:
        return debate_id in self._tasks

    def broadcaster(self, debate_id: str) -> Broadcaster | None:
        return self._broadcasters.get(debate_id)

    def start(self, debate_id: str, topic: str, *, resume: bool = False) -> None:
        if debate_id in self._tasks:
            return
        self._broadcasters[debate_id] = Broadcaster()
        self._tasks[debate_id] = asyncio.create_task(
            self._run(debate_id, topic, resume), name=f"debate-{debate_id}"
        )

    async def wait(self, debate_id: str) -> None:
        task = self._tasks.get(debate_id)
        if task:
            await asyncio.gather(task, return_exceptions=True)

    async def stop(self, debate_id: str) -> bool:
        task = self._tasks.get(debate_id)
        if task is None:
            return False
        self._stop_requested.add(debate_id)
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        return True

    async def delete_thread(self, debate_id: str) -> None:
        try:
            await self._checkpointer.adelete_thread(debate_id)
        except Exception:
            logger.exception("체크포인트 삭제 실패: %s", debate_id)

    async def recover(self) -> None:
        """서버 시작 시 `running` 상태로 남은 토론을 마지막 체크포인트부터 이어서 실행한다."""
        for debate_id, topic in await self._store.running_debates():
            checkpoint = await self._checkpointer.aget_tuple(
                {"configurable": {"thread_id": debate_id}}
            )
            logger.info("토론 복구: %s (resume=%s)", debate_id, checkpoint is not None)
            self.start(debate_id, topic, resume=checkpoint is not None)

    async def shutdown(self) -> None:
        """서버 종료: 상태를 바꾸지 않고 태스크만 취소한다. 다음 시작 때 recover()가 이어 간다."""
        tasks = list(self._tasks.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _run(self, debate_id: str, topic: str, resume: bool) -> None:
        broadcaster = self._broadcasters[debate_id]
        deps = GraphDeps(
            llm=self._llm,
            search=self._search,
            emit=broadcaster.emit,
            store=self._store,
            max_search_calls=self._max_search_calls,
        )
        config = {"configurable": {"thread_id": debate_id}, "recursion_limit": 100}
        status, error = DebateStatus.completed, None
        try:
            graph_input = None if resume else initial_state(debate_id, topic)
            await self._graph.ainvoke(graph_input, config, context=deps)
        except asyncio.CancelledError:
            if debate_id not in self._stop_requested:  # 서버 종료로 인한 취소
                self._cleanup(debate_id)
                raise
            status = DebateStatus.stopped
        except Exception:
            logger.exception("토론 실행 실패: %s", debate_id)
            status, error = DebateStatus.failed, FAILURE_MESSAGE

        try:
            await self._store.set_status(debate_id, status, error)
            await broadcaster.emit("status", {"status": status.value, "error": error})
        finally:
            self._cleanup(debate_id)

    def _cleanup(self, debate_id: str) -> None:
        self._tasks.pop(debate_id, None)
        self._stop_requested.discard(debate_id)
        broadcaster = self._broadcasters.pop(debate_id, None)
        if broadcaster:
            broadcaster.close()

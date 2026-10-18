"""토론 하나의 실시간 이벤트를 여러 SSE 구독자에게 나눠 준다."""

import asyncio
from typing import Any

Event = tuple[str, dict[str, Any]]


class Broadcaster:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[Event | None]] = set()
        # 작성 중인 발언. 늦게 접속한 구독자에게 현재까지의 내용을 보내는 데 쓴다.
        self.partial: dict[str, Any] | None = None
        self.closed = False

    def subscribe(self) -> asyncio.Queue[Event | None]:
        queue: asyncio.Queue[Event | None] = asyncio.Queue()
        if self.closed:
            queue.put_nowait(None)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[Event | None]) -> None:
        self._subscribers.discard(queue)

    def _track(self, event: str, data: dict[str, Any]) -> None:
        if event == "turn_start":
            self.partial = {**data, "text": "", "searches": []}
        elif self.partial is not None and data.get("seq") == self.partial["seq"]:
            if event == "token":
                self.partial["text"] += data["delta"]
            elif event == "turn_reset":
                self.partial["text"] = ""
            elif event == "search":
                self.partial["searches"].append(data["query"])
        if event == "turn_end":
            self.partial = None

    async def emit(self, event: str, data: dict[str, Any]) -> None:
        self._track(event, data)
        for queue in list(self._subscribers):
            queue.put_nowait((event, data))

    def close(self) -> None:
        self.closed = True
        self.partial = None
        for queue in list(self._subscribers):
            queue.put_nowait(None)

import asyncio
import json
import uuid
from datetime import datetime, time
from typing import Annotated, Any
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sse_starlette import EventSourceResponse

from app.auth.deps import CurrentUser, SessionDep
from app.config import get_settings
from app.debates.runner import DebateRunner
from app.guard.jev import JevError
from app.models import Debate, DebateStatus
from app.schemas import DebateCreate, DebateDetail, DebateListItem

router = APIRouter(prefix="/api/debates", tags=["debates"])

KST = ZoneInfo("Asia/Seoul")


def get_runner(request: Request) -> DebateRunner:
    return request.app.state.runner


def get_judge(request: Request):
    return request.app.state.judge


RunnerDep = Annotated[DebateRunner, Depends(get_runner)]


async def _get_owned(session: SessionDep, debate_id: uuid.UUID, user_id: uuid.UUID, *, detail: bool = False) -> Debate:
    stmt = select(Debate).where(Debate.id == debate_id, Debate.user_id == user_id)
    if detail:
        stmt = stmt.options(
            selectinload(Debate.turns), selectinload(Debate.sources), selectinload(Debate.summary)
        )
    debate = await session.scalar(stmt)
    if debate is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "토론을 찾을 수 없습니다.")
    return debate


@router.get("", response_model=list[DebateListItem])
async def list_debates(user: CurrentUser, session: SessionDep) -> list[Debate]:
    rows = await session.scalars(
        select(Debate).where(Debate.user_id == user.id).order_by(Debate.created_at.desc())
    )
    return list(rows)


@router.post("", response_model=DebateListItem, status_code=status.HTTP_201_CREATED)
async def create_debate(
    body: DebateCreate,
    user: CurrentUser,
    session: SessionDep,
    runner: RunnerDep,
    judge: Annotated[Any, Depends(get_judge)],
) -> Debate:
    settings = get_settings()
    running = await session.scalar(
        select(func.count())
        .select_from(Debate)
        .where(Debate.user_id == user.id, Debate.status == DebateStatus.running)
    )
    if running:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "이미 진행 중인 토론이 있습니다. 끝나거나 종료한 뒤 시작해 주세요."
        )

    day_start = datetime.combine(datetime.now(KST).date(), time.min, tzinfo=KST)
    today_count = await session.scalar(
        select(func.count())
        .select_from(Debate)
        .where(Debate.user_id == user.id, Debate.created_at >= day_start)
    )
    if (today_count or 0) >= settings.daily_debate_limit:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"오늘 시작할 수 있는 토론 수({settings.daily_debate_limit}회)를 모두 사용했습니다.",
        )

    try:
        verdict = await judge(body.topic)
    except JevError:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "주제 판정 서비스에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요."
        ) from None
    if verdict.status != "ok":
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            {"status": verdict.status, "reason": verdict.reason, "message": verdict.message},
        )

    debate = Debate(user_id=user.id, topic_raw=body.topic, jev_result=verdict.raw)
    session.add(debate)
    await session.commit()
    runner.start(str(debate.id), debate.topic_raw)
    return debate


@router.get("/{debate_id}", response_model=DebateDetail)
async def get_debate(debate_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> Debate:
    return await _get_owned(session, debate_id, user.id, detail=True)


@router.get("/{debate_id}/stream")
async def stream_debate(
    debate_id: uuid.UUID,
    request: Request,
    user: CurrentUser,
    session: SessionDep,
    runner: RunnerDep,
) -> EventSourceResponse:
    user_id = user.id
    await _get_owned(session, debate_id, user_id)
    broadcaster = runner.broadcaster(str(debate_id))
    # 구독과 partial 읽기 사이에 await가 없어야 이벤트가 빠지지 않는다.
    queue = broadcaster.subscribe() if broadcaster else None
    partial = dict(broadcaster.partial) if broadcaster and broadcaster.partial else None

    session.expire_all()
    debate = await _get_owned(session, debate_id, user_id, detail=True)
    snapshot = DebateDetail.model_validate(debate).model_dump(mode="json")
    snapshot["partial"] = partial

    async def events():
        try:
            yield {"event": "snapshot", "data": json.dumps(snapshot, ensure_ascii=False)}
            if queue is None:
                return
            while True:
                if await request.is_disconnected():
                    break
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=10)
                except TimeoutError:
                    continue
                if item is None:
                    break
                event, data = item
                yield {"event": event, "data": json.dumps(data, ensure_ascii=False)}
        finally:
            if broadcaster and queue:
                broadcaster.unsubscribe(queue)

    return EventSourceResponse(
        events(), ping=15, headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@router.post("/{debate_id}/stop", response_model=DebateListItem)
async def stop_debate(
    debate_id: uuid.UUID, user: CurrentUser, session: SessionDep, runner: RunnerDep
) -> Debate:
    user_id = user.id
    debate = await _get_owned(session, debate_id, user_id)
    if debate.status != DebateStatus.running:
        raise HTTPException(status.HTTP_409_CONFLICT, "진행 중인 토론이 아닙니다.")
    if not await runner.stop(str(debate_id)):
        # 실행 태스크가 없는데 running으로 남은 경우(비정상 종료 등)
        debate.status = DebateStatus.stopped
        await session.commit()
    session.expire_all()
    return await _get_owned(session, debate_id, user_id)


@router.delete("/{debate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_debate(
    debate_id: uuid.UUID, user: CurrentUser, session: SessionDep, runner: RunnerDep
) -> Response:
    user_id = user.id
    await _get_owned(session, debate_id, user_id)
    await runner.stop(str(debate_id))
    session.expire_all()
    debate = await _get_owned(session, debate_id, user_id, detail=True)
    await session.delete(debate)
    await session.commit()
    await runner.delete_thread(str(debate_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)

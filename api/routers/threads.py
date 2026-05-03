"""会话（thread）相关路由。"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from agent.react_agent import ReactAgent
from api.deps import get_agent
from api.schemas import HistoryMessage, HistoryResponse, ThreadCreateResponse

router = APIRouter(prefix="/threads", tags=["threads"])


@router.post("", response_model=ThreadCreateResponse)
def create_thread() -> ThreadCreateResponse:
    return ThreadCreateResponse(thread_id=str(uuid.uuid4()))


@router.get("/{thread_id}/history", response_model=HistoryResponse)
def get_history(
    thread_id: str,
    agent: ReactAgent = Depends(get_agent),
) -> HistoryResponse:
    messages = agent.load_history(thread_id)
    return HistoryResponse(
        thread_id=thread_id,
        messages=[HistoryMessage(**m) for m in messages],
    )

"""对话路由：非流式 + SSE 流式。"""

from __future__ import annotations

import asyncio
import uuid
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from agent.react_agent import ReactAgent
from api.deps import get_agent
from api.schemas import ChatRequest, ChatResponse
from api.sse import sse_event

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    agent: ReactAgent = Depends(get_agent),
) -> ChatResponse:
    """非流式对话：等 Agent 全部完成后一次性返回最终回答。"""
    thread_id = req.thread_id or str(uuid.uuid4())

    chunks: list[str] = []
    for chunk in agent.execute_stream(req.query, thread_id=thread_id):
        chunks.append(chunk)

    if not chunks:
        raise HTTPException(status_code=500, detail="Agent 未产生任何响应")

    return ChatResponse(thread_id=thread_id, answer=chunks[-1].strip())


@router.post("/chat/stream")
async def chat_stream(
    req: ChatRequest,
    agent: ReactAgent = Depends(get_agent),
) -> StreamingResponse:
    """流式对话：通过 SSE 把 Agent 的中间/最终输出按 chunk 推给前端。

    事件类型：
        - ``thread`` 首先推送 thread_id
        - ``message`` Agent 产出的每个 chunk
        - ``error`` 出错信息
        - ``done`` 流结束（携带 thread_id）
    """
    thread_id = req.thread_id or str(uuid.uuid4())

    async def event_source() -> AsyncIterator[bytes]:
        yield sse_event("thread", thread_id)

        loop = asyncio.get_running_loop()
        sync_gen = agent.execute_stream(req.query, thread_id=thread_id)
        sentinel = object()

        def _next_chunk():
            try:
                return next(sync_gen)
            except StopIteration:
                return sentinel

        try:
            while True:
                chunk = await loop.run_in_executor(None, _next_chunk)
                if chunk is sentinel:
                    break
                yield sse_event("message", chunk)
        except Exception as exc:  # noqa: BLE001
            yield sse_event("error", str(exc))
        finally:
            yield sse_event("done", thread_id)

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

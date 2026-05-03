"""API 请求/响应模型。"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="用户输入的问题")
    thread_id: Optional[str] = Field(
        default=None,
        description="会话 ID；不传时由服务端自动生成（在响应里返回）",
    )


class ChatResponse(BaseModel):
    thread_id: str
    answer: str


class ThreadCreateResponse(BaseModel):
    thread_id: str


class HistoryMessage(BaseModel):
    role: str
    content: str


class HistoryResponse(BaseModel):
    thread_id: str
    messages: list[HistoryMessage]


class HealthResponse(BaseModel):
    status: str

"""FastAPI 依赖注入。

- ``get_agent``：从 ``app.state`` 取出在 lifespan 中初始化好的 ReactAgent。
"""

from __future__ import annotations

from fastapi import HTTPException, Request

from agent.react_agent import ReactAgent


def get_agent(request: Request) -> ReactAgent:
    agent: ReactAgent | None = getattr(request.app.state, "agent", None)
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent 尚未初始化")
    return agent

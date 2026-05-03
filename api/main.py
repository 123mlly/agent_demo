"""FastAPI 应用工厂与启动入口。

启动方式（在 agent_project 目录下）：
    uvicorn api:app --host 0.0.0.0 --port 8000 --reload
    python -m api.main
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent.react_agent import ReactAgent
from api.routers import chat, health, threads


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时把 Agent 实例化一次，整个进程复用，避免每次请求都重建 checkpointer
    app.state.agent = ReactAgent()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="智扫通机器人智能客服 API",
        description="基于 LangGraph ReactAgent 的对话服务",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(threads.router)
    app.include_router(chat.router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)

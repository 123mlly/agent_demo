"""FastAPI 服务包入口。

对外只导出 ``app``，方便用 ``uvicorn api:app`` 启动。
"""

from api.main import app

__all__ = ["app"]

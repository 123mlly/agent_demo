"""SSE（Server-Sent Events）协议工具函数。"""

from __future__ import annotations


def sse_event(event: str, data: str) -> bytes:
    """将一条事件编码成符合 SSE 协议的字节串。

    SSE 规则：每行 ``data:`` 开头，多行 data 之间用 ``\\n``，事件之间用空行分隔。
    """
    safe_data = data.replace("\r\n", "\n").replace("\r", "\n")
    payload = "".join(f"data: {line}\n" for line in safe_data.split("\n"))
    return f"event: {event}\n{payload}\n".encode("utf-8")

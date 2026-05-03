"""Streamlit 前端：通过 HTTP / SSE 调用 FastAPI 后端。

启动顺序：
    1. 先启动后端：``uvicorn api:app --port 8000``
    2. 再启动前端：``streamlit run app.py``

可选环境变量：
    AGENT_API_BASE_URL  默认 http://localhost:8000
"""

from __future__ import annotations

import os
import time
import uuid
from typing import Iterator

import httpx
import streamlit as st

API_BASE_URL = os.getenv("AGENT_API_BASE_URL", "http://localhost:8000").rstrip("/")
REQUEST_TIMEOUT = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0)


@st.cache_resource(show_spinner=False)
def get_http_client() -> httpx.Client:
    """整个 Streamlit 进程复用一个 httpx.Client，避免每次都建连。"""
    return httpx.Client(base_url=API_BASE_URL, timeout=REQUEST_TIMEOUT)


def fetch_history(thread_id: str) -> list[dict]:
    client = get_http_client()
    try:
        resp = client.get(f"/threads/{thread_id}/history")
        resp.raise_for_status()
    except httpx.HTTPError as e:
        st.warning(f"加载历史失败：{e}")
        return []
    return resp.json().get("messages", [])


def stream_chat(prompt: str, thread_id: str) -> Iterator[str]:
    """调用后端 SSE 流式接口，逐 chunk 产出文本。

    SSE 协议解析：
        - 每条事件以空行分隔
        - ``event:`` 行表示事件类型
        - ``data:`` 行（可能多行）拼成事件数据
    只对 ``message`` 事件产出文本，``error`` 事件抛异常。
    """
    client = get_http_client()
    payload = {"query": prompt, "thread_id": thread_id}

    with client.stream("POST", "/chat/stream", json=payload) as resp:
        resp.raise_for_status()

        event_type = "message"
        data_lines: list[str] = []

        for raw_line in resp.iter_lines():
            if raw_line == "":
                if data_lines:
                    data = "\n".join(data_lines)
                    if event_type == "message":
                        yield data
                    elif event_type == "error":
                        raise RuntimeError(f"后端错误：{data}")
                    # thread / done 事件这里不需要透传到 UI
                event_type = "message"
                data_lines = []
                continue

            if raw_line.startswith("event:"):
                event_type = raw_line[len("event:"):].strip()
            elif raw_line.startswith("data:"):
                data_lines.append(raw_line[len("data:"):].lstrip(" "))


st.title("智扫通机器人智能客服")
st.caption(f"后端 API：`{API_BASE_URL}`")
st.divider()

if "thread_id" not in st.session_state:
    qp = st.query_params
    if "thread" in qp and qp["thread"]:
        st.session_state["thread_id"] = qp["thread"]
    else:
        st.session_state["thread_id"] = str(uuid.uuid4())
        st.query_params["thread"] = st.session_state["thread_id"]

if "message" not in st.session_state:
    st.session_state["message"] = fetch_history(st.session_state["thread_id"])

with st.sidebar:
    st.caption(f"thread_id: `{st.session_state['thread_id']}`")
    if st.button("新建对话"):
        new_id = str(uuid.uuid4())
        st.session_state["thread_id"] = new_id
        st.query_params["thread"] = new_id
        st.session_state["message"] = []
        st.rerun()

for message in st.session_state["message"]:
    st.chat_message(message["role"]).write(message["content"])

prompt = st.chat_input("请输入问题")

if prompt:
    st.chat_message("user").write(prompt)
    st.session_state["message"].append({"role": "user", "content": prompt})

    response_messages: list[str] = []
    with st.spinner("智能客服思考中..."):
        try:
            res_stream = stream_chat(prompt, thread_id=st.session_state["thread_id"])

            def capture(generator: Iterator[str], cache_list: list[str]) -> Iterator[str]:
                for chunk in generator:
                    cache_list.append(chunk)
                    for char in chunk:
                        time.sleep(0.01)
                        yield char

            st.chat_message("assistant").write_stream(
                capture(res_stream, response_messages)
            )
        except Exception as e:  # noqa: BLE001
            st.error(f"调用 API 失败：{e}")
        else:
            if response_messages:
                st.session_state["message"].append(
                    {"role": "assistant", "content": response_messages[-1]}
                )
            st.rerun()

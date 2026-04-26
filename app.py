import time
import uuid

import streamlit as st
from agent.react_agent import ReactAgent

st.title("智扫通机器人智能客服")
st.divider()

if "agent" not in st.session_state:
    st.session_state["agent"] = ReactAgent()

if "thread_id" not in st.session_state:
    qp = st.query_params
    if "thread" in qp and qp["thread"]:
        st.session_state["thread_id"] = qp["thread"]
    else:
        st.session_state["thread_id"] = str(uuid.uuid4())
        st.query_params["thread"] = st.session_state["thread_id"]

if "message" not in st.session_state:
    st.session_state["message"] = st.session_state["agent"].load_history(
        st.session_state["thread_id"]
    )

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

    response_messages = []
    with st.spinner("智能客服思考中..."):
        res_stream = st.session_state["agent"].execute_stream(
            prompt,
            thread_id=st.session_state["thread_id"],
        )

        def capture(generator, cache_list):
            for chunk in generator:
                cache_list.append(chunk)
                for char in chunk:
                    time.sleep(0.01)
                    yield char

        st.chat_message("assistant").write_stream(capture(res_stream, response_messages))
        st.session_state["message"].append({"role": "assistant", "content": response_messages[-1]})
        st.rerun()

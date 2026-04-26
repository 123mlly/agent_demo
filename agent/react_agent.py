import sqlite3

from langchain.agents import create_agent
from langgraph.checkpoint.sqlite import SqliteSaver

from agent.tools.agent_tools import fill_context_for_report, get_current_month, get_user_id, get_user_location, get_weather, rag_summarize
from agent.tools.middleware import log_before_model, monitor_tool, report_prompt_switch
from model.factory import chat_model
from utils.path_tool import get_abs_path


def _build_checkpointer() -> SqliteSaver:
    db_path = get_abs_path("agent_history.db")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    saver = SqliteSaver(conn)
    saver.setup()
    return saver


class ReactAgent(object):
    def __init__(self):
        self.agent = create_agent(
            model=chat_model,
            tools=[rag_summarize, get_weather, get_user_location, get_user_id, get_current_month, fill_context_for_report],
            system_prompt="你是一个助手，请根据用户输入回答问题",
            middleware=[monitor_tool, log_before_model, report_prompt_switch],
            checkpointer=_build_checkpointer(),
        )

    def load_history(self, thread_id: str) -> list[dict]:
        """从 SQLite 把指定 thread_id 的历史加载成 UI 可渲染的消息列表"""
        config = {"configurable": {"thread_id": thread_id}}
        state = self.agent.get_state(config)
        messages = state.values.get("messages", []) if state and state.values else []

        ui_messages: list[dict] = []
        for m in messages:
            if m.type == "human":
                role = "user"
            elif m.type == "ai":
                if getattr(m, "tool_calls", None):
                    continue
                role = "assistant"
            else:
                continue
            content = (m.content or "").strip()
            if content:
                ui_messages.append({"role": role, "content": content})
        return ui_messages

    def execute_stream(self, query: str, thread_id: str = "default"):
        input_dict = {
            "messages": [
                {"role": "user", "content": query}
            ]
        }
        config = {"configurable": {"thread_id": thread_id}}

        for chunk in self.agent.stream(
            input_dict,
            stream_mode="values",
            context={"report": False},
            config=config,
        ):
            latest_message = chunk["messages"][-1]
            if latest_message.content:
                yield latest_message.content.strip() + "\n"

from typing import Callable
from langchain.agents.middleware import AgentState, ModelRequest, before_model, dynamic_prompt, wrap_tool_call
from langchain_core.messages import ToolMessage
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.runtime import Runtime
from langgraph.types import Command
from utils.logger_handle import logger
from utils.prompt_loader import load_report_prompts, load_system_prompts



@before_model
def log_before_model(
    state: AgentState,
    runtime: Runtime
):
    logger.info(f"[log_before_model]: {state}")

    logger.debug(f"[log_before_model]: {state['messages']}")

    return None



@dynamic_prompt
def report_prompt_switch(
    request: ModelRequest
):
    is_report = request.runtime.context.get("report", False)
    if is_report:
        return load_report_prompts()

    return load_system_prompts()



@wrap_tool_call
def monitor_tool(
    request: ToolCallRequest, 
    handler: Callable[[ToolCallRequest], ToolMessage | Command]
)-> ToolMessage | Command:
    logger.info(f"monitor_tool: {request.tool_call['name']}")
    logger.info(f"monitor_tool: {request.tool_call['args']}")
    try:
        result = handler(request)
        logger.info(f"monitor_tool: {result}")
        if(request.tool_call['name'] == 'fill_context_for_report'):
            request.runtime.context["report"] = True
        
        return result
    except Exception as e:
        logger.error(f"monitor_tool: {e}")
        raise e

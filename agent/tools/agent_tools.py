from datetime import datetime
from langchain_core.tools import tool
from requests import get
from rag.rag_service import RagSummarizeService
import random
from utils.config_handler import agent_conf
from utils.path_tool import get_abs_path
import os
from utils.logger_handle import logger

user_ids = ["1001", "1002", "1003", "1004", "1005", "1006", "1007", "1008", "1009", "1010",]

rag_service = RagSummarizeService()

external_data = {}

@tool(description="从向量存储中检索参考资料")
def rag_summarize(query: str) -> str:
    return rag_service.summarize(query)

# 天气工具,后续可接入真实天气数据
@tool(description="获取指定城市的天气，以消息字符串的形式返回")
def get_weather(city: str) -> str:
    return f"明天，{city}天气晴，温度20-25度，空气湿度30-50%，降雨概率10%"

# 用户位置工具，后续可接入真实位置数据
@tool(description="获取当前用户所在城市，以消息字符串的形式返回")
def get_user_location() -> str:
    return random.choice(["北京", "上海", "广州", "深圳", "成都", "重庆", "杭州", "南京", "武汉", "西安"])


# 用户ID工具，后续可接入真实用户ID数据
@tool(description="获取当前用户唯一标识，以字符串的形式返回")
def get_user_id() -> str:
    return random.choice(user_ids)



@tool(description="获取当前系统当前月份，以字符串的形式返回")
def get_current_month() -> str:
    return datetime.now().strftime("%Y-%m")


def generate_external_data() -> str:
    if not external_data:
         external_data_path = get_abs_path(agent_conf["external_data_path"])
         
         if not os.path.exists(external_data_path):
            raise FileNotFoundError(f"外部数据文件不存在: {external_data_path}")

         with open(external_data_path, "r", encoding="utf-8") as f:
            for line in f.readlines()[1:]:
                arr:list[str] = line.strip().split(",")
                
                user_id: str = arr[0].replace('"', '')
                feature: str = arr[1].replace('"', '')
                efficiency: str = arr[2].replace('"', '')
                cousumables: str = arr[3].replace('"', '')
                comparison: str = arr[4].replace('"', '')
                time: str = arr[5].replace('"', '')

                if user_id not in external_data:
                    external_data[user_id] = {}

                external_data[user_id][time] = {
                    "efficiency": efficiency,
                    "cousumables": cousumables,
                    "comparison": comparison,
                    "feature": feature
                }



@tool(description="从外部数据源获取指定用户在指定月份的扫地/扫拖机器人完整使用记录，以消息字符串的形式返回，如果获取不到，则返回空字符串")
def fetch_external_data(user_id: str, month: str) -> str:
    generate_external_data()

    try:
        return external_data[user_id][month]
    except KeyError:
        logger.warning(f"未能获取到用户{user_id}在{month}的扫地/扫拖机器人完整使用记录")
        return ""


@tool(description="无入参，无返回值，调用后为报告生成场景动态注入上下文信息，为后续提示词切换提供上下文支撑")
def fill_context_for_report():
    return "fill_context_for_report已调用"
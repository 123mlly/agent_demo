try:
    from .config_handler import prompts_conf
    from .logger_handle import logger
    from .path_tool import get_abs_path
except ImportError:
    from config_handler import prompts_conf
    from logger_handle import logger
    from path_tool import get_abs_path


def load_system_prompts():
    try:
        system_prompt_path = get_abs_path(prompts_conf["main_prompt_path"])

    except Exception as e:
        logger.error(f"加载系统提示词失败: {str(e)}")
        raise e

    try:
        return open(system_prompt_path, "r", encoding="utf-8").read()
    except Exception as e:
        logger.error(f"[system_prompt_path]解析系统提示次出错: {str(e)}")
        raise e


def load_rag_prompts():
    try:
        rag_prompt_path = get_abs_path(prompts_conf["rag_summary_prompt_path"])

    except Exception as e:
        logger.error(f"加载系统提示词失败: {str(e)}")
        raise e

    try:
        return open(rag_prompt_path, "r", encoding="utf-8").read()
    except Exception as e:
        logger.error(f"[rag_prompt_path]解析RAG提示次出错: {str(e)}")
        raise e



def load_report_prompts():
    try:
        report_prompt_path = get_abs_path(prompts_conf["report_prompt_path"])

    except Exception as e:
        logger.error(f"加载系统提示词失败: {str(e)}")
        raise e

    try:
        return open(report_prompt_path, "r", encoding="utf-8").read()
    except Exception as e:
        logger.error(f"[report_prompt_path]解析报告提示次出错: {str(e)}")    
        raise e


if __name__ == "__main__":
    print(load_system_prompts())
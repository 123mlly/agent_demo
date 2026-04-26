import os
import hashlib
try:
    from .logger_handle import logger
except ImportError:
    from logger_handle import logger
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader


def get_file_md5_hex(file_path: str) -> str:

    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return
    
    if not os.path.isfile(file_path):
        logger.error(f"文件不是文件: {file_path}")
        return

    md5_obj = hashlib.md5()
    chunk_size = 4096   # 4kb 分片
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                md5_obj.update(chunk)
        return md5_obj.hexdigest()
    
    except Exception as e:
        logger.error(f"获取文件md5失败: {e}")
        return



def listdir_with_allowed_type(file_path: str, allowed_types: tuple[str]) -> list[str]:      # 返回文件夹内的文件列表
    files = []

    if not os.path.isdir(file_path):
        logger.error(f"文件夹不存在: {file_path}")
        return allowed_types
    
    for file in os.listdir(file_path):
        if file.endswith(allowed_types):
            files.append(os.path.join(file_path, file))

    return tuple(files)


def pdf_loader(file_path: str) -> list[Document]:
    return PyPDFLoader(file_path).load()


def text_loader(file_path: str) -> list[Document]:
    return TextLoader(file_path, encoding="utf-8").load()






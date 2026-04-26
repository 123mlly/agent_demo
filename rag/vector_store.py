import os
import sys

# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chromadb.api.types import Document
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from utils.file_handler import listdir_with_allowed_type, text_loader, pdf_loader, get_file_md5_hex
from utils.path_tool import get_abs_path
from utils.config_handler import chroma_conf
from utils.logger_handle import logger
from model.factory import embeddings


class VectorStoreService(object):
    def __init__(self):
        self.vector_store = Chroma(
            collection_name=chroma_conf["collection_name"],
            embedding_function=embeddings,
            persist_directory=get_abs_path(chroma_conf["persist_directory"]),
        )

        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=chroma_conf["chunk_size"],
            chunk_overlap=chroma_conf["chunk_overlap"],
            separators=chroma_conf["separators"],
        )

    
    def get_retriever(self):
        return self.vector_store.as_retriever(search_kwargs={"k": chroma_conf["k"]})


    def load_document(self):


        def check_md5_hex(md5_for_check: str) -> bool:
            if not os.path.exists(get_abs_path(chroma_conf["md5_hex_store"])):
                open(get_abs_path(chroma_conf["md5_hex_store"]), "w", encoding="utf-8").close()
                return False   #MD5不存在，返回False
            
            with open(get_abs_path(chroma_conf["md5_hex_store"]), "r", encoding="utf-8") as f:
                for line in f.readlines():
                    if line.strip() == md5_for_check:
                        return True    #MD5处理过的，返回True
            return False


        
        def save_md5_hex(md5_for_check: str):
            with open(get_abs_path(chroma_conf["md5_hex_store"]), "a", encoding="utf-8") as f:
                f.write(md5_for_check + "\n")



        def get_file_documents(read_path: str):
            if read_path.endswith("txt"):
                return text_loader(read_path)
            
            if read_path.endswith("pdf"):
                return pdf_loader(read_path)


            return []


        allowed_files_path = listdir_with_allowed_type(
            get_abs_path(chroma_conf["data_path"]), 
            tuple(chroma_conf["allowed_knowledge_types"])
            )

        for file_path in allowed_files_path:
            md5_hex = get_file_md5_hex(file_path)

            if check_md5_hex(md5_hex):
                logger.info(f"MD5已存在，跳过: {file_path}")
                continue

            
            try:
                documents: list[Document] = get_file_documents(file_path)

                if not documents:
                    logger.warning(f"文件读取跳过: {file_path}")
                    continue

                split_documents: list[Document] = self.spliter.split_documents(documents)

                if not split_documents:
                    logger.warning(f"文件分割跳过: {file_path}")
                    continue

                self.vector_store.add_documents(split_documents)

                # 记录 md5
                save_md5_hex(md5_hex)

                logger.info(f"文件处理完成: {file_path}")


            except Exception as e:
                # 记录错误信息
                logger.error(f"文件读取失败: {file_path} - 错误信息: {str(e)}", exc_info=True)
                continue


if __name__ == "__main__":
    vs = VectorStoreService()
    vs.load_document()

    retriever = vs.get_retriever()

    result = retriever.invoke("扫地机器人")

    for doc in result:
        print(doc.page_content) 
        print("-" * 20)


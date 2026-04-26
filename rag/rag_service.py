from chromadb.api.types import Document
from rag.vector_store import VectorStoreService
from utils.prompt_loader import load_rag_prompts
from langchain_core.prompts import PromptTemplate
from model.factory import chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable, RunnableLambda, RunnablePassthrough


def print_prompt(prompt):
    print(prompt.to_string())
    print("-" * 20)
    return prompt


class RagSummarizeService(object):
    def __init__(self):
        self.vector_store = VectorStoreService()
        self.retriever = self.vector_store.get_retriever()
        self.prompt_text = load_rag_prompts()
        self.prompt_template = PromptTemplate.from_template(self.prompt_text) 
        self.model = chat_model
        self.chain = self._init_chain()


    def _init_chain(self):
        chain = self.prompt_template | print_prompt | self.model | StrOutputParser()
        return chain


    def retriever_docs(self, query: str)->list[Document]:
        return self.retriever.invoke(query)

    def summarize(self, query: str)->str:
        
        context_docs = self.retriever_docs(query)
        if not context_docs:
            return "无相关资料"

        counter = 0
        context = ""

        for doc in context_docs:
            counter += 1
            context += f"参考资料{counter}: {doc.page_content} ｜ 文档元数据: {doc.metadata}\n"
        
        return self.chain.invoke(
            {"input": query, "context": context}
        )
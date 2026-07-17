# from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from llms.rag_llm import RagLLM


class LLM:

    def __init__(self, agent_model:str, rag_model:str, openai_api_key:str, google_api_key:str):
        self.agent_model = agent_model
        self.rag_model = rag_model
        self.__openai_api_key = openai_api_key
        self.__google_api_key = google_api_key

    def get_rag_llm(self) -> RagLLM:
        return RagLLM(self.rag_model, self.__openai_api_key, self.__google_api_key)

    def get_agent_model(self):
        # llm = ChatGroq(
        #     model="openai/gpt-oss-120b",
        #     temperature=0,
        #     api_key=self.__groq_api_key
        #     )
        llm = ChatOpenAI(
            model=self.agent_model,
            temperature=0.3,
            max_tokens=4096,
            api_key=self.__openai_api_key
        )
        return llm
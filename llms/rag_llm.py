# from llama_index.llms.groq import Groq
from llama_index.llms.openai import OpenAI
# from llama_index.llms.gemini import Gemini
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
# from langchain_google_genai import GoogleGenerativeAIEmbeddings
# from llama_index.embeddings.huggingface import HuggingFaceEmbedding


class RagLLM:

    def __init__(self, rag_model:str, openai_api_key:str, google_api_key:str):
        self.rag_model = rag_model
        # self.embedding_model = embedding_model
        self.__openai_api_key = openai_api_key
        self.__google_api_key = google_api_key

    def get_chat_model(self):
        # return Gemini(model=self.rag_model, api_key=self.__google_api_key, temperature=0.1)
        # CHAT_MODEL = "openai/gpt-oss-120b"
        # return Groq(model=CHAT_MODEL, api_key=self.__groq_api_key)
        return OpenAI(
            model=self.rag_model,
            temperature=0.1,
            max_tokens=2048,
            api_key=self.__openai_api_key,
            reasoning_effort="medium"
        )
    
    def get_embedding_model(self):
        return GoogleGenAIEmbedding(model="text-embedding-004", api_key=self.__google_api_key)
        # EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
        # return HuggingFaceEmbedding(model_name=EMBEDDING_MODEL)
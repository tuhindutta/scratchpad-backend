import os
from pathlib import Path
from llama_index.core import StorageContext, load_index_from_storage
from langchain_core.language_models.chat_models import BaseChatModel
from rag.pipeline_utils import ingest
from llama_index.core import Settings
from llms.rag_llm import RagLLM
from rag.rag_query_rephraser import rephraser

# rag_llm = RagLLM(os.getenv("GROQ_API_KEY"))

def create_dir(dir) -> None:
    directory = Path(dir)
    directory.mkdir(parents=True, exist_ok=True)


class RAG:

    def __init__(self, rag_llm:RagLLM, ingestion_dir:str, llm:BaseChatModel):
        self.raw_data_location = os.path.join(ingestion_dir, "raw_data")
        self.parsed_data_location = os.path.join(ingestion_dir, "parsed_data")
        self.vectorstore_location = os.path.join(ingestion_dir, "vectorstore")

        for dir in [self.raw_data_location, self.parsed_data_location, self.vectorstore_location]:
            create_dir(dir)

        self.query_engine = None
        self.user_id = None
        self.thread_id = None
        self.rag_llm = rag_llm
        self.llm = llm

    async def ingest(self, user_id:str, thread_id:str):
        async for event in ingest(self.rag_llm, self.raw_data_location, self.parsed_data_location, self.vectorstore_location, user_id, thread_id):
            yield {
                "node": "ingestion",
                "content": event
            }

    def get_query_engine(self, user_id:str, thread_id:str):
        if (user_id != self.user_id) and (thread_id != self.thread_id):
            self.user_id = user_id
            self.thread_id = thread_id
            Settings.llm = self.rag_llm.get_chat_model()
            Settings.embed_model = self.rag_llm.get_embedding_model()
            storage_context = StorageContext.from_defaults(persist_dir=os.path.join(self.vectorstore_location, f"{user_id}_{thread_id}"))
            index = load_index_from_storage(storage_context)
            self.query_engine = index.as_query_engine(llm=self.rag_llm.get_chat_model())

    def retrieve_context(self, query:str, user_id:str, thread_id:str):

        rephrased_query = rephraser(self.llm, query)

        print(rephrased_query)

        prompt = f"""
Answer the following query.

Strict guidelines:

- Do not answer anything which is not present in your knowledge base.
- Give detailed output in structured format (always in markdown) like bullets, tables.

Query:

{rephrased_query}
        """.strip()

        self.get_query_engine(user_id, thread_id)
        response = self.query_engine.query(prompt)
        return str(response)
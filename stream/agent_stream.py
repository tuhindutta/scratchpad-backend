from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.checkpoint.base import BaseCheckpointSaver
from stream.extract_event_text import extract_event_text
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from stream.toolset.tools import toolset
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
import aiosqlite



class AgentStream:

    def __init__(self, scratchpad_dir:str, ingestion_dir:str, llm:BaseChatModel, firecrawl_api_key:str,
                 rag_llm_kwargs:str,
                 system_prompt:str, checkpointer_path:str=None):
        self.scratchpad_dir = scratchpad_dir
        self.ingestion_dir = ingestion_dir
        self.llm = llm
        self.firecrawl_api_key = firecrawl_api_key
        self.rag_llm_kwargs = rag_llm_kwargs
        self.system_prompt = system_prompt
        self.checkpointer_path = checkpointer_path


    def create_assistant(self, checkpointer:BaseCheckpointSaver=None):
        
        tools = toolset(self.scratchpad_dir, self.ingestion_dir, self.llm, self.firecrawl_api_key)

        agent = create_agent(
            model=self.llm,
            tools=tools, system_prompt=self.system_prompt,
            checkpointer=checkpointer
        )

        return agent
    

    async def astream(self, message:str, user_id:str, thread_id:str):
        prev_event = None

        async with AsyncSqliteSaver.from_conn_string(self.checkpointer_path) as memory:

            agent = self.create_assistant(memory)

            scoped_id = f"{user_id}::{thread_id}"
        
            async for event in agent.astream(
                    {
                        "messages": message.strip()
                    },
                    {
                        "configurable": {
                            "thread_id": scoped_id,
                            "rag_llm_kwargs": self.rag_llm_kwargs
                        }
                    }
                ):
            
                if prev_event is not None:

                    yield {
                        "node": "reasoning",
                        **extract_event_text(prev_event)
                    }
            
                prev_event = event

            if prev_event is not None:    
                yield {
                    "node": "response",
                    **extract_event_text(prev_event)
                }


    async def list_all_threads(self) -> list[str]:
        """
        Retrieves a unique list of active thread IDs from the database.
        If target_user_id is provided, it filters the results to that user.
        """
        if not self.checkpointer_path:
            return []

        unique_threads = set()

        async with AsyncSqliteSaver.from_conn_string(self.checkpointer_path) as memory:
            # .alist() yields all historical checkpoint entries matching the provided config
            async for checkpoint_tuple in memory.alist(config=None):
                thread_id = checkpoint_tuple.config["configurable"].get("thread_id")  
                unique_threads.add(thread_id)

        # threads = [i.split('::') for i in list(unique_threads)]      
        return list(unique_threads)
    

    async def delete_thread_history(self, *thread_ids: str):
        """Permanently purges a specific thread conversation from SQLite."""
        if not self.checkpointer_path:
            return

        async with AsyncSqliteSaver.from_conn_string(self.checkpointer_path) as memory:
            # adelete_thread completely scrubs checkpoints, writes, and states for this ID
            for thread_id in thread_ids:
                await memory.adelete_thread(thread_id)
                message = f"Successfully deleted all history for thread: {thread_id}"
        return message
    
    async def delete_full_history(self):
        async with aiosqlite.connect(self.checkpointer_path) as db:
            await db.execute("DELETE FROM checkpoints")
            await db.execute("DELETE FROM writes")
            await db.commit()
            message = "Database purge complete"
        return message


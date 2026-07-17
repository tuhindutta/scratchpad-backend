import json
from collections.abc import AsyncIterable
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from stream.agent_stream import AgentStream
from rag.rag import RAG
from fastapi import HTTPException


def create_app(agent_stream: AgentStream, rag: RAG, ingest_notification_prompt:str) -> FastAPI:
        
    app = FastAPI()

    class Credential(BaseModel):
        user_id: str
        thread_id: str

    class Payload(BaseModel):
        message: str
        credential: Credential



    @app.get("/assistant/chat", response_class=StreamingResponse)
    async def stream_story(payload: Payload) -> AsyncIterable[str]:
        async def generator():
            async for event in agent_stream.astream(
                message=payload.message,
                user_id=payload.credential.user_id,
                thread_id=payload.credential.thread_id,
            ):
                yield json.dumps(event) + "\n"

        return StreamingResponse(
            generator(),
            media_type="application/x-ndjson",
        )

    @app.post("/rag/ingest")
    async def ingest(credential: Credential) -> AsyncIterable[str]:

        user_id = credential.user_id
        thread_id = credential.thread_id

        async def generator():

            async for event in rag.ingest(user_id, thread_id):
                yield json.dumps(event) + "\n"

            async for event in agent_stream.astream(
                message=ingest_notification_prompt,
                user_id=user_id,
                thread_id=thread_id,
            ):
                yield json.dumps(event) + "\n"

        return StreamingResponse(
            generator(),
            media_type="application/x-ndjson",
        )


    @app.get("/assistant/chats/list")
    async def get_user_chat_history():
        try:
            threads = await agent_stream.list_all_threads()
            return {"active_threads": threads}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


    class DeleteThreadRequest(BaseModel):
        thread_id: str


    @app.post("/assistant/chats/delete/thread")
    async def delete_chat_thread(request: DeleteThreadRequest):
        try:
            message = await agent_stream.delete_thread_history(request.thread_id)

            return {
                "status": "success",
                "message": message,
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


    @app.post("/assistant/chats/delete/full")
    async def delete_full_chat_history():
        try:
            message = await agent_stream.delete_full_history()

            return {
                "status": "success",
                "message": message,
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return app
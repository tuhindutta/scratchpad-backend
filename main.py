from stream.agent_stream import AgentStream
from llms.llms import LLM
from rag import RAG, create_dir
import os
import uvicorn
import argparse
from create_app import create_app

from dotenv import load_dotenv
load_dotenv()


parser = argparse.ArgumentParser(description="Start the FastAPI server.")
parser.add_argument(
    "--port", 
    type=int, 
    default=8080, 
    help="Port to run the FastAPI server on (default: 8080)"
)

args = parser.parse_args()



##################### ENV VARS #########################

AGENT_MODEL = os.getenv("AGENT_MODEL", "gpt-4.1-mini")
RAG_MODEL = os.getenv("RAG_MODEL", "gpt-4.1-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
WORK_DIR = os.getenv("WORK_DIR", "work")
SCRATCHPAD_DIR = os.path.join(WORK_DIR, "scratchpad")
INGESTION_DIR = os.path.join(WORK_DIR, "ingestion")
CHECKPOINTER_DIR = os.path.join(WORK_DIR, "checkpointer")

for dir in [SCRATCHPAD_DIR, INGESTION_DIR, CHECKPOINTER_DIR]:
    create_dir(dir)


##################### ENV VARS MISSING #########################

class MissingEnvVariablesError(Exception):
    """Exception raised when the required project folder structure is incomplete."""
    pass

REQUIRED_KEYS = ["OPENAI_API_KEY", "GOOGLE_API_KEY", "FIRECRAWL_API_KEY"]
missing_keys = [key for key in REQUIRED_KEYS if not os.getenv(key)]
if missing_keys:
    missing_str = ", ".join(missing_keys)
    raise MissingEnvVariablesError(
        f"Environment variables in use: AGENT_MODEL, RAG_MODEL, OPENAI_API_KEY, GOOGLE_API_KEY, FIRECRAWL_API_KEY, WORK_DIR. "
        f"Server failed to start! The following required environment variables "
        f"are missing: [{missing_str}]. Please check your configuration or .env file."
    )




##################### WORK DIR LAYOUT ISSUE #########################

# class MissingDirectoryStructureError(Exception):
#     """Exception raised when the required project folder structure is incomplete."""
#     pass


# def validate(work_dir:str):

#     required_paths = [
#         os.path.join(work_dir, "ingestion", "raw_data"),
#         os.path.join(work_dir, "ingestion", "vectorstore"),
#         os.path.join(work_dir, "ingestion", "parsed_data"),
#         os.path.join(work_dir, "scratchpad"),
#         os.path.join(work_dir, "checkpointer"),
#     ]

#     work_structure_valid = all(os.path.exists(path) for path in required_paths)

#     return work_structure_valid

# valid_work_dir_struct = validate(WORK_DIR)
# if not valid_work_dir_struct:
#     required_structure = f"""
# {WORK_DIR}/
# └── ingestion/
#     ├── raw_data/
#     ├── vectorstore/
#     └── parsed_data/
# └── scratchpad/
# └── checkpointer/
# """.strip()
#     raise MissingDirectoryStructureError(
#         f"""
# Required directory layout not found. Expected layout:
# `````````````````````
# {required_structure}
# `````````````````````
# """.strip()
#     )




##################### LLM & RAG APIs #########################

llm_api = LLM(AGENT_MODEL, RAG_MODEL, OPENAI_API_KEY, GOOGLE_API_KEY)
llm = llm_api.get_agent_model()
rag = RAG(llm_api.get_rag_llm(), INGESTION_DIR, llm)




##################### PROMPTS & ARG DEPS #########################

with open("prompts/system_prompt.md", 'r') as f:
    system_prompt = f.read().strip()

with open("prompts/ingest_notification_prompt.md", 'r') as f:
    ingest_notification_prompt = f.read().strip()

rag_llm_kwargs = {
    "rag_model": RAG_MODEL,
    "openai_api_key": OPENAI_API_KEY,
    "google_api_key": GOOGLE_API_KEY
}

checkpointer_path = os.path.join(CHECKPOINTER_DIR, "agent_memory.sqlite")





##################### AGENT #########################

agent_stream = AgentStream(SCRATCHPAD_DIR, INGESTION_DIR, llm, FIRECRAWL_API_KEY,
                           rag_llm_kwargs, system_prompt, checkpointer_path)


app = create_app(agent_stream, rag, ingest_notification_prompt)

if __name__ == "__main__":
    uvicorn.run(app, port=args.port, host="0.0.0.0")



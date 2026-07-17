import os
from docling.document_converter import DocumentConverter
import asyncio
from pathlib import Path
import shutil
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llms.rag_llm import RagLLM



def parse_from_raw_data(raw_data_location: str, file_path:str):
    full_path = os.path.join(raw_data_location, file_path)
    converter = DocumentConverter()
    doc = converter.convert(full_path).document
    return doc.export_to_markdown()

def save_parsed_data(parsed_data_location:str, file_path:str, text:str):
    with open(os.path.join(parsed_data_location, file_path), "w") as f:
        f.write(text)



async def empty_folder(folder_path):
    path = Path(folder_path)
    
    # Ensure the directory actually exists first
    if not path.exists():
        print(f"The directory {folder_path} does not exist.")
        return

    for item in path.iterdir():
        try:
            if item.is_file() or item.is_symlink():
                item.unlink()  # Delete files or links
            elif item.is_dir():
                shutil.rmtree(item)  # Delete subfolders and contents
        except Exception as e:
            print(f"Failed to delete {item}. Reason: {e}")



def create_vector_store(rag_llm:RagLLM, data_location_directory:str, vectorstore_location:str, user_id:str, thread_id:str):
    Settings.llm = rag_llm.get_chat_model()
    Settings.embed_model = rag_llm.get_embedding_model()
    documents = SimpleDirectoryReader(data_location_directory).load_data()
    index = VectorStoreIndex.from_documents(documents)
    index.storage_context.persist(persist_dir=os.path.join(vectorstore_location, f"{user_id}_{thread_id}"))


async def parsing_pipeline(raw_data_location:str, parsed_data_location:str, file_path: str):
    file_name = file_path.split('.')[0]
    parsed = parse_from_raw_data(raw_data_location, file_path)
    save_parsed_data(parsed_data_location, f"{file_name}.md", parsed)


async def ingest(rag_llm:RagLLM, raw_data_location:str, parsed_data_location:str, vectorstore_location:str, user_id:str, thread_id:str):
    yield "Parsing data..."
    await asyncio.gather(*[parsing_pipeline(raw_data_location, parsed_data_location, file) for file in os.listdir(raw_data_location)])
    yield "Data parsed."
    yield "Creating vector store..."
    create_vector_store(rag_llm, parsed_data_location, vectorstore_location, user_id, thread_id)
    yield "Vector store created."
    # await asyncio.gather(empty_folder(raw_data_location), empty_folder(parsed_data_location))
    # yield "Raw and Parsed data location emptied."
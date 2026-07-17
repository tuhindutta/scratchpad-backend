import os
import shutil
import stat
from langchain_core.tools import tool
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import RunnableConfig
from langchain_community.tools import DuckDuckGoSearchRun
import os
from urllib.parse import urlparse
from dotenv import load_dotenv
load_dotenv()
from llms.rag_llm import RagLLM
from rag.rag import RAG
from stream.toolset.website_scraper import WebsiteScraper



def toolset(scratchpad_dir:str, ingestion_dir:str, llm:BaseChatModel, firecrawl_api_key:str):

    parent = scratchpad_dir

    search = DuckDuckGoSearchRun()
    scraper = WebsiteScraper(firecrawl_api_key)

    # Define the exact names of directories and files to completely skip
    IGNORE_DIRS = {".git", "node_modules", "venv", "__pycache__", ".ipynb_checkpoints", ".venv"}
    IGNORE_FILES = {".DS_Store", "thumbs.db", ".env"}

    @tool
    def print_tree():
        """
        Returns the complete repository structure.

        Use only when:

        * Repository structure is unknown
        * `index.md` is missing
        * Repository consistency must be verified
        """
        directory = f"./{parent}"
        output = []
        
        # Standardize the root path to ensure string replacement behaves consistently
        directory = os.path.normpath(directory)
        
        for root, dirs, files in os.walk(directory):
            # 1. Modify dirs IN-PLACE to skip ignored folders entirely
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            # Skip processing the root parent directory line itself
            if root == directory:
                # We process files inside the root directory right here, with 0 indentation
                for file in files:
                    if file in IGNORE_FILES:
                        continue
                    output.append(f"[File] {file}")
                continue
                
            # 2. Calculate level relative to the inner items (subtract 1 so inner start at 0)
            level = root.replace(directory, '').count(os.sep) - 1
            indent = ' ' * 4 * level
            output.append(f"{indent}[Directory] {os.path.basename(root)}/")
            
            # 3. Filter and append sub-files
            sub_indent = ' ' * 4 * (level + 1)
            for file in files:
                if file in IGNORE_FILES:
                    continue  # Skip ignored files
                output.append(f"{sub_indent}[File] {file}")

        return "\n".join(output)

    @tool
    def write_index_file(text: str):
        """
        Regenerate and overwrite `index.md`.

        `index.md` is a managed artifact.

        Only `write_index_file` may modify `index.md`.

        Never update `index.md` using:

        * read_file
        * append_text_in_existing_file
        * write_text_in_new_file

        Use `write_index_file` when:

        * `index.md` is missing
        * Files are created
        * Files are removed
        * Files are renamed
        * A file's title, purpose, description, or keywords change
        """
        try:
            full_path = f"./{parent}/index.md"
            
            # Extract directory path and create it safely
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, "w", encoding="utf-8") as file:
                file.write(text)

            status = "Succesfully written INDEX file."
        except Exception as e:
            status = f"Failed to write INDEX file: {str(e)}"
        return status

        # write_text_in_new_file("index", text)

    @tool
    def write_text_in_new_file(file_path: str, text: str):
        """
        Create a new markdown file.

        Use only when:

        * The target file does not exist
        * No suitable existing file can be updated

        Never use this tool to modify existing files.
        """
        try:
            full_path = f"./{parent}/{file_path}"
            
            # Extract directory path and create it safely
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(text)
        
            status = f"Succesfully written {file_path} file."
        except Exception as e:
            status = f"Failed to write {file_path} file: {str(e)}"
        return status
        

    @tool
    def append_text_in_existing_file(file_path: str, text: str):
        """
        Append information to an existing markdown file.

        Use when information extends an existing document.
        """
        try:
            full_path = f"./{parent}/{file_path}"
            
            # Extract directory path and create it safely
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, "a", encoding="utf-8") as file:
                file.write(f"\n\n{text}")
            status = f"Succesfully written {file_path} file."
        except Exception as e:
            status = f"Failed to append {file_path} file: {str(e)}"
        return status
        

    @tool
    def read_file(file_path:str):
        """To read a file."""
        try:
            with open(f"./{parent}/{file_path}", 'r') as f:
                text = f.read()
        except Exception as e:
            text = f"Could not read the file (ERROR): **{str(e)}**"
        return text

    @tool
    def read_index():
        """
        Reads `index.md` file directly.

        Use before repository exploration whenever possible.
        """
        try:
            with open(f"./{parent}/index.md", 'r') as f:
                text = f.read()
        except Exception as e:
            text = f"Could not INDEX file (ERROR): **{str(e)}**"
        return text


    @tool
    def delete_file(file_path: str):
        """
        Delete a single file.

        Use only when:

        * The file is obsolete
        * The file is duplicated by another file
        * The user explicitly requests deletion

        After successful deletion:

        1. Verify the file no longer exists
        2. Regenerate `index.md` using `write_index_file`
        """
        file_path = os.path.join(parent, file_path)
        try:
            os.remove(file_path)
            return True
        except FileNotFoundError:
            return f"{file_path} succesfully deleted"
        except PermissionError:
            return f"Permission denied: Cannot delete {file_path}"
            return False
        except Exception as e:
            return f"Failed to delete {file_path}: {str(e)}"

    @tool
    def force_delete_folder(folder_path: str) -> bool:
        """
        Delete a directory and all contents recursively.

        Use only when:

        * The entire folder is obsolete
        * The user explicitly requests removal
        * Repository restructuring requires removal

        Before deletion:

        1. Confirm the folder is no longer needed
        2. Ensure important information is not lost

        After successful deletion:

        1. Verify the folder no longer exists
        2. Regenerate `index.md` using `write_index_file`

        
        ## Deletion Safety Rules

        Never delete a file or folder if:

        * It contains unique information not stored elsewhere
        * The repository has not been inspected
        * The deletion target is uncertain

        Before deleting:

        1. Read `index.md`
        2. Identify the target
        3. Verify the target is correct
        4. Perform deletion
        5. Update `index.md`

        Deletion must never leave stale entries in `index.md`.
        """
        def _clear_readonly(func, path, excinfo):
            """Callback to clear read-only flag and retry deletion."""
            try:
                os.chmod(path, stat.S_IWRITE)
                func(path)
            except Exception:
                pass

        folder_path = os.path.join(parent, folder_path)
        try:
            # 'onexc' handles read-only or permission blocks during recursion
            shutil.rmtree(folder_path, onexc=_clear_readonly)
            return f"{folder_path} succesfully deleted"
        except FileNotFoundError:
            return f"{folder_path} already not present"
        except Exception as e:
            return f"Failed to force delete folder {folder_path}: {str(e)}"
        

    @tool
    def query_RAG_agent(query:str, config: RunnableConfig):
        """
        This provides access to knowledge that is not stored in
        your markdown repository.

        With this tool, you can query an external smart (RAG) agent that is in charge of
        ingested data in vector store, for smart retrieval.

        Do not assume external knowledge is permanently available in
        your markdown repository unless you explicitly store it.

        Use when:
        • answering questions about ingested documents
        • searching the vector store/DB
        • exploring newly ingested information
        • comparing repository knowledge with external knowledge

        You may choose to summarize or persist useful information into
        your markdown repository if it is likely to be valuable in the future
        and ignore information that is not worth remembering.
        """
        configurable = config.get("configurable", {})
        # user_id = configurable.get("user_id")
        scoped_id = configurable.get("thread_id")
        user_id, thread_id = scoped_id.split("::")

        rag_llm_kwargs = configurable.get("rag_llm_kwargs", {})
        
        if user_id and thread_id:
            rag_llm = RagLLM(**rag_llm_kwargs)
            rag = RAG(rag_llm, ingestion_dir, llm)
            response = rag.retrieve_context(query, user_id, thread_id)
        else:
            response = f"""
Passed user_id/thread_id not found:

user_id = {user_id}

thread_id = {thread_id}
    """.strip()
            
        return response
    
    @tool
    def query_search_engine(query:str):
        """
        Search the public web and return accurate, up-to-date information.
        Prefer authoritative sources, summarize concisely, and include source URLs.
        Never fabricate information.
        """
        response = search.invoke(query)
        return response
    
    @tool()
    def scrape_website(url:str) -> str:
        """
        Scrape the provided URL and return its main content in Markdown.
        Use this tool only when the content of a specific URL is needed.
        """
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return "Invalid URL"
            return scraper.data(url)
        except Exception as e:
            return f"Error fetching website data: {str(e)}"
    

    @tool
    def summarize(query:str, text_to_summarize:str):
        """
        Summarize large content while preserving query-relevant information.

        Use when:

        * Files are large
        * Multiple files must be processed
        * Context reduction is beneficial
        """
        res = llm.invoke(f"Summarize the following text corresponding to the query asked: '{query}'", text_to_summarize)
        return res
    
    tools = [print_tree, read_index, write_index_file, read_file, append_text_in_existing_file,
             write_text_in_new_file, summarize, delete_file, force_delete_folder, query_RAG_agent,
             query_search_engine, scrape_website]
    return tools
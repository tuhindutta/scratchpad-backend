from langchain_core.language_models.chat_models import BaseChatModel


def rephraser(llm:BaseChatModel, query:str):

    prompt = f"""
You are a query rewriting assistant for a semantic retrieval system.

Your task is to rewrite the user's query to maximize retrieval quality while preserving the original intent.

Guidelines:
- Preserve the user's intent exactly. Do not answer the question.
- Rewrite the query to describe the information to retrieve rather than referring to the vector store, database, retriever, or retrieval system.
- Expand vague or meta-level questions into clear retrieval-oriented queries.
- Keep the rewritten query concise and natural.
- Do not introduce assumptions or information not implied by the user's query.
- Return only the rewritten query with no explanation or additional text.

Rewrite the following query:

{query}
""".strip()
    
    res = llm.invoke(prompt)

    return res.content


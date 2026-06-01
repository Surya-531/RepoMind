from langchain_openai import ChatOpenAI

from config import BASE_URL, MODEL_NAME, OPENROUTER_API_KEY


def answer_question(vectorstore, question: str) -> str:
    docs = vectorstore.similarity_search(question, k=6)

    context_blocks = []
    for doc in docs:
        source = doc.metadata.get("source", "repository")
        context_blocks.append(f"Source: {source}\n{doc.page_content}")

    context = "\n\n---\n\n".join(context_blocks)

    llm = ChatOpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=BASE_URL,
        model=MODEL_NAME,
        temperature=0.2,
        default_headers={
            "HTTP-Referer": "http://localhost",
            "X-Title": "RepoMind",
        },
    )

    prompt = f"""
You are RepoMind, a repository Q&A assistant.

Answer ONLY from the repository information below. If the answer is not present
in the repository context, say that the repository context does not contain
enough information to answer confidently.

When useful, mention specific files or sources from the context.

Repository Context:

{context}

Question:

{question}
"""

    response = llm.invoke(prompt)
    return response.content

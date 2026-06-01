def _chunk_text(text: str, chunk_size: int = 1400, overlap: int = 180) -> list[str]:
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)

    return chunks


def _add_chunked_document(
    docs: list,
    content: str,
    source: str,
    doc_type: str,
) -> None:
    from langchain_core.documents import Document

    for index, chunk in enumerate(_chunk_text(content)):
        docs.append(
            Document(
                page_content=chunk,
                metadata={
                    "source": source,
                    "type": doc_type,
                    "chunk": index,
                },
            )
        )


def build_vector_store(repo_data: dict, analysis_report: str | None = None):
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS

    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    docs: list = []

    _add_chunked_document(
        docs,
        repo_data.get("readme", ""),
        "README",
        "readme",
    )

    files = repo_data.get("files", [])
    if files:
        _add_chunked_document(
            docs,
            "\n".join(files),
            "FILE_TREE",
            "file_tree",
        )

    for file_data in repo_data.get("file_contents", []):
        path = file_data.get("path", "UNKNOWN_FILE")
        content = file_data.get("content", "")
        _add_chunked_document(docs, content, path, "file")

    commits = repo_data.get("commits", [])
    if commits:
        _add_chunked_document(
            docs,
            "\n".join(commits),
            "RECENT_COMMITS",
            "commits",
        )

    meta = repo_data.get("meta", {})
    if meta:
        _add_chunked_document(
            docs,
            "\n".join(f"{key}: {value}" for key, value in meta.items()),
            "REPOSITORY_METADATA",
            "metadata",
        )

    if analysis_report:
        _add_chunked_document(
            docs,
            analysis_report,
            "REPOMIND_ANALYSIS_REPORT",
            "analysis_report",
        )

    if not docs:
        raise ValueError("No repository content available to build a knowledge base.")

    return FAISS.from_documents(docs, embedding_model)

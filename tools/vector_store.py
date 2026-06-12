import math
import re
from collections import Counter
from dataclasses import dataclass


TOKEN_RE = re.compile(r"[A-Za-z0-9_./-]+")


@dataclass
class SearchDocument:
    page_content: str
    metadata: dict


class KeywordVectorStore:
    """Small in-memory retriever that avoids heavyweight model downloads on Render."""

    def __init__(self, docs: list[SearchDocument]):
        self.docs = docs
        self.doc_tokens = [_token_counts(doc.page_content) for doc in docs]
        self.idf = self._calculate_idf()

    def _calculate_idf(self) -> dict[str, float]:
        doc_count = len(self.doc_tokens)
        document_frequency = Counter()

        for tokens in self.doc_tokens:
            document_frequency.update(tokens.keys())

        return {
            token: math.log((1 + doc_count) / (1 + frequency)) + 1
            for token, frequency in document_frequency.items()
        }

    def similarity_search(self, query: str, k: int = 6) -> list[SearchDocument]:
        query_tokens = _token_counts(query)
        if not query_tokens:
            return self.docs[:k]

        scored_docs = []
        for index, doc_tokens in enumerate(self.doc_tokens):
            score = _cosine_similarity(query_tokens, doc_tokens, self.idf)
            if score > 0:
                scored_docs.append((score, index))

        scored_docs.sort(reverse=True)
        return [self.docs[index] for _, index in scored_docs[:k]] or self.docs[:k]


def _token_counts(text: str) -> Counter:
    tokens = [token.lower() for token in TOKEN_RE.findall(text or "")]
    return Counter(tokens)


def _cosine_similarity(
    query_tokens: Counter,
    doc_tokens: Counter,
    idf: dict[str, float],
) -> float:
    shared_tokens = set(query_tokens) & set(doc_tokens)
    if not shared_tokens:
        return 0.0

    numerator = sum(
        query_tokens[token] * doc_tokens[token] * idf.get(token, 1.0) ** 2
        for token in shared_tokens
    )
    query_norm = math.sqrt(
        sum((count * idf.get(token, 1.0)) ** 2 for token, count in query_tokens.items())
    )
    doc_norm = math.sqrt(
        sum((count * idf.get(token, 1.0)) ** 2 for token, count in doc_tokens.items())
    )

    if not query_norm or not doc_norm:
        return 0.0

    return numerator / (query_norm * doc_norm)


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
    docs: list[SearchDocument],
    content: str,
    source: str,
    doc_type: str,
) -> None:
    for index, chunk in enumerate(_chunk_text(content)):
        docs.append(
            SearchDocument(
                page_content=chunk,
                metadata={
                    "source": source,
                    "type": doc_type,
                    "chunk": index,
                },
            )
        )


def build_vector_store(repo_data: dict, analysis_report: str | None = None):
    docs: list[SearchDocument] = []

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

    return KeywordVectorStore(docs)

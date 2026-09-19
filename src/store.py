from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401

            # TODO: initialize chromadb client + collection
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        embedding = self._embedding_fn(doc.content)
        return {
            "id": doc.id,
            "content": doc.content,
            "metadata": doc.metadata or {},
            "embedding": embedding,
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if not records:
            return []
        query_emb = self._embedding_fn(query)
        scored = []
        for r in records:
            from .chunking import compute_similarity
            score = compute_similarity(query_emb, r["embedding"])
            scored.append({
                "id": r["id"],
                "content": r["content"],
                "metadata": r["metadata"],
                "score": score,
            })
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.
        """
        if not docs:
            return
        if self._use_chroma and self._collection is not None:
            try:
                ids = [d.id for d in docs]
                contents = [d.content for d in docs]
                embeddings = [self._embedding_fn(d.content) for d in docs]
                metadatas = [d.metadata or {} for d in docs]
                self._collection.add(
                    ids=ids,
                    documents=contents,
                    embeddings=embeddings,
                    metadatas=metadatas,
                )
            except Exception:
                pass

        for d in docs:
            self._store.append(self._make_record(d))

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.
        """
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.
        """
        if not metadata_filter:
            return self.search(query, top_k=top_k)

        filtered_records = []
        for r in self._store:
            matches = True
            rec_meta = r.get("metadata", {})
            for key, val in metadata_filter.items():
                if rec_meta.get(key) != val:
                    matches = False
                    break
            if matches:
                filtered_records.append(r)

        return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.
        """
        initial_count = len(self._store)
        self._store = [
            r for r in self._store 
            if r["id"] != doc_id and r.get("metadata", {}).get("doc_id") != doc_id
        ]
        removed = len(self._store) < initial_count

        if self._use_chroma and self._collection is not None:
            try:
                self._collection.delete(ids=[doc_id])
                removed = True
            except Exception:
                pass

        return removed

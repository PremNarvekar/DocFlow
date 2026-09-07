from __future__ import annotations

from pathlib import Path
from typing import Any

import chromadb


DEFAULT_COLLECTION = "documents"
DEFAULT_DB_PATH = Path("./chroma_db")


class DocumentStore:
    """Persistent ChromaDB storage for processed DocFlow documents."""

    def __init__(
        self,
        db_path: str | Path = DEFAULT_DB_PATH,
        collection_name: str = DEFAULT_COLLECTION,
    ) -> None:
        self.db_path = Path(db_path)

        self.client = chromadb.PersistentClient(
            path=str(self.db_path)
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name
        )

    def add_document(
        self,
        document_id: str,
        text: str,
        metadata: dict[str, Any],
    ) -> None:
        if not document_id.strip():
            raise ValueError("document_id cannot be empty")

        if not text.strip():
            raise ValueError("text cannot be empty")

        self.collection.upsert(
            ids=[document_id],
            documents=[text],
            metadatas=[metadata],
        )

    def get_document(
        self,
        document_id: str,
    ) -> dict[str, Any]:
        result = self.collection.get(
            ids=[document_id]
        )

        if not result["ids"]:
            raise KeyError(
                f"Document not found: {document_id}"
            )

        return {
            "id": result["ids"][0],
            "text": result["documents"][0],
            "metadata": result["metadatas"][0],
        }

    def search(
        self,
        query: str,
        limit: int = 5,
    ) -> dict[str, Any]:
        if not query.strip():
            raise ValueError("query cannot be empty")

        if limit < 1:
            raise ValueError("limit must be at least 1")

        return self.collection.query(
            query_texts=[query],
            n_results=limit,
        )

    def delete_document(
        self,
        document_id: str,
    ) -> None:
        self.collection.delete(
            ids=[document_id]
        )

    def count(self) -> int:
        return self.collection.count()
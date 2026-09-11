"""
Document pipeline storage.

Handles semantic chunking and vector storage into ChromaDB.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import chromadb

DEFAULT_COLLECTION = "documents"
DEFAULT_DB_PATH = Path("./chroma_db")


def semantic_chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Splits text into overlapping chunks for semantic RAG retrieval."""
    if not text:
        return []
        
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size

        if end < text_length:
            # Find a natural breaking point: double newline, single newline, or space
            break_point = text.rfind('\n\n', start, end)
            if break_point == -1 or break_point <= start + (chunk_size // 2):
                break_point = text.rfind('\n', start, end)
            if break_point == -1 or break_point <= start + (chunk_size // 2):
                break_point = text.rfind(' ', start, end)

            if break_point != -1 and break_point > start:
                end = break_point + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move start forward, ensuring we always progress
        next_start = end - overlap
        start = max(next_start, start + 1)

    return chunks


class DocumentStore:
    """Persistent ChromaDB storage for processed DocFlow documents.
    
    Automatically chunks large documents to ensure semantic RAG retrieval
    quality without blowing up context windows.
    """

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

        # Delete existing chunks if this is an update
        self.delete_document(document_id)

        # Chunk the document
        chunks = semantic_chunk_text(text, chunk_size=1000, overlap=200)

        if not chunks:
            return

        ids = []
        documents = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_chunk_{i}"
            chunk_metadata = metadata.copy()
            chunk_metadata["document_id"] = document_id
            chunk_metadata["chunk_index"] = i
            chunk_metadata["total_chunks"] = len(chunks)

            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append(chunk_metadata)

        # Batch insert into ChromaDB
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

    def get_document(
        self,
        document_id: str,
    ) -> dict[str, Any]:
        """Reconstructs the full document from its chunks."""
        # Query by document_id metadata
        result = self.collection.get(
            where={"document_id": document_id}
        )

        if not result or not result["ids"]:
            raise KeyError(
                f"Document not found: {document_id}"
            )

        # Reconstruct chunks in order
        chunks = []
        for i, doc_id in enumerate(result["ids"]):
            chunks.append({
                "text": result["documents"][i],
                "index": result["metadatas"][i]["chunk_index"],
                "metadata": result["metadatas"][i]
            })
            
        chunks.sort(key=lambda x: x["index"])
        
        # Combine text
        combined_text = "\n\n".join(c["text"] for c in chunks)
        
        # Base metadata (exclude chunk-specific fields)
        base_metadata = chunks[0]["metadata"].copy()
        base_metadata.pop("chunk_index", None)
        base_metadata.pop("total_chunks", None)
        base_metadata.pop("document_id", None)

        return {
            "id": document_id,
            "text": combined_text,
            "metadata": base_metadata,
        }

    def search(
        self,
        query: str,
        limit: int = 5,
        document_id: str | None = None,
    ) -> dict[str, Any]:
        """Semantic search returning the most relevant documents based on their chunks."""
        if not query.strip():
            raise ValueError("query cannot be empty")

        if limit < 1:
            raise ValueError("limit must be at least 1")

        query_params = {
            "query_texts": [query],
            "n_results": limit,
        }
        
        if document_id:
            query_params["where"] = {"document_id": document_id}

        raw_results = self.collection.query(**query_params)

        # Re-map chunk IDs and metadatas back to parent document view
        # so consumers just get matching document references.
        remapped_ids = []
        remapped_metadatas = []
        
        for ids, metadatas in zip(raw_results.get("ids", []), raw_results.get("metadatas", [])):
            batch_ids = []
            batch_metadatas = []
            seen_docs = set()
            for chunk_id, meta in zip(ids, metadatas):
                doc_id = meta.get("document_id")
                if doc_id and doc_id not in seen_docs:
                    seen_docs.add(doc_id)
                    batch_ids.append(doc_id)
                    
                    # Clean metadata
                    clean_meta = meta.copy()
                    clean_meta.pop("chunk_index", None)
                    clean_meta.pop("total_chunks", None)
                    clean_meta.pop("document_id", None)
                    batch_metadatas.append(clean_meta)
            
            remapped_ids.append(batch_ids)
            remapped_metadatas.append(batch_metadatas)

        raw_results["ids"] = remapped_ids
        raw_results["metadatas"] = remapped_metadatas
        
        return raw_results

    def delete_document(
        self,
        document_id: str,
    ) -> None:
        """Deletes all chunks associated with a document_id."""
        self.collection.delete(
            where={"document_id": document_id}
        )

    def count(self) -> int:
        """Returns the number of chunks, not documents."""
        return self.collection.count()
from pathlib import Path

from pipeline.store import DocumentStore


def test_store_add_and_get(tmp_path: Path):
    store = DocumentStore(
        db_path=tmp_path / "chroma"
    )

    store.add_document(
        document_id="doc-001",
        text="Invoice INV-001 total INR 1000",
        metadata={
            "document_type": "invoice",
            "file_name": "invoice.pdf",
        },
    )

    result = store.get_document("doc-001")

    assert result["id"] == "doc-001"
    assert result["text"] == "Invoice INV-001 total INR 1000"
    assert result["metadata"]["document_type"] == "invoice"


def test_store_upsert_updates_document(tmp_path: Path):
    store = DocumentStore(
        db_path=tmp_path / "chroma"
    )

    store.add_document(
        document_id="doc-001",
        text="Original document",
        metadata={"version": "1"},
    )

    store.add_document(
        document_id="doc-001",
        text="Updated document",
        metadata={"version": "2"},
    )

    result = store.get_document("doc-001")

    assert result["text"] == "Updated document"
    assert result["metadata"]["version"] == "2"
    assert store.count() == 1


def test_store_search(tmp_path: Path):
    store = DocumentStore(
        db_path=tmp_path / "chroma"
    )

    store.add_document(
        document_id="invoice-001",
        text="Invoice for software development INR 75000",
        metadata={"document_type": "invoice"},
    )

    store.add_document(
        document_id="contract-001",
        text="Employment contract between company and employee",
        metadata={"document_type": "contract"},
    )

    result = store.search(
        query="software invoice",
        limit=1,
    )

    assert len(result["ids"][0]) == 1
    assert result["ids"][0][0] == "invoice-001"


def test_store_rejects_empty_document(tmp_path: Path):
    store = DocumentStore(
        db_path=tmp_path / "chroma"
    )

    try:
        store.add_document(
            document_id="doc-001",
            text="",
            metadata={},
        )
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_store_delete(tmp_path: Path):
    store = DocumentStore(
        db_path=tmp_path / "chroma"
    )

    store.add_document(
        document_id="doc-001",
        text="Test document",
        metadata={"document_type": "invoice"},
    )

    assert store.count() == 1

    store.delete_document("doc-001")

    assert store.count() == 0
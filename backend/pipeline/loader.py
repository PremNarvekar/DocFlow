from pathlib import Path

import fitz
from pydantic import BaseModel, Field


class PageContent(BaseModel):
    page_num: int = Field(..., ge=1)
    text: str


class LoadedDocument(BaseModel):
    file_name: str
    file_path: str
    page_count: int = Field(..., ge=1)
    pages: list[PageContent]


def load_and_extract(file_path: str) -> LoadedDocument:
    if "../" in file_path or "..\\" in file_path:
        raise ValueError("Path traversal attempt detected")
        
    path = Path(file_path).resolve()

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported")

    try:
        with fitz.open(path) as document:
            if document.page_count == 0:
                raise ValueError("PDF contains no pages")
    
            pages = []
    
            for page_index in range(document.page_count):
                page = document.load_page(page_index)
                text = page.get_text("text").strip()
    
                pages.append(
                    PageContent(
                        page_num=page_index + 1,
                        text=text,
                    )
                )
    
            return LoadedDocument(
                file_name=path.name,
                file_path=str(path),
                page_count=document.page_count,
                pages=pages,
            )
    except Exception as e:
        raise ValueError(f"Failed to process PDF: {str(e)}") from e
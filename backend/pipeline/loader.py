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
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported")

    document = None

    try:
        document = fitz.open(path)

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

    finally:
        if document is not None:
            document.close()
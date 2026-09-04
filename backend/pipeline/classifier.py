from enum import Enum

from google import genai
from google.genai import types
from pydantic import BaseModel

from config import GEMINI_API_KEY


class DocumentType(str, Enum):
    INVOICE = "invoice"
    CONTRACT = "contract"
    MEDICAL_REPORT = "medical_report"
    FINANCIAL_STATEMENT = "financial_statement"
    UNKNOWN = "unknown"


class DocumentClassification(BaseModel):
    document_type: DocumentType


client = genai.Client(
    api_key=GEMINI_API_KEY
)


def classify_document(text: str) -> DocumentClassification:

    if not text or not text.strip():
        return DocumentClassification(
            document_type=DocumentType.UNKNOWN
        )

    preview = text[:500]

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=preview,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=DocumentClassification,
            system_instruction=(
                "You are a document classification system. "
                "Classify the document into exactly one of these "
                "categories: invoice, contract, medical_report, "
                "financial_statement, or unknown. "
                "Return unknown if the document does not clearly "
                "belong to one of the supported categories."
            ),
        ),
    )

    return DocumentClassification.model_validate_json(
        response.text
    )
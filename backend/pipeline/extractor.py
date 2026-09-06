"""
Structured data extractor — pulls typed fields from documents.

CHANGED from original:
- Original: hardcoded google.genai client, redundant load_dotenv()
- Now: uses AI Router — provider is selected automatically
- PRESERVED: MODEL_MAP, extract_document() signature, error handling

The extractor receives the document text + classified type,
looks up the correct Pydantic schema, and asks the AI to
extract structured data matching that schema.
"""

from pydantic import BaseModel

from ai import get_router, AITask
from pipeline.classifier import DocumentType
from models.invoice import InvoiceData
from models.contract import ContractData
from models.medical import MedicalReportData
from models.financial import FinancialStatementData


MODEL_MAP: dict[DocumentType, type[BaseModel]] = {
    DocumentType.INVOICE: InvoiceData,
    DocumentType.CONTRACT: ContractData,
    DocumentType.MEDICAL_REPORT: MedicalReportData,
    DocumentType.FINANCIAL_STATEMENT: FinancialStatementData,
}


EXTRACTION_SYSTEM_PROMPT = (
    "Extract information from this document "
    "according to the provided schema.\n\n"
    "Rules:\n"
    "1. Never invent information.\n"
    "2. Only extract information present in the document.\n"
    "3. Leave optional fields empty when information is missing.\n"
    "4. Preserve the meaning and values from the document."
)


def extract_document(
    text: str,
    document_type: DocumentType,
) -> BaseModel:
    if not text or not text.strip():
        raise ValueError(
            "Cannot extract fields from empty document text"
        )

    schema = MODEL_MAP.get(document_type)

    if schema is None:
        raise ValueError(
            f"Unsupported document type: {document_type}"
        )

    router = get_router()

    prompt = (
        f"Document type: {document_type.value}\n\n"
        f"Document:\n{text}"
    )

    response = router.parse(
        prompt=prompt,
        schema=schema,
        system_instruction=EXTRACTION_SYSTEM_PROMPT,
        task=AITask.STRUCTURED_EXTRACTION,
    )

    return schema.model_validate_json(response.text)
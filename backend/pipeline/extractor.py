from dotenv import load_dotenv

load_dotenv()

from google import genai
from google.genai import types

from pipeline.classifier import DocumentType
from models.invoice import InvoiceData
from models.contract import ContractData
from models.medical import MedicalReportData
from models.financial import FinancialStatementData


client = genai.Client()



MODEL_MAP = {
    DocumentType.INVOICE: InvoiceData,
    DocumentType.CONTRACT: ContractData,
    DocumentType.MEDICAL_REPORT: MedicalReportData,
    DocumentType.FINANCIAL_STATEMENT: FinancialStatementData,
}


def extract_document(
    text: str,
    document_type: DocumentType,
):
    if not text or not text.strip():
        raise ValueError(
            "Cannot extract fields from empty document text"
        )

    schema = MODEL_MAP.get(document_type)

    if schema is None:
        raise ValueError(
            f"Unsupported document type: {document_type}"
        )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(
                        text=(
                            "Extract information from this document "
                            "according to the provided schema.\n\n"
                            "Rules:\n"
                            "1. Never invent information.\n"
                            "2. Only extract information present in the document.\n"
                            "3. Leave optional fields empty when information is missing.\n"
                            "4. Preserve the meaning and values from the document.\n\n"
                            f"Document type: {document_type.value}\n\n"
                            f"Document:\n{text}"
                        )
                    )
                ],
            )
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
        ),
    )

return schema.model_validate_json(response.text)
from pipeline.classifier import DocumentType
from pipeline.extractor import extract_document


invoice_text = """
ABC Technologies Pvt Ltd
INVOICE

Invoice Number: INV-2026-001
Invoice Date: 2026-09-04
Due Date: 2026-09-30

Vendor: ABC Technologies Pvt Ltd
Customer: XYZ Solutions Pvt Ltd

Item: Laptop
Quantity: 2
Unit Price: 50000
Amount: 100000

Subtotal: 100000
Tax: 18000
Discount: 5000
Total: 113000

Currency: INR
Payment Terms: Net 30
"""


result = extract_document(
    text=invoice_text,
    document_type=DocumentType.INVOICE,
)

print(result)
print()
print("Invoice Number:", result.invoice_number)
print("Vendor:", result.vendor_name)
print("Customer:", result.customer_name)
print("Total:", result.total)
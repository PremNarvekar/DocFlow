"""
PHASE 5 — CLASSIFIER TESTING
PHASE 6 — GROK/GEMINI API TESTING 
PHASE 7+8 — EXTRACTION TESTING

Tests classifier, API integration, and extractor with real and mock scenarios.
"""
import sys
import os
import time
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import date

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PASS = 0
FAIL = 0
RESULTS = []


def record(test_name, expected, actual, passed, critique=""):
    global PASS, FAIL
    status = "PASS" if passed else "FAIL"
    if passed:
        PASS += 1
    else:
        FAIL += 1
    RESULTS.append({
        "test": test_name,
        "expected": expected,
        "actual": str(actual)[:200],
        "status": status,
        "critique": critique,
    })
    icon = "✓" if passed else "✗"
    print(f"  {icon} {test_name}: {status}")
    if not passed:
        print(f"    Expected: {expected}")
        print(f"    Actual: {str(actual)[:200]}")
    if critique:
        print(f"    CRITIQUE: {critique}")


# ============================================================
# PHASE 5: CLASSIFIER TESTS
# ============================================================
print("=" * 60)
print("PHASE 5: CLASSIFIER TESTS")
print("=" * 60)

# First, verify classifier imports
print("\n--- Import Test ---")
try:
    from pipeline.classifier import classify_document, DocumentType, DocumentClassification
    record("Classifier: Import", "Import succeeds", "Imported", True)
except Exception as e:
    record("Classifier: Import", "Import succeeds", f"{type(e).__name__}: {e}", False,
           critique="CRITICAL: Cannot import classifier. All classifier tests will fail.")
    print("\nCANNOT PROCEED — classifier import failed")
    sys.exit(1)


# Test 1: Empty text returns UNKNOWN
print("\n--- Empty Input Tests ---")
result = classify_document("")
record(
    "Classifier: Empty string",
    "UNKNOWN",
    result.document_type.value,
    result.document_type == DocumentType.UNKNOWN,
    critique="Good: empty text is handled locally without calling the LLM."
)

result = classify_document("   ")
record(
    "Classifier: Whitespace only",
    "UNKNOWN",
    result.document_type.value,
    result.document_type == DocumentType.UNKNOWN,
)

result = classify_document(None)
record(
    "Classifier: None input",
    "UNKNOWN",
    result.document_type.value,
    result.document_type == DocumentType.UNKNOWN,
)

# Test classification dataset
print("\n--- Classification Dataset Tests ---")
classification_tests = [
    # INVOICE TESTS
    {
        "name": "Clear Invoice",
        "text": """INVOICE
Invoice Number: INV-2026-001
Date: September 4, 2026
Due Date: September 30, 2026

Bill To: XYZ Solutions Pvt Ltd
From: ABC Technologies Pvt Ltd

Item: Laptop, Quantity: 2, Unit Price: 50,000, Amount: 100,000
Subtotal: 100,000
Tax (18%): 18,000
Total: 118,000
Payment Terms: Net 30""",
        "expected": DocumentType.INVOICE,
    },
    {
        "name": "Invoice without title",
        "text": """Document #: 4872
Date: 2026-08-15
Due: 2026-09-15

Seller: Global Supplies Inc
Buyer: Metro Industries

1. Office Chairs (x10) - $2,500
2. Standing Desks (x5) - $3,750
Subtotal: $6,250
Sales Tax: $562.50
Total Due: $6,812.50""",
        "expected": DocumentType.INVOICE,
    },
    # CONTRACT TESTS
    {
        "name": "Clear Contract",
        "text": """SERVICE AGREEMENT

This Agreement is entered into as of January 1, 2026
between ABC Corporation ("Party A") and XYZ Services ("Party B").

1. SCOPE OF WORK
Party B shall provide software development services...

2. TERM
This agreement shall be effective from January 1, 2026
and shall continue until December 31, 2026.

3. COMPENSATION
Party A shall pay Party B a total of $120,000...

4. TERMINATION
Either party may terminate this agreement with 30 days written notice.""",
        "expected": DocumentType.CONTRACT,
    },
    {
        "name": "Contract looking like invoice",
        "text": """MASTER SERVICES AGREEMENT

Contract Value: $500,000
Payment Schedule: Monthly installments of $41,666.67

Party A: TechCorp Inc
Party B: DataServices LLC

Effective Date: March 1, 2026
Term: 12 months

SCOPE: Data analytics platform development and maintenance
PAYMENT TERMS: Net 30 from invoice date
TERMINATION: 60 days written notice""",
        "expected": DocumentType.CONTRACT,
    },
    # MEDICAL REPORT TESTS
    {
        "name": "Clear Medical Report",
        "text": """PATHOLOGY REPORT

Patient Name: John Smith
Patient ID: MRN-2026-4521
Date: September 3, 2026
Referring Doctor: Dr. Sarah Johnson
Facility: City General Hospital

TEST RESULTS:
1. Complete Blood Count (CBC)
   - Hemoglobin: 14.2 g/dL (Reference: 13.5-17.5)
   - WBC: 7,500 /μL (Reference: 4,500-11,000)

IMPRESSION: Normal blood work
RECOMMENDATION: Routine follow-up in 12 months""",
        "expected": DocumentType.MEDICAL_REPORT,
    },
    # FINANCIAL STATEMENT TESTS
    {
        "name": "Clear Financial Statement",
        "text": """CONSOLIDATED INCOME STATEMENT
TechCorp International Ltd
For the Quarter Ended September 30, 2026

Revenue: $45,000,000
Cost of Goods Sold: ($18,000,000)
Gross Profit: $27,000,000

Operating Expenses: ($12,000,000)
Operating Income: $15,000,000
Net Income: $11,250,000

Total Assets: $180,000,000
Total Liabilities: $72,000,000
Total Equity: $108,000,000""",
        "expected": DocumentType.FINANCIAL_STATEMENT,
    },
    {
        "name": "Financial looking like invoice",
        "text": """QUARTERLY FINANCIAL REPORT
Q3 2026

Revenue Breakdown:
Product Sales: $30,000,000
Service Revenue: $15,000,000
Total Revenue: $45,000,000

Expense Categories:
COGS: $18,000,000
Salaries: $8,000,000
Operating: $4,000,000

Net Profit: $15,000,000""",
        "expected": DocumentType.FINANCIAL_STATEMENT,
    },
    # UNKNOWN DOCUMENT TESTS
    {
        "name": "Meeting Minutes (should be UNKNOWN)",
        "text": """MEETING MINUTES
Date: September 4, 2026
Attendees: Alice, Bob, Charlie

Agenda:
1. Project status update
2. Budget review
3. Next steps

Notes:
Alice reported that the project is on track.
Bob mentioned concerns about the timeline.
Action: Charlie to prepare updated schedule by Friday.""",
        "expected": DocumentType.UNKNOWN,
    },
    {
        "name": "Random text (should be UNKNOWN)",
        "text": """The quick brown fox jumps over the lazy dog.
Pack my box with five dozen liquor jugs.
How vexingly quick daft zebras jump.""",
        "expected": DocumentType.UNKNOWN,
    },
    # DIFFICULT CASES
    {
        "name": "Short ambiguous text",
        "text": "Total: $5,000. Due: Oct 15.",
        "expected": DocumentType.INVOICE,
    },
    {
        "name": "Info appears AFTER 500 chars",
        "text": ("x" * 600) + "\nINVOICE NUMBER: INV-001\nTotal: $5000\n",
        "expected": DocumentType.INVOICE,
    },
]

correct = 0
total = len(classification_tests)
confusion = {}

for test in classification_tests:
    print(f"\n  Testing: {test['name']}")
    start = time.time()
    try:
        result = classify_document(test["text"])
        elapsed = time.time() - start
        predicted = result.document_type
        expected = test["expected"]
        passed = predicted == expected

        if passed:
            correct += 1

        # Build confusion matrix
        exp_val = expected.value
        pred_val = predicted.value
        confusion.setdefault(exp_val, {})
        confusion[exp_val][pred_val] = confusion[exp_val].get(pred_val, 0) + 1

        critique = ""
        if test["name"] == "Info appears AFTER 500 chars" and not passed:
            critique = ("CRITICAL WEAKNESS: The classifier uses only the first 500 characters. "
                       "This document's invoice information appears after position 600. "
                       "The 500-char truncation causes misclassification. "
                       "ALTERNATIVES: (1) Use first page text, (2) title/heading extraction, "
                       "(3) representative sampling, (4) two-pass classification.")
        
        record(
            f"Classify: {test['name']}",
            expected.value,
            f"{predicted.value} ({elapsed:.2f}s)",
            passed,
            critique=critique,
        )
    except Exception as e:
        record(
            f"Classify: {test['name']}",
            test["expected"].value,
            f"Error: {type(e).__name__}: {str(e)[:100]}",
            False,
        )

print(f"\n  ACCURACY: {correct}/{total} = {correct/total*100:.1f}%")

print("\n  CONFUSION MATRIX:")
all_types = sorted(set(list(confusion.keys()) + [v for d in confusion.values() for v in d.keys()]))
header = "  " + " " * 22 + "  ".join(f"{t[:8]:>8}" for t in all_types)
print(header)
for actual_type in all_types:
    row = f"  {actual_type:>20}  "
    for pred_type in all_types:
        count = confusion.get(actual_type, {}).get(pred_type, 0)
        row += f"{count:>8}  "
    print(row)


# ============================================================
# PHASE 6: API FAILURE TESTS (mocked)
# ============================================================
print("\n" + "=" * 60)
print("PHASE 6: API FAILURE TESTS (MOCKED)")
print("=" * 60)

# Test: What happens if the API raises an exception
print("\n--- Simulated API Failures ---")

# Mock the client to simulate failures
from pipeline import classifier

# Test: Network timeout
print("\n  Testing: Simulated timeout")
original_client = classifier.client
try:
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"document_type": "invoice"}'
    mock_client.models.generate_content.side_effect = TimeoutError("Connection timed out")
    classifier.client = mock_client

    try:
        result = classify_document("Invoice text here")
        record("API: Timeout handling", "Exception propagated", f"Result: {result}", False,
               critique="Timeout was silently swallowed.")
    except TimeoutError:
        record("API: Timeout handling", "TimeoutError propagated", "TimeoutError raised", True,
               critique="The classifier does not catch or retry on timeout. This means the caller "
                        "must handle retries. This is acceptable if the caller implements retry logic, "
                        "but currently there is no retry mechanism anywhere in the codebase.")
    except Exception as e:
        record("API: Timeout handling", "TimeoutError propagated", f"{type(e).__name__}: {e}", False)
finally:
    classifier.client = original_client

# Test: Rate limit simulation
print("\n  Testing: Simulated rate limit (429)")
try:
    mock_client = MagicMock()
    # Simulate a 429-like error
    mock_client.models.generate_content.side_effect = Exception("429 Resource has been exhausted")
    classifier.client = mock_client

    try:
        result = classify_document("Invoice text")
        record("API: Rate limit (429)", "Exception propagated", f"Result: {result}", False)
    except Exception as e:
        has_429 = "429" in str(e)
        record("API: Rate limit (429)", "Exception with 429 info", f"{type(e).__name__}: {str(e)[:100]}", True,
               critique="No retry/backoff logic for rate limits. The error propagates directly. "
                        "In production, this should have exponential backoff with jitter.")
finally:
    classifier.client = original_client

# Test: Malformed response
print("\n  Testing: Simulated malformed JSON response")
try:
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = 'not valid json at all'
    mock_client.models.generate_content.return_value = mock_response
    classifier.client = mock_client

    try:
        result = classify_document("Some text")
        record("API: Malformed JSON", "Validation error", f"Result: {result}", False,
               critique="Malformed JSON was accepted somehow.")
    except Exception as e:
        record("API: Malformed JSON", "Exception raised", f"{type(e).__name__}: {str(e)[:100]}", True,
               critique="Malformed LLM response raises exception. Good — invalid responses are not silently accepted.")
finally:
    classifier.client = original_client

# Test: Invalid document type in response
print("\n  Testing: Simulated invalid document type")
try:
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"document_type": "email"}'  # Not a valid DocumentType
    mock_client.models.generate_content.return_value = mock_response
    classifier.client = mock_client

    try:
        result = classify_document("Some text")
        record("API: Invalid type in response", "Validation error", f"Result: {result.document_type}", False,
               critique="The LLM returned an invalid document type ('email') which was accepted.")
    except Exception as e:
        record("API: Invalid type in response", "Validation error",
               f"{type(e).__name__}: {str(e)[:100]}", True,
               critique="Good: Pydantic rejects document types not in the enum.")
finally:
    classifier.client = original_client


# ============================================================
# PHASE 7: EXTRACTION TESTS
# ============================================================
print("\n" + "=" * 60)
print("PHASE 7: EXTRACTION TESTS")
print("=" * 60)

try:
    from pipeline.extractor import extract_document
    record("Extractor: Import", "Import succeeds", "Imported", True)
except ImportError as e:
    record("Extractor: Import", "Import succeeds", f"ImportError: {e}", False,
           critique="CRITICAL: Cannot import extractor.")
    print("\nCANNOT PROCEED — extractor import failed")
    sys.exit(1)

# Check for the MedicalReportData import bug
print("\n--- Import Bug Check ---")
try:
    from models.medical import MedicalReportData
    record("Extractor: MedicalReportData exists", "Class exists", "Found", True)
except ImportError:
    record("Extractor: MedicalReportData exists", "Class exists", "ImportError",  False,
           critique="CRITICAL BUG: models/medical.py defines 'MedicalReportDate' (typo with 'Date' instead of 'Data'). "
                    "extractor.py imports 'MedicalReportData' which does not exist. "
                    "Any attempt to process a medical report will crash with ImportError.")

# Test: Empty text
print("\n--- Empty Text ---")
try:
    extract_document("", DocumentType.INVOICE)
    record("Extractor: Empty text", "ValueError", "No error", False)
except ValueError as e:
    record("Extractor: Empty text", "ValueError", f"ValueError: {e}", True)

# Test: Unsupported document type
print("\n--- Unsupported Type ---")
try:
    extract_document("Some text", DocumentType.UNKNOWN)
    record("Extractor: UNKNOWN type", "ValueError", "No error", False)
except ValueError as e:
    record("Extractor: UNKNOWN type", "ValueError", f"ValueError: {e}", True)

# Test: Real invoice extraction
print("\n--- Real Invoice Extraction ---")
invoice_text = """
INVOICE

Invoice Number: INV-2026-0847
Invoice Date: September 4, 2026
Due Date: September 30, 2026

From: ABC Technologies Pvt Ltd
To: XYZ Solutions Pvt Ltd

Items:
1. Laptop (Dell Latitude 5540)
   Quantity: 2
   Unit Price: ₹50,000
   Amount: ₹100,000

2. Mouse (Logitech MX Master)
   Quantity: 2
   Unit Price: ₹5,000
   Amount: ₹10,000

Subtotal: ₹110,000
Tax (18% GST): ₹19,800
Discount: ₹5,000
Total: ₹124,800

Currency: INR
Payment Terms: Net 30
"""

ground_truth_invoice = {
    "invoice_number": "INV-2026-0847",
    "invoice_date": "2026-09-04",
    "due_date": "2026-09-30",
    "vendor_name": "ABC Technologies Pvt Ltd",
    "customer_name": "XYZ Solutions Pvt Ltd",
    "subtotal": 110000,
    "tax": 19800,
    "discount": 5000,
    "total": 124800,
    "currency": "INR",
    "item_count": 2,
}

start = time.time()
try:
    result = extract_document(invoice_text, DocumentType.INVOICE)
    elapsed = time.time() - start
    
    print(f"\n  Extraction took {elapsed:.2f}s")
    print(f"  Result type: {type(result).__name__}")
    
    # Semantic comparison
    checks = {
        "invoice_number": (result.invoice_number, ground_truth_invoice["invoice_number"]),
        "vendor_name": (result.vendor_name, ground_truth_invoice["vendor_name"]),
        "customer_name": (result.customer_name, ground_truth_invoice["customer_name"]),
        "total": (result.total, ground_truth_invoice["total"]),
        "subtotal": (result.subtotal, ground_truth_invoice["subtotal"]),
        "tax": (result.tax, ground_truth_invoice["tax"]),
        "discount": (result.discount, ground_truth_invoice["discount"]),
        "currency": (result.currency, ground_truth_invoice["currency"]),
        "item_count": (len(result.items), ground_truth_invoice["item_count"]),
    }

    semantic_pass = 0
    semantic_total = len(checks)
    
    for field, (actual, expected) in checks.items():
        match = False
        if isinstance(expected, (int, float)):
            match = abs(actual - expected) < 0.01
        else:
            match = str(actual).strip().lower() == str(expected).strip().lower()
        
        if match:
            semantic_pass += 1
        
        record(
            f"Extract Invoice: {field}",
            str(expected),
            str(actual),
            match,
            critique=f"SEMANTIC MISMATCH: LLM extracted '{actual}' but ground truth is '{expected}'" if not match else "",
        )
    
    # Check date fields
    if hasattr(result, 'invoice_date') and result.invoice_date:
        expected_date = date(2026, 9, 4)
        record(
            "Extract Invoice: invoice_date",
            str(expected_date),
            str(result.invoice_date),
            result.invoice_date == expected_date,
        )
    
    print(f"\n  SEMANTIC ACCURACY: {semantic_pass}/{semantic_total} = {semantic_pass/semantic_total*100:.1f}%")
    
    # Check mathematical consistency
    expected_total = result.subtotal + result.tax - result.discount
    math_match = abs(result.total - expected_total) < 0.01
    record(
        "Extract Invoice: Math consistency (subtotal+tax-discount=total)",
        f"{result.subtotal}+{result.tax}-{result.discount}={expected_total}",
        f"total={result.total}",
        math_match,
        critique=f"Math inconsistency: {result.subtotal}+{result.tax}-{result.discount}={expected_total} but total={result.total}" if not math_match else "",
    )

except Exception as e:
    elapsed = time.time() - start
    record("Extract Invoice: Full extraction", "Successful extraction", 
           f"Error after {elapsed:.2f}s: {type(e).__name__}: {str(e)[:200]}", False,
           critique=f"Invoice extraction failed completely: {e}")


# Test: Contract extraction
print("\n--- Real Contract Extraction ---")
contract_text = """
SERVICE AGREEMENT

Contract ID: CON-2026-0042
Title: Software Development Services Agreement

This Agreement is entered into between:
Party A: TechCorp India Pvt Ltd
Party B: DataWorks Solutions LLC

Effective Date: January 1, 2026
Expiration Date: December 31, 2026

Contract Value: $240,000
Currency: USD

SCOPE OF WORK:
Development and maintenance of a cloud-based data analytics platform,
including dashboard design, API development, and database optimization.

Payment Terms: Monthly invoicing, Net 30
Termination: Either party may terminate with 60 days written notice
Governing Law: State of Delaware, United States
"""

start = time.time()
try:
    result = extract_document(contract_text, DocumentType.CONTRACT)
    elapsed = time.time() - start
    print(f"  Extraction took {elapsed:.2f}s")
    
    record("Extract Contract: contract_id", "CON-2026-0042", str(result.contract_id),
           "CON-2026-0042" in str(result.contract_id))
    record("Extract Contract: party_a", "TechCorp India Pvt Ltd", str(result.party_a),
           "TechCorp" in str(result.party_a))
    record("Extract Contract: party_b", "DataWorks Solutions LLC", str(result.party_b),
           "DataWorks" in str(result.party_b))
    if result.contract_value:
        record("Extract Contract: contract_value", "240000", str(result.contract_value),
               abs(result.contract_value - 240000) < 0.01)
except Exception as e:
    record("Extract Contract: Full extraction", "Success", f"Error: {e}", False)


# ============================================================
# PHASE 8: EDGE CASE EXTRACTION TESTS
# ============================================================
print("\n" + "=" * 60)
print("PHASE 8: EXTRACTION EDGE CASES")
print("=" * 60)

# Test: Missing fields — does the LLM hallucinate?
print("\n--- Missing Fields Test ---")
minimal_invoice = """
Invoice #: 999
Date: 2026-09-01
Total: $100
"""

try:
    result = extract_document(minimal_invoice, DocumentType.INVOICE)
    
    # Check if LLM invented missing fields
    hallucination_checks = {
        "vendor_name": result.vendor_name,
        "customer_name": result.customer_name,
        "currency": result.currency,
    }
    
    for field, value in hallucination_checks.items():
        # These fields are REQUIRED in the schema but NOT in the document
        # The LLM is forced to provide them because Pydantic requires them
        record(
            f"Hallucination: {field}",
            "None/empty (field missing from document)",
            str(value),
            False,  # This is always a concern
            critique=f"ARCHITECTURAL WEAKNESS: '{field}' is required in schema but not in document. "
                     f"The LLM was forced to provide '{value}'. If this was hallucinated, "
                     f"it's a semantic error that Pydantic cannot catch. "
                     f"SOLUTION: Make these fields Optional[str] or add confidence scores."
        )
except Exception as e:
    record("Hallucination test", "Extraction succeeds", f"Error: {e}", False)


# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("CLASSIFIER + EXTRACTOR TEST SUMMARY")
print("=" * 60)
print(f"Total: {PASS + FAIL}")
print(f"PASS:  {PASS}")
print(f"FAIL:  {FAIL}")

print()
print("CRITICAL ISSUES:")
criticals = [r for r in RESULTS if "CRITICAL" in r.get("critique", "")]
for i, c in enumerate(criticals, 1):
    print(f"  {i}. [{c['test']}] {c['critique']}")

print()
print("ARCHITECTURAL WEAKNESSES:")
weaknesses = [r for r in RESULTS if "WEAKNESS" in r.get("critique", "") or "ARCHITECTURAL" in r.get("critique", "")]
for i, w in enumerate(weaknesses, 1):
    print(f"  {i}. [{w['test']}] {w['critique']}")

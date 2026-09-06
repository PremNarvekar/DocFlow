"""
PHASE 3 — PYDANTIC MODEL TESTING
Tests every document model for valid data, missing fields, wrong types,
null/optional fields, invalid dates, invalid numerics, and extra fields.
"""
import sys
import json
from datetime import date
from pathlib import Path

# Ensure backend is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import ValidationError

from models.invoice import InvoiceData, InvoiceItem
from models.contract import ContractData
from models.medical import TestResult
from models.financial import FinancialStatementData

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
        "actual": actual,
        "status": status,
        "critique": critique,
    })
    icon = "✓" if passed else "✗"
    print(f"  {icon} {test_name}: {status}")
    if critique:
        print(f"    CRITIQUE: {critique}")


def test_expects_success(test_name, model_class, data, critique=""):
    """Test that valid data is accepted."""
    try:
        obj = model_class(**data)
        record(test_name, "Validation succeeds", "Validation succeeded", True, critique)
        return obj
    except (ValidationError, Exception) as e:
        record(test_name, "Validation succeeds", f"Error: {e}", False, critique)
        return None


def test_expects_failure(test_name, model_class, data, critique=""):
    """Test that invalid data is rejected."""
    try:
        obj = model_class(**data)
        record(test_name, "Validation error", f"Accepted: {obj}", False, critique)
        return obj
    except ValidationError as e:
        record(test_name, "Validation error", "Validation error raised", True, critique)
        return None
    except Exception as e:
        record(test_name, "ValidationError", f"Unexpected error: {type(e).__name__}: {e}", False, critique)
        return None


# ============================================================
# INVOICE MODEL TESTS
# ============================================================
print("\n" + "=" * 60)
print("INVOICE MODEL TESTS")
print("=" * 60)

# Test 1: Valid invoice
test_expects_success("Invoice: Valid complete data", InvoiceData, {
    "invoice_number": "INV-001",
    "invoice_date": "2026-09-04",
    "due_date": "2026-09-30",
    "vendor_name": "ABC Corp",
    "customer_name": "XYZ Ltd",
    "currency": "INR",
    "items": [{"description": "Laptop", "quantity": 2, "unit_price": 50000, "amount": 100000}],
    "subtotal": 100000,
    "tax": 18000,
    "discount": 5000,
    "total": 113000,
    "payment_terms": "Net 30",
})

# Test 2: Missing required field (invoice_number)
test_expects_failure("Invoice: Missing invoice_number", InvoiceData, {
    "invoice_date": "2026-09-04",
    "vendor_name": "ABC Corp",
    "customer_name": "XYZ Ltd",
    "currency": "INR",
    "items": [{"description": "Laptop", "quantity": 2, "unit_price": 50000, "amount": 100000}],
    "subtotal": 100000,
    "tax": 18000,
    "discount": 5000,
    "total": 113000,
})

# Test 3: Missing optional field (due_date)
test_expects_success("Invoice: Missing optional due_date", InvoiceData, {
    "invoice_number": "INV-002",
    "invoice_date": "2026-09-04",
    "vendor_name": "ABC Corp",
    "customer_name": "XYZ Ltd",
    "currency": "INR",
    "items": [{"description": "Laptop", "quantity": 2, "unit_price": 50000, "amount": 100000}],
    "subtotal": 100000,
    "tax": 18000,
    "discount": 5000,
    "total": 113000,
})

# Test 4: Wrong type for invoice_date
test_expects_failure("Invoice: Wrong type for invoice_date (int)", InvoiceData, {
    "invoice_number": "INV-003",
    "invoice_date": 12345,
    "vendor_name": "ABC Corp",
    "customer_name": "XYZ Ltd",
    "currency": "INR",
    "items": [{"description": "Laptop", "quantity": 2, "unit_price": 50000, "amount": 100000}],
    "subtotal": 100000,
    "tax": 18000,
    "discount": 5000,
    "total": 113000,
}, critique="Pydantic may coerce int to date. Check if this is desirable.")

# Test 5: Invalid date string
test_expects_failure("Invoice: Invalid date string", InvoiceData, {
    "invoice_number": "INV-004",
    "invoice_date": "not-a-date",
    "vendor_name": "ABC Corp",
    "customer_name": "XYZ Ltd",
    "currency": "INR",
    "items": [{"description": "Laptop", "quantity": 2, "unit_price": 50000, "amount": 100000}],
    "subtotal": 100000,
    "tax": 18000,
    "discount": 5000,
    "total": 113000,
})

# Test 6: Empty items list
test_expects_success("Invoice: Empty items list", InvoiceData, {
    "invoice_number": "INV-005",
    "invoice_date": "2026-09-04",
    "vendor_name": "ABC Corp",
    "customer_name": "XYZ Ltd",
    "currency": "INR",
    "items": [],
    "subtotal": 0,
    "tax": 0,
    "discount": 0,
    "total": 0,
}, critique="WEAKNESS: An invoice with zero items should arguably be rejected. "
           "The schema does not enforce min_length on items list.")

# Test 7: Negative total
test_expects_success("Invoice: Negative total", InvoiceData, {
    "invoice_number": "INV-006",
    "invoice_date": "2026-09-04",
    "vendor_name": "ABC Corp",
    "customer_name": "XYZ Ltd",
    "currency": "INR",
    "items": [{"description": "Laptop", "quantity": 1, "unit_price": 50000, "amount": 50000}],
    "subtotal": 50000,
    "tax": 0,
    "discount": 0,
    "total": -50000,
}, critique="WEAKNESS: Negative total is accepted. No ge=0 constraint on monetary fields. "
           "This means an LLM could hallucinate negative amounts and Pydantic would accept them.")

# Test 8: Negative quantity
test_expects_success("Invoice: Negative quantity", InvoiceItem, {
    "description": "Widget",
    "quantity": -5,
    "unit_price": 100,
    "amount": -500,
}, critique="WEAKNESS: Negative quantity is accepted. No ge=0 constraint.")

# Test 9: Total does not match subtotal + tax - discount
test_expects_success("Invoice: Mathematically inconsistent total", InvoiceData, {
    "invoice_number": "INV-007",
    "invoice_date": "2026-09-04",
    "vendor_name": "ABC Corp",
    "customer_name": "XYZ Ltd",
    "currency": "INR",
    "items": [{"description": "Laptop", "quantity": 2, "unit_price": 50000, "amount": 100000}],
    "subtotal": 100000,
    "tax": 18000,
    "discount": 5000,
    "total": 999999,
}, critique="CRITICAL WEAKNESS: Pydantic accepts total=999999 when subtotal(100000)+tax(18000)-discount(5000)=113000. "
           "There is no cross-field validation. This is a semantic bug that deterministic Python validation must catch.")

# Test 10: due_date before invoice_date
test_expects_success("Invoice: due_date before invoice_date", InvoiceData, {
    "invoice_number": "INV-008",
    "invoice_date": "2026-09-30",
    "due_date": "2026-09-01",
    "vendor_name": "ABC Corp",
    "customer_name": "XYZ Ltd",
    "currency": "INR",
    "items": [{"description": "Service", "quantity": 1, "unit_price": 1000, "amount": 1000}],
    "subtotal": 1000,
    "tax": 0,
    "discount": 0,
    "total": 1000,
}, critique="WEAKNESS: due_date (Sept 1) is before invoice_date (Sept 30). No cross-field date validation.")

# Test 11: Extra fields
try:
    obj = InvoiceData(
        invoice_number="INV-009",
        invoice_date="2026-09-04",
        vendor_name="ABC",
        customer_name="XYZ",
        currency="INR",
        items=[{"description": "X", "quantity": 1, "unit_price": 1, "amount": 1}],
        subtotal=1, tax=0, discount=0, total=1,
        extra_field_that_should_not_exist="surprise",
    )
    # Check if extra field is silently dropped or kept
    has_extra = hasattr(obj, 'extra_field_that_should_not_exist')
    if has_extra:
        record("Invoice: Extra fields", "Rejected or ignored", "Extra field kept", False,
               "Extra fields are being stored. model_config should forbid extras.")
    else:
        record("Invoice: Extra fields", "Rejected or ignored", "Extra field silently ignored", True,
               "Pydantic ignores extra fields by default. Consider model_config = ConfigDict(extra='forbid') "
               "to catch unexpected LLM output.")
except (ValidationError, TypeError) as e:
    record("Invoice: Extra fields", "Rejected or ignored", f"Rejected: {type(e).__name__}", True,
           "Good: extra fields are rejected.")


# ============================================================
# CONTRACT MODEL TESTS
# ============================================================
print("\n" + "=" * 60)
print("CONTRACT MODEL TESTS")
print("=" * 60)

test_expects_success("Contract: Valid complete data", ContractData, {
    "contract_id": "CON-001",
    "title": "Service Agreement",
    "party_a": "Company A",
    "party_b": "Company B",
    "effective_date": "2026-01-01",
    "expiration_date": "2027-01-01",
    "contract_value": 500000,
    "currency": "INR",
    "scope_of_work": "Software development services",
    "payment_terms": "Monthly",
    "termination_terms": "30 days notice",
    "governing_law": "Indian law",
})

test_expects_failure("Contract: Missing contract_id", ContractData, {
    "title": "Service Agreement",
    "party_a": "Company A",
    "party_b": "Company B",
    "effective_date": "2026-01-01",
    "scope_of_work": "Software development",
})

test_expects_failure("Contract: Missing scope_of_work", ContractData, {
    "contract_id": "CON-002",
    "title": "Service Agreement",
    "party_a": "Company A",
    "party_b": "Company B",
    "effective_date": "2026-01-01",
})

test_expects_success("Contract: Expiration before effective date", ContractData, {
    "contract_id": "CON-003",
    "title": "Bad Agreement",
    "party_a": "Company A",
    "party_b": "Company B",
    "effective_date": "2027-01-01",
    "expiration_date": "2026-01-01",
    "scope_of_work": "Nothing",
}, critique="WEAKNESS: Expiration date is before effective date. No cross-field date validation.")

test_expects_success("Contract: Negative contract value", ContractData, {
    "contract_id": "CON-004",
    "title": "Weird Contract",
    "party_a": "A",
    "party_b": "B",
    "effective_date": "2026-01-01",
    "contract_value": -100000,
    "scope_of_work": "Something",
}, critique="WEAKNESS: Negative contract value accepted. No ge=0 constraint.")


# ============================================================
# MEDICAL REPORT MODEL TESTS
# ============================================================
print("\n" + "=" * 60)
print("MEDICAL REPORT MODEL TESTS")
print("=" * 60)

# CRITICAL BUG CHECK: The file defines MedicalReportDate, but extractor imports MedicalReportData
try:
    from models.medical import MedicalReportData
    record("Medical: MedicalReportData import", "Import succeeds", "Import succeeded", True)
except ImportError as e:
    record("Medical: MedicalReportData import", "Import succeeds", f"ImportError: {e}", False,
           "CRITICAL BUG: The model file defines 'MedicalReportDate' (typo) but extractor.py "
           "imports 'MedicalReportData'. This will crash at runtime.")

# Test with the actual class name from the file
from models.medical import MedicalReportDate as MedicalReportActual

test_expects_success("Medical: Valid complete data", MedicalReportActual, {
    "patient_id": "P-001",
    "patient_name": "John Doe",
    "report_date": "2026-09-04",
    "doctor_name": "Dr. Smith",
    "facility_name": "City Hospital",
    "tests": [{"name": "Blood Sugar", "result": "110 mg/dL", "unit": "mg/dL", "reference_range": "70-110"}],
    "findings": ["Normal glucose levels"],
    "impression": "Healthy",
    "recommendation": ["Regular checkup in 6 months"],
})

test_expects_failure("Medical: Missing patient_id", MedicalReportActual, {
    "patient_name": "John Doe",
    "report_date": "2026-09-04",
    "tests": [{"name": "Blood Sugar", "result": "110"}],
})

test_expects_success("Medical: Empty tests list", MedicalReportActual, {
    "patient_id": "P-002",
    "patient_name": "Jane Doe",
    "report_date": "2026-09-04",
    "tests": [],
}, critique="WEAKNESS: A medical report with no tests should arguably be rejected.")


# ============================================================
# FINANCIAL STATEMENT MODEL TESTS
# ============================================================
print("\n" + "=" * 60)
print("FINANCIAL STATEMENT MODEL TESTS")
print("=" * 60)

test_expects_success("Financial: Valid complete data", FinancialStatementData, {
    "company_name": "TechCorp",
    "reporting_period": "Q3 2026",
    "currency": "INR",
    "revenue": 10000000,
    "cost_of_goods_sold": 4000000,
    "gross_profit": 6000000,
    "operating_expenses": 2000000,
    "operating_income": 4000000,
    "net_income": 3500000,
    "total_assets": 50000000,
    "total_liabilities": 20000000,
    "total_equity": 30000000,
    "operating_cash_flow": 5000000,
    "investing_cash_flow": -1000000,
    "financing_cash_flow": -2000000,
})

test_expects_failure("Financial: Missing company_name", FinancialStatementData, {
    "reporting_period": "Q3 2026",
    "currency": "INR",
    "revenue": 10000000,
    "net_income": 3500000,
})

test_expects_success("Financial: Inconsistent profit calculation", FinancialStatementData, {
    "company_name": "BadMath Corp",
    "reporting_period": "Q3 2026",
    "currency": "INR",
    "revenue": 10000000,
    "cost_of_goods_sold": 4000000,
    "gross_profit": 9999999,
    "net_income": 3500000,
}, critique="WEAKNESS: gross_profit(9999999) != revenue(10000000) - COGS(4000000). "
           "No cross-field arithmetic validation.")

test_expects_success("Financial: Assets != Liabilities + Equity", FinancialStatementData, {
    "company_name": "Imbalanced Corp",
    "reporting_period": "Q3 2026",
    "currency": "INR",
    "revenue": 1000000,
    "net_income": 500000,
    "total_assets": 100000,
    "total_liabilities": 50000,
    "total_equity": 10000,
}, critique="WEAKNESS: total_assets(100000) != total_liabilities(50000) + total_equity(10000). "
           "Balance sheet equation not validated.")


# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("MODEL TEST SUMMARY")
print("=" * 60)
print(f"Total: {PASS + FAIL}")
print(f"PASS:  {PASS}")
print(f"FAIL:  {FAIL}")
print()

print("ARCHITECTURAL WEAKNESSES FOUND:")
weaknesses = [r for r in RESULTS if "WEAKNESS" in r.get("critique", "") or "CRITICAL" in r.get("critique", "")]
for i, w in enumerate(weaknesses, 1):
    print(f"  {i}. [{w['test']}] {w['critique']}")

print()
print("FAILED TESTS:")
failures = [r for r in RESULTS if r["status"] == "FAIL"]
if failures:
    for f in failures:
        print(f"  ✗ {f['test']}: Expected={f['expected']}, Actual={f['actual']}")
        if f.get("critique"):
            print(f"    {f['critique']}")
else:
    print("  None")

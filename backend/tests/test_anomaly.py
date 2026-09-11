from datetime import date

from models.invoice import InvoiceData, InvoiceItem
from pipeline.anomaly import check_invoice, document_fingerprint


def make_invoice(
    subtotal: float = 1000,
    tax: float = 180,
    discount: float = 80,
    total: float = 1100,
):
    return InvoiceData(
        invoice_number="INV-001",
        invoice_date=date(2026, 9, 7),
        vendor_name="ABC Technologies",
        customer_name="XYZ Solutions",
        currency="INR",
        items=[
            InvoiceItem(
                description="AI Development",
                quantity=1,
                unit_price=1000,
                amount=1000,
            )
        ],
        subtotal=subtotal,
        tax=tax,
        discount=discount,
        total=total,
    )


def test_valid_invoice_has_no_anomalies():
    invoice = make_invoice()

    report = check_invoice(invoice)

    assert report.has_anomalies is False
    assert report.count == 0


def test_total_mismatch_is_detected():
    invoice = make_invoice(total=1300)

    report = check_invoice(invoice)

    assert report.has_anomalies is True
    assert any(
        anomaly.code == "TOTAL_MISMATCH"
        for anomaly in report.anomalies
    )


def test_negative_amount_is_detected():
    invoice = make_invoice(subtotal=-100)

    report = check_invoice(invoice)

    assert report.has_anomalies is True
    assert any(
        anomaly.code == "NEGATIVE_AMOUNT"
        for anomaly in report.anomalies
    )


def test_duplicate_fingerprint_is_deterministic():
    text = "Invoice INV-001 ABC Technologies Total INR 1100"

    first = document_fingerprint(text)
    second = document_fingerprint(text)

    assert first == second


def test_fingerprint_ignores_whitespace_and_case():
    first = document_fingerprint("Invoice   INV-001")
    second = document_fingerprint("invoice inv-001")

    assert first == second
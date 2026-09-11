from datetime import date

import pytest
from pydantic import ValidationError

from models.invoice import InvoiceData, InvoiceItem
from models.contract import ContractData
from models.financial import FinancialStatementData


def test_invoice_negative_quantity_fails():
    with pytest.raises(ValidationError) as exc:
        InvoiceItem(
            description="Test Item",
            quantity=-5.0,
            unit_price=10.0,
            amount=50.0
        )
    assert "quantity" in str(exc.value)


def test_invoice_math_validation():
    # Correct math
    valid = InvoiceData(
        invoice_number="INV-001",
        invoice_date=date(2023, 1, 1),
        vendor_name="A",
        customer_name="B",
        currency="USD",
        items=[InvoiceItem(description="x", quantity=1, unit_price=100, amount=100)],
        subtotal=100.0,
        tax=10.0,
        discount=5.0,
        total=105.0
    )
    assert valid.total == 105.0

    # Incorrect math
    with pytest.raises(ValidationError) as exc:
        InvoiceData(
            invoice_number="INV-002",
            invoice_date=date(2023, 1, 1),
            vendor_name="A",
            customer_name="B",
            currency="USD",
            items=[InvoiceItem(description="x", quantity=1, unit_price=100, amount=100)],
            subtotal=100.0,
            tax=10.0,
            discount=5.0,
            total=999.0  # Wrong!
        )
    assert "Arithmetic failure" in str(exc.value)


def test_contract_date_validation():
    # Reversed dates
    with pytest.raises(ValidationError) as exc:
        ContractData(
            contract_id="C-001",
            title="Test",
            party_a="A",
            party_b="B",
            effective_date=date(2023, 1, 1),
            expiration_date=date(2022, 1, 1),  # Before effective
            scope_of_work="Test"
        )
    assert "effective_date cannot be later than expiration_date" in str(exc.value)


def test_financial_accounting_equation():
    # Incorrect Assets = Liab + Equity
    with pytest.raises(ValidationError) as exc:
        FinancialStatementData(
            company_name="Corp",
            reporting_period="Q1",
            currency="USD",
            revenue=1000,
            net_income=200,
            total_assets=1000.0,
            total_liabilities=500.0,
            total_equity=999.0 # Wrong, 500+999 != 1000
        )
    assert "Accounting equation failed" in str(exc.value)

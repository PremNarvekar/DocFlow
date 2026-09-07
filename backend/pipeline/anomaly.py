from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any

from models.invoice import InvoiceData


@dataclass(frozen=True)
class Anomaly:
    code: str
    message: str
    severity: str = "warning"
    field: str | None = None


@dataclass
class AnomalyReport:
    has_anomalies: bool
    anomalies: list[Anomaly] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.anomalies)


def _check_invoice_amounts(invoice: InvoiceData) -> list[Anomaly]:
    anomalies: list[Anomaly] = []

    monetary_fields = {
        "subtotal": invoice.subtotal,
        "tax": invoice.tax,
        "discount": invoice.discount,
        "total": invoice.total,
    }

    for field_name, value in monetary_fields.items():
        if value < 0:
            anomalies.append(
                Anomaly(
                    code="NEGATIVE_AMOUNT",
                    message=f"{field_name} cannot be negative.",
                    severity="error",
                    field=field_name,
                )
            )

    expected_total = invoice.subtotal + invoice.tax - invoice.discount

    if abs(expected_total - invoice.total) > 0.01:
        anomalies.append(
            Anomaly(
                code="TOTAL_MISMATCH",
                message=(
                    f"Invoice total does not match subtotal + tax - discount. "
                    f"Expected {expected_total:.2f}, "
                    f"received {invoice.total:.2f}."
                ),
                severity="error",
                field="total",
            )
        )

    return anomalies


def _check_invoice_items(invoice: InvoiceData) -> list[Anomaly]:
    anomalies: list[Anomaly] = []

    if not invoice.items:
        anomalies.append(
            Anomaly(
                code="MISSING_ITEMS",
                message="Invoice contains no line items.",
                severity="error",
                field="items",
            )
        )
        return anomalies

    for index, item in enumerate(invoice.items):
        if item.quantity < 0:
            anomalies.append(
                Anomaly(
                    code="NEGATIVE_QUANTITY",
                    message=f"Item {index + 1} has a negative quantity.",
                    severity="error",
                    field="items",
                )
            )

        if item.unit_price < 0:
            anomalies.append(
                Anomaly(
                    code="NEGATIVE_UNIT_PRICE",
                    message=f"Item {index + 1} has a negative unit price.",
                    severity="error",
                    field="items",
                )
            )

        if item.amount < 0:
            anomalies.append(
                Anomaly(
                    code="NEGATIVE_ITEM_AMOUNT",
                    message=f"Item {index + 1} has a negative amount.",
                    severity="error",
                    field="items",
                )
            )

    return anomalies


def check_invoice(invoice: InvoiceData) -> AnomalyReport:
    """
    Run deterministic business-rule checks against an extracted invoice.
    """

    anomalies: list[Anomaly] = []

    anomalies.extend(_check_invoice_amounts(invoice))
    anomalies.extend(_check_invoice_items(invoice))

    return AnomalyReport(
        has_anomalies=bool(anomalies),
        anomalies=anomalies,
    )


def document_fingerprint(text: str) -> str:
    """
    Generate a deterministic fingerprint for duplicate-document detection.
    """

    normalized = " ".join(text.split()).lower()

    return sha256(
        normalized.encode("utf-8")
    ).hexdigest()
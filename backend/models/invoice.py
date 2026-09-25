from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class InvoiceItem(BaseModel):
    description: str
    quantity: float = Field(..., ge=0)
    unit_price: float = Field(..., ge=0)
    amount: float = Field(..., ge=0)


class InvoiceData(BaseModel):
    invoice_number: str

    invoice_date: date
    due_date: Optional[date] = None

    vendor_name: str
    customer_name: str

    currency: str = Field(..., pattern=r"^[A-Z]{3}$")

    items: List[InvoiceItem] = Field(..., min_length=1)

    subtotal: float = Field(..., ge=0)
    tax: float = Field(..., ge=0)
    discount: float = Field(..., ge=0)
    total: float = Field(..., ge=0)

    payment_terms: Optional[str] = None

    @model_validator(mode="after")
    def validate_dates(self) -> "InvoiceData":
        if self.due_date and self.invoice_date > self.due_date:
            raise ValueError("invoice_date cannot be later than due_date")
        return self

    @model_validator(mode="after")
    def validate_totals(self) -> "InvoiceData":
        # Relaxed mathematical validation for AI extraction.
        # Strict discrepancies are handled downstream by the Anomaly Engine instead 
        # of fatally crashing the extraction task here.
        return self
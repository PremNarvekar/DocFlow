from datetime import date
from typing import List, Optional

from pydantic import BaseModel


class InvoiceItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    amount: float


class InvoiceData(BaseModel):
    invoice_number: str

    invoice_date: date
    due_date: Optional[date] = None

    vendor_name: str
    customer_name: str

    currency: str

    items: List[InvoiceItem]

    subtotal: float
    tax: float
    discount: float
    total: float

    payment_terms: Optional[str] = None
from typing import Optional

from pydantic import BaseModel


class FinancialStatementData(BaseModel):
    company_name: str
    reporting_period: str
    currency: str

    revenue: float
    cost_of_goods_sold: Optional[float] = None
    gross_profit: Optional[float] = None

    operating_expenses: Optional[float] = None
    operating_income: Optional[float] = None
    net_income: float

    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    total_equity: Optional[float] = None

    operating_cash_flow: Optional[float] = None
    investing_cash_flow: Optional[float] = None
    financing_cash_flow: Optional[float] = None
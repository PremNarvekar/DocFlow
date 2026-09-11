from typing import Optional

from pydantic import BaseModel, Field, model_validator


class FinancialStatementData(BaseModel):
    company_name: str
    reporting_period: str
    currency: str = Field(..., pattern=r"^[A-Z]{3}$")

    revenue: float
    cost_of_goods_sold: Optional[float] = None
    gross_profit: Optional[float] = None

    operating_expenses: Optional[float] = None
    operating_income: Optional[float] = None
    net_income: float

    total_assets: Optional[float] = Field(None, ge=0)
    total_liabilities: Optional[float] = Field(None, ge=0)
    total_equity: Optional[float] = None

    operating_cash_flow: Optional[float] = None
    investing_cash_flow: Optional[float] = None
    financing_cash_flow: Optional[float] = None

    @model_validator(mode="after")
    def validate_equations(self) -> "FinancialStatementData":
        # 1. assets = liab + equity
        if (
            self.total_assets is not None 
            and self.total_liabilities is not None 
            and self.total_equity is not None
        ):
            expected_assets = self.total_liabilities + self.total_equity
            if abs(expected_assets - self.total_assets) > 0.02:
                raise ValueError(
                    f"Accounting equation failed: total_liabilities ({self.total_liabilities}) + "
                    f"total_equity ({self.total_equity}) = {expected_assets:.2f}, but total_assets is {self.total_assets}"
                )

        # 2. revenue - COGS = gross
        if (
            self.cost_of_goods_sold is not None
            and self.gross_profit is not None
        ):
            expected_gross = self.revenue - self.cost_of_goods_sold
            if abs(expected_gross - self.gross_profit) > 0.02:
                raise ValueError(
                    f"Income equation failed: revenue ({self.revenue}) - "
                    f"COGS ({self.cost_of_goods_sold}) = {expected_gross:.2f}, but gross_profit is {self.gross_profit}"
                )
                
        return self
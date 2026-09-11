from pydantic import BaseModel, Field, model_validator
from typing import Optional 
from datetime import date


class ContractData(BaseModel):
    contract_id:str
    title:str
    
    party_a: str
    party_b: str
    effective_date:date 
    expiration_date:Optional[date] = None
    
    contract_value: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, pattern=r"^[A-Z]{3}$")
    
    scope_of_work:str
    payment_terms: Optional[str] = None
    termination_terms: Optional[str] = None
    governing_law: Optional[str] = None
    
    @model_validator(mode="after")
    def validate_dates(self) -> "ContractData":
        if self.expiration_date and self.effective_date > self.expiration_date:
            raise ValueError("effective_date cannot be later than expiration_date")
        return self
    
    
    
    
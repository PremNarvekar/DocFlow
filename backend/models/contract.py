from pydantic import BaseModel
from typing import Optional 
from datetime import date


class ContractData(BaseModel):
    contract_id:str
    title:str
    
    party_a: str
    party_b: str
    effective_date:date 
    expiration_date:Optional[date] = None
    
    contract_value: Optional[float] = None
    currency: Optional[str] = None
    
    scope_of_work:str
    payment_terms: Optional[str] = None
    termination_terms: Optional[str] = None
    governing_law: Optional[str] = None
    
    
    
    
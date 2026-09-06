from pydantic import BaseModel
from typing import List , Optional 

from datetime import date

class TestResult(BaseModel):
    name: str
    result: str
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    
    
class MedicalReportData(BaseModel):
    patient_id:str
    patient_name:str
    
    report_date:date
    
    doctor_name:Optional[str] = None
    facility_name:Optional[str] = None
    
    tests:List[TestResult]
    
    findings:List[str] = []
    
    impression:Optional[str] = None
    recommendation: List[str] = []

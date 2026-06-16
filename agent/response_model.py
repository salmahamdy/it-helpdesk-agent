from pydantic import BaseModel

class HelpdeskResponse(BaseModel):
    issue_class:str 
    confidence:float
    diagnosis_summary:str
    resolution_steps:list[str]
    commands:list[str]
    escalation_required: bool
    preventive_measures: list[str]
    used_rag: bool

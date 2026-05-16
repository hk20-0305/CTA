# app/schemas.py - COMPLETE FIX
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class PatientBase(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None


class PatientCreate(BaseModel):
    name: str
    age: int
    gender: str
    comorbidities: List[str] = []  # ✅ Changed to List
    medications: List[str] = []     # ✅ Changed to List


class PatientResponse(PatientBase):
    id: int
    mrn: str
    comorbidities: List[str] = []   # ✅ Added
    medications: List[str] = []      # ✅ Added
    lab_values: Dict[str, Any] = {}  # ✅ Added
    created_at: datetime

    class Config:
        from_attributes = True


class TrialBase(BaseModel):
    title: str
    condition: Optional[str] = None
    phase: Optional[str] = None


class TrialCreate(BaseModel):
    title: str
    condition: str
    phase: Optional[str] = ""
    inclusion_criteria: List[str] = []   # ✅ Changed to List
    exclusion_criteria: List[str] = []   # ✅ Changed to List


class TrialResponse(TrialBase):
    id: int
    trial_id: str
    inclusion_criteria: List[str] = []   # ✅ Added
    exclusion_criteria: List[str] = []   # ✅ Added
    created_at: datetime

    class Config:
        from_attributes = True


class EligibilityCheckResponse(BaseModel):
    check_id: int = Field(alias="id")    # ✅ Fixed: alias id to check_id
    overall_score: float = Field(..., ge=0, le=1)
    confidence_score: float = Field(..., ge=0, le=100)
    status: str
    explanation: str
    evidence: Optional[Dict[str, Any]] = {}
    matched_criteria: Optional[List[Any]] = []
    excluded_criteria: Optional[List[Any]] = []
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True  # ✅ Allow both id and check_id


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    hospital_name: Optional[str] = None


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    hospital_name: Optional[str] = None

    class Config:
        from_attributes = True

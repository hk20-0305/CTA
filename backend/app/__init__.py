# app/__init__.py
"""
Clinical Trial Eligibility Automation App
"""

from .main import app
from .config import settings
from .database import engine, Base, get_db
from .models import User, Patient, Trial, EligibilityCheck, AuditLog
from .schemas import (
    UserCreate, UserOut, PatientBase, PatientCreate, PatientResponse,
    TrialBase, TrialCreate, TrialResponse, EligibilityCheckResponse
)
from .services import (
    document_parser,
    nlp_engine,
    matching_engine,
    audit_service,
    # explainability_engine,  # ← remove or comment this, file does not exist
)

from .utils import helpers, normalization

# Make sure all models are imported so SQLAlchemy can create tables
__all__ = [
    "app",
    "settings",
    "engine",
    "Base",
    "get_db",
    "User",
    "Patient",
    "Trial",
    "EligibilityCheck",
    "AuditLog",
    "UserCreate",
    "UserOut",
    "PatientBase",
    "PatientCreate",
    "PatientResponse",
    "TrialBase",
    "TrialCreate",
    "TrialResponse",
    "EligibilityCheckResponse",
    "document_parser",
    "nlp_engine",
    "matching_engine",
    #"explainability_engine",
    "audit_service",
    "helpers",
    "normalization"
]

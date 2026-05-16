# backend/app/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text, ForeignKey, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(500), nullable=False)
    name = Column(String(255), nullable=False)
    hospital_name = Column(String(255))
    role = Column(String(50), default="researcher")
    created_at = Column(DateTime, default=datetime.utcnow)

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    mrn = Column(String(100), unique=True, nullable=False)
    name = Column(String(255))
    age = Column(Integer)
    gender = Column(String(10))
    medical_history = Column(JSON)
    medications = Column(JSON)
    lab_values = Column(JSON)
    comorbidities = Column(ARRAY(String))
    pdf_url = Column(String(500))
    extracted_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class Trial(Base):
    __tablename__ = "trials"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    trial_id = Column(String(100), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    inclusion_criteria = Column(JSON)
    exclusion_criteria = Column(JSON)
    condition = Column(String(500))
    phase = Column(String(10))
    pdf_url = Column(String(500))
    extracted_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class EligibilityCheck(Base):
    __tablename__ = "eligibility_checks"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="SET NULL"), nullable=True)
    trial_id = Column(Integer, ForeignKey("trials.id", ondelete="SET NULL"), nullable=True)
    overall_score = Column(Float)
    confidence_score = Column(Float)
    explanation = Column(Text)
    matched_criteria = Column(JSON)
    excluded_criteria = Column(JSON)
    evidence = Column(JSON)
    status = Column(String(50))  # eligible, not_eligible, unknown
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(255))
    check_id = Column(Integer, ForeignKey("eligibility_checks.id", ondelete="SET NULL"), nullable=True)
    changes = Column(JSON)
    ip_address = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

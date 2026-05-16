from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from typing import List, Optional
from pydantic import BaseModel
import logging

from app.database import get_db
from app.models import Patient, Trial, EligibilityCheck, User
from app.schemas import PatientResponse, TrialResponse, EligibilityCheckResponse
from app.api.auth import get_current_user
from app.services.document_parser import document_parser
from app.services.matching_engine import matching_engine
from app.services.explainability import explainability_engine
from app.services.audit_service import audit_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["core"])


# Pydantic models for JSON endpoints
class PatientCreate(BaseModel):
    name: str
    age: int
    gender: str
    comorbidities: List[str] = []
    medications: List[str] = []


class TrialCreate(BaseModel):
    title: str
    condition: str
    phase: Optional[str] = ""
    inclusion_criteria: List[str] = []
    exclusion_criteria: List[str] = []


# -------------------------------------------------------------------
# Patients CRUD
# -------------------------------------------------------------------

@router.get("/patients", response_model=List[PatientResponse])
def list_patients(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patients = db.query(Patient).filter(Patient.user_id == current_user.id).all()
    return patients


@router.get("/patients/{patient_id}", response_model=PatientResponse)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id, Patient.user_id == current_user.id)
        .first()
    )
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


@router.post("/patients/upload")
async def upload_patient_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload and parse patient PDF"""
    try:
        text = document_parser.extract_from_pdf(file)
        patient_data = document_parser.parse_patient_data(text)
        
        patient = Patient(
            user_id=current_user.id,
            mrn=f"MRN{current_user.id}{db.query(Patient).count() + 1}",
            name=patient_data.get("name"),
            age=patient_data.get("age"),
            gender=patient_data.get("gender"),
            comorbidities=patient_data.get("conditions", []),
            medications=patient_data.get("medications", []),
            lab_values=patient_data.get("lab_values", {})
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)
        
        return {
            "id": patient.id,
            "message": "Patient uploaded successfully",
            "extracted_data": patient_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")


@router.post("/patients", response_model=PatientResponse)
def create_patient(
    patient_data: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create patient manually"""
    patient = Patient(
        user_id=current_user.id,
        mrn=f"MRN{current_user.id}{db.query(Patient).count() + 1}",
        name=patient_data.name,
        age=patient_data.age,
        gender=patient_data.gender,
        comorbidities=patient_data.comorbidities,
        medications=patient_data.medications,
        lab_values={}
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.put("/patients/{patient_id}", response_model=PatientResponse)
def update_patient(
    patient_id: int,
    patient_data: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update patient"""
    patient = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.user_id == current_user.id
    ).first()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    patient.name = patient_data.name
    patient.age = patient_data.age
    patient.gender = patient_data.gender
    patient.comorbidities = list(patient_data.comorbidities)
    patient.medications = list(patient_data.medications)
    flag_modified(patient, "comorbidities")
    flag_modified(patient, "medications")
    
    db.commit()
    db.refresh(patient)
    return patient


@router.delete("/patients/{patient_id}")
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete patient - nullifies related eligibility checks then deletes"""
    patient = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.user_id == current_user.id
    ).first()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    try:
        # Nullify FK references in eligibility_checks first
        db.query(EligibilityCheck).filter(
            EligibilityCheck.patient_id == patient_id
        ).update({"patient_id": None}, synchronize_session="fetch")
        db.commit()
        
        db.delete(patient)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting patient {patient_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete patient: {str(e)}")
    
    return {"message": "Patient deleted successfully"}


# -------------------------------------------------------------------
# Trials CRUD
# -------------------------------------------------------------------

@router.get("/trials", response_model=List[TrialResponse])
def list_trials(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    trials = db.query(Trial).filter(Trial.user_id == current_user.id).all()
    return trials


@router.get("/trials/{trial_id}", response_model=TrialResponse)
def get_trial(
    trial_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    trial = (
        db.query(Trial)
        .filter(Trial.id == trial_id, Trial.user_id == current_user.id)
        .first()
    )
    if not trial:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial not found")
    return trial


@router.post("/trials/upload")
async def upload_trial_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload and parse trial PDF"""
    try:
        text = document_parser.extract_from_pdf(file)
        trial_data = document_parser.parse_trial_data(text)
        
        trial = Trial(
            user_id=current_user.id,
            trial_id=f"TRIAL{current_user.id}{db.query(Trial).count() + 1}",
            title=trial_data.get("title", "Unknown Trial"),
            condition=trial_data.get("condition"),
            inclusion_criteria=trial_data.get("inclusion_criteria", []),
            exclusion_criteria=trial_data.get("exclusion_criteria", [])
        )
        db.add(trial)
        db.commit()
        db.refresh(trial)
        
        return {
            "id": trial.id,
            "message": "Trial uploaded successfully",
            "extracted_data": trial_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")


@router.post("/trials", response_model=TrialResponse)
def create_trial(
    trial_data: TrialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create trial manually"""
    trial = Trial(
        user_id=current_user.id,
        trial_id=f"TRIAL{current_user.id}{db.query(Trial).count() + 1}",
        title=trial_data.title,
        condition=trial_data.condition,
        phase=trial_data.phase,
        inclusion_criteria=trial_data.inclusion_criteria,
        exclusion_criteria=trial_data.exclusion_criteria
    )
    db.add(trial)
    db.commit()
    db.refresh(trial)
    return trial


@router.put("/trials/{trial_id}", response_model=TrialResponse)
def update_trial(
    trial_id: int,
    trial_data: TrialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update trial"""
    trial = db.query(Trial).filter(
        Trial.id == trial_id,
        Trial.user_id == current_user.id
    ).first()
    
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    trial.title = trial_data.title
    trial.condition = trial_data.condition
    trial.phase = trial_data.phase
    trial.inclusion_criteria = list(trial_data.inclusion_criteria)
    trial.exclusion_criteria = list(trial_data.exclusion_criteria)
    flag_modified(trial, "inclusion_criteria")
    flag_modified(trial, "exclusion_criteria")
    
    db.commit()
    db.refresh(trial)
    return trial


@router.delete("/trials/{trial_id}")
def delete_trial(
    trial_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete trial - nullifies related eligibility checks then deletes"""
    trial = db.query(Trial).filter(
        Trial.id == trial_id,
        Trial.user_id == current_user.id
    ).first()
    
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    try:
        # Nullify FK references in eligibility_checks first
        db.query(EligibilityCheck).filter(
            EligibilityCheck.trial_id == trial_id
        ).update({"trial_id": None}, synchronize_session="fetch")
        db.commit()
        
        db.delete(trial)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting trial {trial_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete trial: {str(e)}")
    
    return {"message": "Trial deleted successfully"}


# -------------------------------------------------------------------
# Eligibility Check - FIXED WITH FORM DATA
# -------------------------------------------------------------------

@router.post("/eligibility/check")
async def check_eligibility(
    # ✅ FIXED: Use Form() for all form fields
    patient_id: Optional[int] = Form(None),
    trial_id: Optional[int] = Form(None),
    patient_text: Optional[str] = Form(None),
    trial_text: Optional[str] = Form(None),
    patient_pdf: Optional[UploadFile] = File(None),
    trial_pdf: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check eligibility between patient and trial
    Accepts multiple input formats for both patient and trial
    """
    try:
        logger.info("=" * 80)
        logger.info("🔬 ELIGIBILITY CHECK REQUEST RECEIVED")
        logger.info(f"User: {current_user.email} (ID: {current_user.id})")
        logger.info(f"Patient ID: {patient_id}, Trial ID: {trial_id}")
        logger.info(f"Patient text: {bool(patient_text)}, Trial text: {bool(trial_text)}")
        logger.info(f"Patient PDF: {bool(patient_pdf)}, Trial PDF: {bool(trial_pdf)}")
        
        # ===== EXTRACT PATIENT DATA =====
        patient_data = None
        patient_obj = None
        
        import json
        import ast

        def parse_json_list(val):
            if isinstance(val, str):
                try: 
                    res = json.loads(val)
                    return res if isinstance(res, list) else [res]
                except Exception:
                    try:
                        res = ast.literal_eval(val)
                        return res if isinstance(res, list) else [res]
                    except Exception:
                        v = val.strip()
                        if (v.startswith('[') and v.endswith(']')) or (v.startswith('{') and v.endswith('}')):
                            v = v[1:-1].strip()
                            if not v:
                                return []
                            return [x.strip().strip("'\"") for x in v.split(',') if x.strip()]
                        return [val] if val else []
            return val if isinstance(val, list) else (list(val) if val else [])
            
        def parse_json_dict(val):
            if isinstance(val, str):
                try: 
                    res = json.loads(val)
                    return res if isinstance(res, dict) else {}
                except Exception:
                    try:
                        res = ast.literal_eval(val)
                        return res if isinstance(res, dict) else {}
                    except Exception: return {}
            return val if isinstance(val, dict) else {}

        if patient_id:
            logger.info(f"📋 Using existing patient ID: {patient_id}")
            patient_obj = db.query(Patient).filter(
                Patient.id == patient_id,
                Patient.user_id == current_user.id
            ).first()
            
            if not patient_obj:
                raise HTTPException(status_code=404, detail="Patient not found")
            
            patient_data = {
                "id": patient_obj.id,
                "name": patient_obj.name,
                "age": patient_obj.age,
                "gender": patient_obj.gender,
                "conditions": parse_json_list(patient_obj.comorbidities),
                "comorbidities": parse_json_list(patient_obj.comorbidities),
                "medications": parse_json_list(patient_obj.medications),
                "lab_values": parse_json_dict(patient_obj.lab_values)
            }
            logger.info(f"✅ Patient loaded: {patient_data['name']}, Age {patient_data['age']}")
        
        elif patient_text:
            logger.info("📝 Parsing patient from text input")
            parsed = document_parser.parse_patient_data(patient_text)
            patient_data = {
                "name": parsed.get("name", "Unknown"),
                "age": parsed.get("age"),
                "gender": parsed.get("gender"),
                "conditions": parsed.get("conditions", []),
                "comorbidities": parsed.get("conditions", []),
                "medications": parsed.get("medications", []),
                "lab_values": parsed.get("lab_values", {})
            }
            logger.info(f"✅ Patient parsed: {patient_data['name']}")
        
        elif patient_pdf:
            logger.info("📄 Parsing patient from PDF")
            text = document_parser.extract_from_pdf(patient_pdf)
            parsed = document_parser.parse_patient_data(text)
            patient_data = {
                "name": parsed.get("name", "Unknown"),
                "age": parsed.get("age"),
                "gender": parsed.get("gender"),
                "conditions": parsed.get("conditions", []),
                "comorbidities": parsed.get("conditions", []),
                "medications": parsed.get("medications", []),
                "lab_values": parsed.get("lab_values", {})
            }
            logger.info(f"✅ Patient extracted from PDF: {patient_data['name']}")
        
        else:
            raise HTTPException(status_code=400, detail="No patient data provided")
        
        
        # ===== EXTRACT TRIAL DATA =====
        trial_data = None
        trial_obj = None
        
        if trial_id:
            logger.info(f"🧪 Using existing trial ID: {trial_id}")
            trial_obj = db.query(Trial).filter(
                Trial.id == trial_id,
                Trial.user_id == current_user.id
            ).first()
            
            if not trial_obj:
                raise HTTPException(status_code=404, detail="Trial not found")
            
            trial_data = {
                "id": trial_obj.id,
                "trial_id": trial_obj.trial_id,
                "title": trial_obj.title,
                "condition": trial_obj.condition,
                "phase": trial_obj.phase,
                "inclusion_criteria": parse_json_list(trial_obj.inclusion_criteria),
                "exclusion_criteria": parse_json_list(trial_obj.exclusion_criteria)
            }
            logger.info(f"✅ Trial loaded: {trial_data['title']}")
            logger.info(f"   Inclusion criteria: {len(trial_data['inclusion_criteria'])}")
            logger.info(f"   Exclusion criteria: {len(trial_data['exclusion_criteria'])}")
        
        elif trial_text:
            logger.info("📝 Parsing trial from text input")
            parsed = document_parser.parse_trial_data(trial_text)
            trial_data = {
                "trial_id": "TEXT_TRIAL",
                "title": parsed.get("title", "Custom Trial"),
                "condition": parsed.get("condition"),
                "inclusion_criteria": parsed.get("inclusion_criteria", []),
                "exclusion_criteria": parsed.get("exclusion_criteria", [])
            }
            logger.info(f"✅ Trial parsed: {trial_data['title']}")
        
        elif trial_pdf:
            logger.info("📄 Parsing trial from PDF")
            text = document_parser.extract_from_pdf(trial_pdf)
            parsed = document_parser.parse_trial_data(text)
            trial_data = {
                "trial_id": "PDF_TRIAL",
                "title": parsed.get("title", "Uploaded Trial"),
                "condition": parsed.get("condition"),
                "inclusion_criteria": parsed.get("inclusion_criteria", []),
                "exclusion_criteria": parsed.get("exclusion_criteria", [])
            }
            logger.info(f"✅ Trial extracted from PDF: {trial_data['title']}")
        
        else:
            raise HTTPException(status_code=400, detail="No trial data provided")
        
        
        # ===== RUN ELIGIBILITY CHECK =====
        logger.info("🤖 Running ML-based eligibility matching...")
        check_result = matching_engine.check_eligibility(patient_data, trial_data)
        
        logger.info(f"✅ Match complete:")
        logger.info(f"   Overall Score: {check_result['overall_score']*100:.1f}%")
        logger.info(f"   Confidence: {check_result['confidence_score']:.1f}%")
        logger.info(f"   Status: {check_result['status'].upper()}")
        
        # Generate explanation
        logger.info("📝 Generating human-readable explanation...")
        explanation = explainability_engine.generate_explanation(check_result)
        check_result["explanation"] = explanation
        logger.info(f"✅ Explanation generated ({len(explanation)} chars)")
        
        
        # ===== SAVE TO DATABASE =====
        logger.info("💾 Saving eligibility check to database...")
        eligibility_check = EligibilityCheck(
            user_id=current_user.id,
            patient_id=patient_obj.id if patient_obj else None,
            trial_id=trial_obj.id if trial_obj else None,
            overall_score=check_result["overall_score"],
            confidence_score=check_result["confidence_score"],
            status=check_result["status"],
            explanation=explanation,
            matched_criteria=check_result.get("matched_criteria", []),
            excluded_criteria=check_result.get("excluded_criteria", []),
            evidence=check_result.get("evidence", {})
        )
        db.add(eligibility_check)
        db.commit()
        db.refresh(eligibility_check)
        logger.info(f"✅ Saved as check ID: {eligibility_check.id}")
        
        # Log audit
        await audit_service.log_check(
            user_id=current_user.id,
            check_id=eligibility_check.id,
            action="eligibility_check",
            details={
                "patient": patient_data.get("name"),
                "trial": trial_data.get("title"),
                "status": check_result["status"],
                "overall_score": check_result["overall_score"],
                "confidence": check_result["confidence_score"]
            }
        )
        
        logger.info("=" * 80)
        
        return check_result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ ELIGIBILITY CHECK FAILED")
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Eligibility check failed: {str(e)}")


# -------------------------------------------------------------------
# Eligibility checks history
# -------------------------------------------------------------------

@router.get("/checks", response_model=List[EligibilityCheckResponse])
def list_checks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        checks = (
            db.query(EligibilityCheck)
            .filter(EligibilityCheck.user_id == current_user.id)
            .order_by(EligibilityCheck.created_at.desc())
            .all()
        )
        return checks
    except Exception as e:
        logger.error(f"Error in list_checks: {e}")
        import traceback
        traceback.print_exc()
        return []
@router.get("/debug/check-data")
async def debug_check_data(
    patient_id: int,
    trial_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Debug endpoint to see actual data being matched"""
    
    patient = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.user_id == current_user.id
    ).first()
    
    trial = db.query(Trial).filter(
        Trial.id == trial_id,
        Trial.user_id == current_user.id
    ).first()
    
    if not patient or not trial:
        raise HTTPException(status_code=404, detail="Patient or trial not found")
    
    return {
        "patient": {
            "id": patient.id,
            "name": patient.name,
            "age": patient.age,
            "gender": patient.gender,
            "comorbidities": patient.comorbidities,
            "comorbidities_type": str(type(patient.comorbidities)),
            "medications": patient.medications,
            "medications_type": str(type(patient.medications)),
            "lab_values": patient.lab_values
        },
        "trial": {
            "id": trial.id,
            "title": trial.title,
            "condition": trial.condition,
            "inclusion_criteria": trial.inclusion_criteria,
            "inclusion_criteria_type": str(type(trial.inclusion_criteria)),
            "inclusion_criteria_count": len(trial.inclusion_criteria) if trial.inclusion_criteria else 0,
            "exclusion_criteria": trial.exclusion_criteria,
            "exclusion_criteria_type": str(type(trial.exclusion_criteria)),
            "exclusion_criteria_count": len(trial.exclusion_criteria) if trial.exclusion_criteria else 0
        }
    }

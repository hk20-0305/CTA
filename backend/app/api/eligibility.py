# backend/app/api/eligibility.py
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database import get_db
from app.models import Patient, Trial, EligibilityCheck, User
from app.api.auth import get_current_user
from app.services.document_parser import document_parser
from app.services.matching_engine import matching_engine
from app.services.explainability import explainability_engine

router = APIRouter(prefix="/api/eligibility", tags=["eligibility"])
logger = logging.getLogger(__name__)

@router.post("/check")
async def check_eligibility(
    patient_pdf: Optional[UploadFile] = File(None),
    trial_pdf: Optional[UploadFile] = File(None),
    patient_text: Optional[str] = Form(None),
    trial_text: Optional[str] = Form(None),
    patient_id: Optional[int] = Form(None),
    trial_id: Optional[int] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check eligibility by accepting:
    - PDF files (patient_pdf, trial_pdf) OR
    - Text input (patient_text, trial_text) OR
    - Existing IDs (patient_id, trial_id)
    """
    
    try:
        # Step 1: Get or parse patient data
        if patient_id:
            # Load from database
            patient = db.query(Patient).filter(
                Patient.id == patient_id,
                Patient.user_id == current_user.id
            ).first()
            if not patient:
                raise HTTPException(status_code=404, detail="Patient not found")
            
            patient_data = {
                "name": patient.name,
                "age": patient.age,
                "gender": patient.gender,
                "conditions": patient.comorbidities or [],
                "medications": patient.medications or [],
                "lab_values": patient.lab_values or {}
            }
        elif patient_pdf:
            # Parse PDF
            text = document_parser.extract_from_pdf(patient_pdf)
            patient_data = document_parser.parse_patient_data(text)
            
            # Save to database
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
            patient_id = patient.id
            
        elif patient_text:
            # Parse text
            patient_data = document_parser.parse_patient_data(patient_text)
            
            # Save to database
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
            patient_id = patient.id
        else:
            raise HTTPException(
                status_code=400,
                detail="Must provide patient_pdf, patient_text, or patient_id"
            )
        
        # Step 2: Get or parse trial data
        if trial_id:
            # Load from database
            trial = db.query(Trial).filter(
                Trial.id == trial_id,
                Trial.user_id == current_user.id
            ).first()
            if not trial:
                raise HTTPException(status_code=404, detail="Trial not found")
            
            trial_data = {
                "trial_id": trial.trial_id,
                "title": trial.title,
                "inclusion_criteria": trial.inclusion_criteria or [],
                "exclusion_criteria": trial.exclusion_criteria or [],
                "condition": trial.condition
            }
        elif trial_pdf:
            # Parse PDF
            text = document_parser.extract_from_pdf(trial_pdf)
            trial_data = document_parser.parse_trial_data(text)
            
            # Save to database
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
            trial_id = trial.id
            
        elif trial_text:
            # Parse text
            trial_data = document_parser.parse_trial_data(trial_text)
            
            # Save to database
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
            trial_id = trial.id
        else:
            raise HTTPException(
                status_code=400,
                detail="Must provide trial_pdf, trial_text, or trial_id"
            )
        
        # Step 3: Run matching engine
        logger.info(f"Checking eligibility for patient {patient_id} and trial {trial_id}")
        match_result = matching_engine.check_eligibility(patient_data, trial_data)
        
        # Step 4: Generate explanation
        explanation = explainability_engine.generate_explanation(match_result)
        
        # Step 5: Save eligibility check to database
        check = EligibilityCheck(
            user_id=current_user.id,
            patient_id=patient_id,
            trial_id=trial_id,
            overall_score=match_result["overall_score"],
            confidence_score=match_result["confidence_score"],
            status=match_result["status"],
            explanation=explanation,
            matched_criteria=match_result.get("matched_criteria", []),
            excluded_criteria=match_result.get("excluded_criteria", []),
            evidence=match_result.get("evidence", {})
        )
        db.add(check)
        db.commit()
        db.refresh(check)
        
        # Step 6: Return result
        return {
            "check_id": check.id,
            "patient_id": patient_id,
            "trial_id": trial_id,
            "overall_score": match_result["overall_score"],
            "confidence_score": match_result["confidence_score"],
            "status": match_result["status"],
            "explanation": explanation,
            "matched_criteria": match_result.get("matched_criteria", []),
            "excluded_criteria": match_result.get("excluded_criteria", []),
            "evidence": match_result.get("evidence", {}),
            "patient_summary": match_result.get("patient_summary", ""),
            "trial_summary": match_result.get("trial_summary", "")
        }
        
    except Exception as e:
        logger.error(f"Eligibility check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Eligibility check failed: {str(e)}")


@router.get("/history")
async def get_eligibility_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all eligibility checks for current user"""
    checks = db.query(EligibilityCheck).filter(
        EligibilityCheck.user_id == current_user.id
    ).order_by(EligibilityCheck.created_at.desc()).all()
    
    return checks


@router.get("/check/{check_id}")
async def get_check_details(
    check_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get details of a specific eligibility check"""
    check = db.query(EligibilityCheck).filter(
        EligibilityCheck.id == check_id,
        EligibilityCheck.user_id == current_user.id
    ).first()
    
    if not check:
        raise HTTPException(status_code=404, detail="Check not found")
    
    # Get patient and trial details
    patient = db.query(Patient).filter(Patient.id == check.patient_id).first()
    trial = db.query(Trial).filter(Trial.id == check.trial_id).first()
    
    return {
        "check": check,
        "patient": patient,
        "trial": trial
    }
#!/usr/bin/env python3
r"""
seed_data.py  –  Populate the CTA database with test patients and trials.

Usage:
    python seed_data.py
    python seed_data.py --email user@example.com   # seed for specific user
    python seed_data.py --clear                     # wipe existing demo data first

Patient ↔ Trial expected outcomes (for testing):

  ┌──────────────────────┬──────────────────────────────┬──────────────┐
  │ Patient              │ Trial                        │ Expected     │
  ├──────────────────────┼──────────────────────────────┼──────────────┤
  │ John Harker (55M)    │ TRIAL-DM2-001 (T2DM)        │ ✅ ELIGIBLE   │
  │ John Harker          │ TRIAL-DM1-003 (T1DM)        │ ❌ NOT ELIG   │
  │ Mary Chen (62F)      │ TRIAL-DM2-001 (T2DM)        │ ✅ ELIGIBLE   │
  │ Mary Chen            │ TRIAL-OB-010 (Obesity)       │ ❌ NOT ELIG   │
  │ Robert Singh (44M)   │ TRIAL-DM1-003 (T1DM)        │ ✅ ELIGIBLE   │
  │ Robert Singh         │ TRIAL-DM2-001 (T2DM)        │ ❌ NOT ELIG   │
  │ Patricia Williams    │ TRIAL-CKD-005 (CKD)         │ ✅ ELIGIBLE   │
  │ Patricia Williams    │ TRIAL-DM2-001 (T2DM)        │ ❌ NOT ELIG   │
  │ James Okafor (38M)   │ TRIAL-ASTH-006 (Asthma)     │ ✅ ELIGIBLE   │
  │ James Okafor         │ TRIAL-COPD-004 (COPD)       │ ❌ NOT ELIG   │
  │ Linda Patel (58F)    │ TRIAL-DM2-001 (T2DM)        │ ⚠️ BORDER     │
  │ David Moreau (50M)   │ TRIAL-COPD-004 (COPD)       │ ✅ ELIGIBLE   │
  │ Susan Kim (48F)      │ TRIAL-DM2-001 (T2DM)        │ ✅ ELIGIBLE   │
  │ Susan Kim            │ TRIAL-OB-010 (Obesity)       │ ❌ NOT ELIG   │
  │ Michael Thompson     │ TRIAL-AFIB-007 (AFib)       │ ✅ ELIGIBLE   │
  │ Michael Thompson     │ TRIAL-DM1-003 (T1DM)        │ ❌ NOT ELIG   │
  │ Nancy Garcia (35F)   │ TRIAL-DM2-001 (T2DM)        │ ❌ NOT ELIG   │
  │ Arun Mehta (52M)     │ TRIAL-DM2-001 (T2DM)        │ ✅ ELIGIBLE   │
  │ Clara Rossi (42F)    │ TRIAL-HTN-002 (HTN)         │ ✅ ELIGIBLE   │
  │ Clara Rossi          │ TRIAL-DM2-001 (T2DM)        │ ❌ NOT ELIG   │
  └──────────────────────┴──────────────────────────────┴──────────────┘
"""

import sys
import argparse
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from app.models import Base, User, Patient, Trial, EligibilityCheck
from app.api.auth import get_password_hash

# ── Patients ──────────────────────────────────────────────────────────────────
# Each patient is designed to clearly MATCH or NOT MATCH specific trials.

DEMO_PATIENTS = [
    # ── PERFECT T2DM match: age 55, T2DM, HbA1c 8.5 ≥ 7.5, BMI 29.4 ≥ 25, eGFR 72 > 30 ──
    {
        "name": "John Harker", "age": 55, "gender": "Male",
        "comorbidities": ["Type 2 Diabetes", "Hypertension"],
        "medications": ["Metformin 500mg", "Lisinopril 10mg"],
        "lab_values": {
            "hba1c": 8.5, "bmi": 29.4, "egfr": 72,
            "fasting_glucose": 165, "systolic_bp": 148, "diastolic_bp": 92,
            "cholesterol": 220, "ldl": 140, "hdl": 42, "creatinine": 1.1
        }
    },
    # ── T2DM match + obesity, HbA1c 9.1, BMI 33.7 (obese), excluded from Obesity trial by diabetes ──
    {
        "name": "Mary Chen", "age": 62, "gender": "Female",
        "comorbidities": ["Type 2 Diabetes", "Obesity"],
        "medications": ["Glimepiride 2mg", "Metformin 1000mg"],
        "lab_values": {
            "hba1c": 9.1, "bmi": 33.7, "egfr": 65,
            "fasting_glucose": 190, "cholesterol": 245, "ldl": 155
        }
    },
    # ── PERFECT T1DM match: T1DM, HbA1c 7.8 (in range 7.0–9.5), age 44 ──
    # ── Should FAIL T2DM trial (has T1DM = exclusion) ──
    {
        "name": "Robert Singh", "age": 44, "gender": "Male",
        "comorbidities": ["Type 1 Diabetes"],
        "medications": ["Insulin Glargine", "Aspirin 81mg"],
        "lab_values": {
            "hba1c": 7.8, "bmi": 24.1, "egfr": 95,
            "fasting_glucose": 140, "creatinine": 0.9
        }
    },
    # ── CKD patient: eGFR 28 (in range 25–75), SHOULD match CKD trial ──
    # ── Should FAIL T2DM trial (no diabetes, eGFR < 30 = exclusion) ──
    {
        "name": "Patricia Williams", "age": 70, "gender": "Female",
        "comorbidities": ["Hypertension", "Chronic Kidney Disease"],
        "medications": ["Furosemide 40mg", "Amlodipine 5mg"],
        "lab_values": {
            "egfr": 28, "bmi": 26.8, "creatinine": 2.8,
            "systolic_bp": 155, "diastolic_bp": 95
        }
    },
    # ── Asthma patient: should match Asthma trial, FAIL COPD trial (asthma = exclusion) ──
    {
        "name": "James Okafor", "age": 38, "gender": "Male",
        "comorbidities": ["Asthma"],
        "medications": ["Salbutamol inhaler", "Fluticasone 250mcg"],
        "lab_values": {
            "bmi": 22.5, "o2_saturation": 96, "hemoglobin": 14.5,
            "egfr": 110
        }
    },
    # ── Borderline T2DM: HbA1c 7.4 (just below 7.5 threshold), BMI 27.9 ≥ 25 ──
    {
        "name": "Linda Patel", "age": 58, "gender": "Female",
        "comorbidities": ["Type 2 Diabetes", "Hypertension"],
        "medications": ["Empagliflozin 10mg", "Losartan 50mg"],
        "lab_values": {
            "hba1c": 7.4, "bmi": 27.9, "egfr": 80,
            "systolic_bp": 142, "diastolic_bp": 88,
            "cholesterol": 210, "ldl": 130
        }
    },
    # ── COPD patient: should match COPD trial ──
    {
        "name": "David Moreau", "age": 50, "gender": "Male",
        "comorbidities": ["COPD"],
        "medications": ["Tiotropium inhaler", "Prednisone 5mg"],
        "lab_values": {
            "bmi": 25.1, "o2_saturation": 93, "hemoglobin": 13.8,
            "egfr": 88
        }
    },
    # ── Strong T2DM match: HbA1c 8.9, BMI 37.2 (obese) ──
    # ── Excluded from Obesity trial because has Diabetes ──
    {
        "name": "Susan Kim", "age": 48, "gender": "Female",
        "comorbidities": ["Type 2 Diabetes", "Obesity"],
        "medications": ["Metformin 500mg", "Semaglutide 1mg"],
        "lab_values": {
            "hba1c": 8.9, "bmi": 37.2, "egfr": 92,
            "fasting_glucose": 185, "cholesterol": 260, "ldl": 170
        }
    },
    # ── AFib + Heart Failure: should match AFib trial, eGFR 55 > 25 ──
    # ── Should FAIL T1DM trial (no diabetes at all) ──
    {
        "name": "Michael Thompson", "age": 66, "gender": "Male",
        "comorbidities": ["Atrial Fibrillation", "Heart Failure"],
        "medications": ["Apixaban 5mg", "Ramipril 5mg", "Bisoprolol 5mg"],
        "lab_values": {
            "egfr": 55, "bmi": 28.6, "creatinine": 1.4,
            "hemoglobin": 12.8
        }
    },
    # ── Healthy-ish (anemia only): should FAIL most trials ──
    {
        "name": "Nancy Garcia", "age": 35, "gender": "Female",
        "comorbidities": ["Anemia"],
        "medications": ["Folic acid 5mg", "Iron supplements"],
        "lab_values": {
            "hemoglobin": 10.2, "bmi": 21.3, "egfr": 105,
            "creatinine": 0.7
        }
    },
    # ── NEW: Perfect T2DM match with all labs ──
    {
        "name": "Arun Mehta", "age": 52, "gender": "Male",
        "comorbidities": ["Type 2 Diabetes", "Hypertension", "Dyslipidemia"],
        "medications": ["Metformin 1000mg", "Empagliflozin 25mg", "Atorvastatin 40mg"],
        "lab_values": {
            "hba1c": 8.2, "bmi": 31.5, "egfr": 68,
            "fasting_glucose": 172, "systolic_bp": 150, "diastolic_bp": 94,
            "cholesterol": 248, "ldl": 158, "hdl": 38, "triglycerides": 210,
            "creatinine": 1.2, "alt": 32, "ast": 28
        }
    },
    # ── NEW: Hypertension-only patient (no diabetes) — matches HTN trial, fails T2DM ──
    {
        "name": "Clara Rossi", "age": 42, "gender": "Female",
        "comorbidities": ["Hypertension"],
        "medications": ["Amlodipine 10mg", "Ramipril 10mg"],
        "lab_values": {
            "systolic_bp": 162, "diastolic_bp": 98, "bmi": 24.8,
            "egfr": 95, "cholesterol": 200, "ldl": 120, "creatinine": 0.8
        }
    },
]


# ── Trials ────────────────────────────────────────────────────────────────────

DEMO_TRIALS = [
    # ── T2DM trial: broad inclusion, clear numeric criteria ──
    {
        "trial_id": "TRIAL-DM2-001",
        "title": "Empagliflozin Phase 3 Study in Type 2 Diabetes Mellitus",
        "condition": "Type 2 Diabetes",
        "phase": "3",
        "inclusion_criteria": [
            "Age 30 to 75 years",
            "Diagnosed with Type 2 Diabetes Mellitus",
            "HbA1c >= 7.5%",
            "BMI >= 25",
            "Currently on oral antidiabetic medication"
        ],
        "exclusion_criteria": [
            "Type 1 Diabetes",
            "eGFR < 30 mL/min",
            "Pregnant or breastfeeding",
            "Active cancer treatment"
        ]
    },
    # ── HTN trial ──
    {
        "trial_id": "TRIAL-HTN-002",
        "title": "Resistant Hypertension Combination Therapy Trial",
        "condition": "Hypertension",
        "phase": "2",
        "inclusion_criteria": [
            "Age 40 to 80 years",
            "Diagnosed with Hypertension",
            "Systolic blood pressure > 140 mmHg",
            "Currently on at least one antihypertensive medication"
        ],
        "exclusion_criteria": [
            "eGFR < 30 mL/min",
            "Pregnancy",
            "Heart failure with reduced ejection fraction"
        ]
    },
    # ── T1DM trial: exclusion for T2DM ──
    {
        "trial_id": "TRIAL-DM1-003",
        "title": "Closed-Loop Insulin Delivery in Type 1 Diabetes",
        "condition": "Type 1 Diabetes",
        "phase": "2",
        "inclusion_criteria": [
            "Age 18 to 65 years",
            "Diagnosed with Type 1 Diabetes",
            "HbA1c between 7.0% and 9.5%",
            "Currently on insulin therapy"
        ],
        "exclusion_criteria": [
            "Type 2 Diabetes",
            "eGFR < 45 mL/min",
            "Pregnant or planning pregnancy"
        ]
    },
    # ── COPD trial: excludes Asthma ──
    {
        "trial_id": "TRIAL-COPD-004",
        "title": "Triple Therapy in Chronic Obstructive Pulmonary Disease",
        "condition": "COPD",
        "phase": "3",
        "inclusion_criteria": [
            "Age 40 to 80 years",
            "Confirmed COPD diagnosis",
            "History of smoking or tobacco use",
            "Oxygen saturation < 95%"
        ],
        "exclusion_criteria": [
            "Active lung cancer",
            "Diagnosed with Asthma",
            "eGFR < 30"
        ]
    },
    # ── CKD trial: eGFR range ──
    {
        "trial_id": "TRIAL-CKD-005",
        "title": "Finerenone in Chronic Kidney Disease with Comorbidities",
        "condition": "Chronic Kidney Disease",
        "phase": "3",
        "inclusion_criteria": [
            "Age 18 years or older",
            "Diagnosed with Chronic Kidney Disease",
            "eGFR between 25 and 75 mL/min"
        ],
        "exclusion_criteria": [
            "eGFR < 25 mL/min",
            "Pregnancy"
        ]
    },
    # ── Asthma trial: excludes COPD ──
    {
        "trial_id": "TRIAL-ASTH-006",
        "title": "Biologic Therapy for Moderate-to-Severe Persistent Asthma",
        "condition": "Asthma",
        "phase": "3",
        "inclusion_criteria": [
            "Age 18 to 75 years",
            "Diagnosed with moderate to severe asthma",
            "On inhaled corticosteroid therapy"
        ],
        "exclusion_criteria": [
            "Diagnosed with COPD",
            "Current smoker",
            "Active respiratory infection"
        ]
    },
    # ── AFib trial ──
    {
        "trial_id": "TRIAL-AFIB-007",
        "title": "Direct Oral Anticoagulant in Non-Valvular Atrial Fibrillation",
        "condition": "Atrial Fibrillation",
        "phase": "3",
        "inclusion_criteria": [
            "Age 50 to 85 years",
            "Diagnosed with Atrial Fibrillation or AFib",
            "Not on warfarin"
        ],
        "exclusion_criteria": [
            "eGFR < 25 mL/min",
            "Mechanical heart valve",
            "Active gastrointestinal bleeding"
        ]
    },
    # ── Heart Failure trial ──
    {
        "trial_id": "TRIAL-HF-008",
        "title": "SGLT2 Inhibitor in Heart Failure with Reduced Ejection Fraction",
        "condition": "Heart Failure",
        "phase": "3",
        "inclusion_criteria": [
            "Age 18 years or older",
            "Diagnosed with Heart Failure",
            "Ejection fraction <= 40%"
        ],
        "exclusion_criteria": [
            "eGFR < 20 mL/min",
            "Type 1 Diabetes",
            "Severe hepatic impairment"
        ]
    },
    # ── Dyslipidemia trial ──
    {
        "trial_id": "TRIAL-DYS-009",
        "title": "PCSK9 Inhibitor for Familial Dyslipidemia",
        "condition": "Dyslipidemia",
        "phase": "3",
        "inclusion_criteria": [
            "Age 35 to 75 years",
            "Diagnosed with Dyslipidemia or high cholesterol",
            "LDL > 130 mg/dL despite statin therapy"
        ],
        "exclusion_criteria": [
            "Active liver disease",
            "ALT or AST > 3x upper limit of normal"
        ]
    },
    # ── Obesity trial: excludes Diabetes ──
    {
        "trial_id": "TRIAL-OB-010",
        "title": "GLP-1 Agonist for Obesity Without Diabetes",
        "condition": "Obesity",
        "phase": "3",
        "inclusion_criteria": [
            "Age 18 to 70 years",
            "BMI >= 30",
            "No prior bariatric surgery"
        ],
        "exclusion_criteria": [
            "Diagnosed with Diabetes (Type 1 or Type 2)",
            "Thyroid disorder causing weight gain",
            "Pregnancy"
        ]
    },
]


# ── Seeding logic ─────────────────────────────────────────────────────────────

def seed(user_email=None, clear=False):
    log_path = os.path.join(os.path.dirname(__file__), "seed_log.txt")

    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"\n--- Seeding started at {datetime.now()} ---\n")
        log.flush()
        print("Starting seed process... (Check seed_log.txt for progress)")

        db = None
        try:
            # 1. Initialize DB
            log.write("🔨 Initializing database tables...\n")
            log.flush()
            Base.metadata.create_all(bind=engine)

            # 2. Open Session
            log.write("🔌 Opening DB session...\n")
            log.flush()
            db = SessionLocal()

            # 3. Find/Create User
            if user_email:
                user = db.query(User).filter(User.email == user_email).first()
                if not user:
                    log.write(f"❌ User {user_email} not found.\n")
                    print(f"❌ Error: User {user_email} not found.")
                    return
            else:
                user = db.query(User).order_by(User.id).first()
                if not user:
                    log.write("👤 No users found. Creating demo user: doctor@example.com\n")
                    user = User(
                        email="doctor@example.com",
                        password_hash=get_password_hash("password1123"),
                        name="Demo Doctor",
                        hospital_name="ClinSight Health",
                        role="researcher"
                    )
                    db.add(user)
                    db.commit()
                    db.refresh(user)
                    log.write(f"   ✅ Created user ID: {user.id}\n")

            log.write(f"👤 Seeding for User: {user.email} (ID: {user.id})\n")
            log.flush()

            # 3.5 Clear existing demo data if requested
            if clear:
                log.write("🗑️  Clearing existing demo data...\n")
                # Clear eligibility checks first (FK refs)
                db.query(EligibilityCheck).filter(
                    EligibilityCheck.user_id == user.id
                ).delete(synchronize_session="fetch")
                # Clear patients
                deleted_p = db.query(Patient).filter(
                    Patient.user_id == user.id,
                    Patient.mrn.like("P-DEMO-%")
                ).delete(synchronize_session="fetch")
                # Clear trials
                deleted_t = db.query(Trial).filter(
                    Trial.user_id == user.id,
                    Trial.trial_id.like("TRIAL-%-U%")
                ).delete(synchronize_session="fetch")
                db.commit()
                log.write(f"   Cleared {deleted_p} patients, {deleted_t} trials\n")
                print(f"   Cleared {deleted_p} patients, {deleted_t} trials")

            # 4. Seed Patients
            log.write("📋 Seeding patients...\n")
            p_added = 0
            for i, p_data in enumerate(DEMO_PATIENTS):
                mrn = f"P-DEMO-{user.id}-{i+1:03d}"
                if db.query(Patient).filter(Patient.mrn == mrn).first():
                    log.write(f"   ⏭️  Patient '{p_data['name']}' ({mrn}) already exists\n")
                    continue

                patient = Patient(
                    user_id=user.id,
                    mrn=mrn,
                    name=p_data["name"],
                    age=p_data["age"],
                    gender=p_data["gender"],
                    comorbidities=p_data["comorbidities"],
                    medications=p_data["medications"],
                    lab_values=p_data["lab_values"]
                )
                db.add(patient)
                p_added += 1
                log.write(f"   ✅ Added: {p_data['name']} ({mrn})\n")

            # 5. Seed Trials
            log.write("🧪 Seeding trials...\n")
            t_added = 0
            for t_data in DEMO_TRIALS:
                t_id = f"{t_data['trial_id']}-U{user.id}"
                if db.query(Trial).filter(Trial.trial_id == t_id).first():
                    log.write(f"   ⏭️  Trial '{t_data['title']}' ({t_id}) already exists\n")
                    continue

                trial = Trial(
                    user_id=user.id,
                    trial_id=t_id,
                    title=t_data["title"],
                    condition=t_data["condition"],
                    phase=t_data["phase"],
                    inclusion_criteria=t_data["inclusion_criteria"],
                    exclusion_criteria=t_data["exclusion_criteria"]
                )
                db.add(trial)
                t_added += 1
                log.write(f"   ✅ Added: {t_data['title']} ({t_id})\n")

            db.commit()
            log.write(f"🎉 Seeding complete. Added {p_added} patients and {t_added} trials.\n")
            print(f"🎉 Success! Added {p_added} patients and {t_added} trials.")
            print(f"\n📋 See the docstring at the top of this file for expected match results.")

        except Exception as e:
            log.write(f"❌ FATAL ERROR: {str(e)}\n")
            import traceback
            traceback.print_exc(file=log)
            traceback.print_exc()
            if db:
                db.rollback()
            print(f"❌ Seeding failed. Check seed_log.txt for details.")
        finally:
            if db:
                db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", help="Target user email")
    parser.add_argument("--clear", action="store_true", help="Clear existing demo data first")
    args = parser.parse_args()
    seed(args.email, args.clear)

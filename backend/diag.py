from app.database import SessionLocal, engine
from app.models import User, Patient, Trial
from sqlalchemy import text

def diagnostic():
    print("--- Diagnostic Start ---")
    try:
        db = SessionLocal()
        # Test connection
        db.execute(text("SELECT 1"))
        print("✅ DB Connection: OK")
        
        users = db.query(User).all()
        print(f"✅ Users found: {len(users)}")
        for u in users:
            print(f"   - User ID: {u.id}, Email: {u.email}")
            
        patients = db.query(Patient).count()
        trials = db.query(Trial).count()
        print(f"✅ Existing Patients: {patients}")
        print(f"✅ Existing Trials: {trials}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        print("--- Diagnostic End ---")

if __name__ == "__main__":
    diagnostic()

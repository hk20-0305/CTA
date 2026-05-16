# app/services/audit_service.py - FIXED VERSION
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import AuditLog, User, EligibilityCheck
import logging

logger = logging.getLogger(__name__)


# ===== Original functions (keep for backward compatibility) =====

def create_audit_log(
    db: Session,
    user_id: int,
    action: str,
    check_id: Optional[int] = None,
    changes: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    details: Optional[str] = None
):
    """
    Create an audit log entry for any significant action.
    """
    audit = AuditLog(
        user_id=user_id,
        action=action,
        check_id=check_id,
        changes=changes,
        ip_address=ip_address,
        created_at=datetime.utcnow()
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit


def log_eligibility_check(
    db: Session,
    user_id: int,
    check_id: int,
    patient_id: int,
    trial_id: int,
    status: str,
    confidence: float,
    ip_address: Optional[str] = None
):
    """
    Log a completed eligibility check with key details.
    """
    changes = {
        "check_id": check_id,
        "patient_id": patient_id,
        "trial_id": trial_id,
        "status": status,
        "confidence": confidence
    }
    create_audit_log(
        db=db,
        user_id=user_id,
        action="eligibility_check_completed",
        check_id=check_id,
        changes=changes,
        ip_address=ip_address
    )


def log_patient_upload(
    db: Session,
    user_id: int,
    patient_id: int,
    ip_address: Optional[str] = None
):
    """
    Log patient record upload.
    """
    changes = {"patient_id": patient_id}
    create_audit_log(
        db=db,
        user_id=user_id,
        action="patient_upload",
        changes=changes,
        ip_address=ip_address
    )


def log_trial_upload(
    db: Session,
    user_id: int,
    trial_id: int,
    ip_address: Optional[str] = None
):
    """
    Log trial protocol upload.
    """
    changes = {"trial_id": trial_id}
    create_audit_log(
        db=db,
        user_id=user_id,
        action="trial_upload",
        changes=changes,
        ip_address=ip_address
    )


def log_user_action(
    db: Session,
    user_id: int,
    action: str,
    details: Optional[str] = None,
    ip_address: Optional[str] = None
):
    """
    Log any user action (login, logout, etc).
    """
    create_audit_log(
        db=db,
        user_id=user_id,
        action=action,
        details=details,
        ip_address=ip_address
    )


def get_audit_logs(
    db: Session,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    limit: int = 100
):
    """
    Retrieve audit logs with optional filters.
    """
    query = db.query(AuditLog)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    return query.order_by(AuditLog.created_at.desc()).limit(limit).all()


# ===== NEW: Wrapper class for async compatibility =====

class AuditService:
    """
    Wrapper class for audit service to make it compatible with async/await
    and to provide a singleton instance
    """
    
    def __init__(self):
        logger.info("✅ AuditService initialized")
    
    async def log_check(
        self,
        user_id: int,
        check_id: int,
        action: str,
        details: Optional[Dict] = None
    ):
        """
        Async wrapper for logging eligibility checks
        Note: This is a simplified version for hackathon that just logs to console
        In production, you'd pass db session and use the functions above
        """
        try:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "check_id": check_id,
                "action": action,
                "details": details or {}
            }
            logger.info(f"📝 AUDIT: {action} by user {user_id} - Check {check_id}")
            logger.debug(f"   Details: {log_entry}")
        except Exception as e:
            logger.error(f"❌ Failed to log audit: {e}")
    
    async def log_action(
        self,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        details: Optional[Dict] = None
    ):
        """Async wrapper for logging general actions"""
        try:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "details": details or {}
            }
            logger.info(f"📝 AUDIT: {action} on {resource_type} by user {user_id}")
            logger.debug(f"   Details: {log_entry}")
        except Exception as e:
            logger.error(f"❌ Failed to log action: {e}")


# ✅ CREATE SINGLETON INSTANCE - This is what routes.py imports
audit_service = AuditService()

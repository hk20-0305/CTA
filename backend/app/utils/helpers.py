# app/utils/helpers.py
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


def generate_hash(data: str) -> str:
    """
    Generate SHA256 hash for a string.
    """
    return hashlib.sha256(data.encode()).hexdigest()


def sanitize_filename(filename: str) -> str:
    """
    Remove unsafe characters from filename.
    """
    return "".join(c for c in filename if c.isalnum() or c in "._- ")


def get_client_ip(request) -> str:
    """
    Extract client IP from request headers.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host


def log_request_details(
    request,
    response,
    start_time: float,
    user_id: Optional[int] = None
):
    """
    Log request details for monitoring.
    """
    duration = datetime.utcnow().timestamp() - start_time
    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"User: {user_id} "
        f"IP: {get_client_ip(request)} "
        f"Duration: {duration:.3f}s "
        f"Status: {response.status_code}"
    )


def format_error_message(error: Exception) -> Dict[str, Any]:
    """
    Format error details for logging.
    """
    return {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": datetime.utcnow().isoformat()
    }


def read_file_chunks(file_path: str, chunk_size: int = 1024 * 1024):
    """
    Generator to read large files in chunks.
    """
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk


def get_file_extension(filename: str) -> str:
    """
    Extract file extension.
    """
    return os.path.splitext(filename)[1].lower()

# backend/app/main.py - FIXED VERSION
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.database import engine, Base
from app.api.auth import router as auth_router
from app.api.routes import router as api_router
from app.api.eligibility import router as eligibility_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Clinical Trial Eligibility API",
    description="Automated clinical trial eligibility checking with explainability",
    version="1.0.0"
)

# IMPORTANT: Add CORS middleware FIRST, before routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Include routers AFTER CORS
app.include_router(auth_router)
app.include_router(api_router)
app.include_router(eligibility_router)

@app.get("/")
def root():
    return {
        "message": "Clinical Trial Eligibility API",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/auth",
            "patients": "/api/patients",
            "trials": "/api/trials",
            "eligibility": "/api/eligibility"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Error handler for debugging
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global error: {exc}", exc_info=True)
    return {
        "detail": str(exc),
        "type": type(exc).__name__
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
# app/config.py
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:abc@localhost:5432/postgres"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_hours: int = 24
    
    # API
    api_title: str = "Clinical Trial Eligibility API"
    api_version: str = "1.0.0"
    debug: bool = False
    
    # NLP Models
    biobert_model: str = "dmis-lab/biobert-base-cased-v1.1"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    generation_model: str = "distilgpt2"
    
    # OCR
    tesseract_cmd: str = "/usr/bin/tesseract"
    
    # Files
    max_pdf_size_mb: int = 50
    upload_dir: str = "uploads/"
    
    # NLP Thresholds
    semantic_similarity_threshold: float = 0.6
    confidence_min_threshold: float = 0.3
    confidence_max_threshold: float = 0.8

    class Config:
        env_file = ".env"

settings = Settings()

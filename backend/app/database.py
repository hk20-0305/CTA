# app/database.py
from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager
import logging
from .config import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.database_url,
    poolclass=pool.QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    echo=settings.debug
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized")

def test_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

"""
Netflix Platform - Database Session & Connection Management
SQLAlchemy engine initialization, connection pooling, and health checks.
"""

import os
import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.engine import Engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Database")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://netflix_admin:netflix_secure_pass@localhost:5432/netflix_platform"
)

Base = declarative_base()


def get_engine() -> Engine:
    """Factory to initialize database engine with fallback."""
    try:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info(f"Connected to database at {DATABASE_URL}")
        return engine
    except Exception as e:
        logger.warning(f"Failed to connect to primary DB ({e}). Using SQLite fallback.")
        fallback_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "netflix_platform.db")
        os.makedirs(os.path.dirname(fallback_path), exist_ok=True)
        fallback_url = f"sqlite:///{fallback_path}"
        engine = create_engine(fallback_url, connect_args={"check_same_thread": False})
        return engine


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_health(db_engine: Engine) -> dict:
    """Health check verifying database connectivity and table counts."""
    try:
        with db_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            
            # Check titles count
            titles_count = conn.execute(text("SELECT COUNT(*) FROM titles")).scalar() or 0
            interactions_count = conn.execute(text("SELECT COUNT(*) FROM user_interactions")).scalar() or 0
            
            is_postgres = "postgresql" in str(db_engine.url)
            vector_extension = False
            if is_postgres:
                ext_check = conn.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")).scalar()
                vector_extension = bool(ext_check)

        return {
            "status": "healthy",
            "database_type": "PostgreSQL (pgvector)" if is_postgres else "SQLite (Fallback)",
            "vector_extension_active": vector_extension or (not is_postgres),
            "total_titles": titles_count,
            "total_interactions": interactions_count
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "database_type": "unknown",
            "vector_extension_active": False,
            "total_titles": 0,
            "total_interactions": 0
        }
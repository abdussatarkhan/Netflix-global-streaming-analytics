"""
Netflix Streaming Intelligence & Personalization Platform - ETL Pipeline
Automated ingestion, cleaning, normalization, telemetry generation, and batch loading.
"""

import os
import re
import datetime
import logging
from typing import Optional, Tuple, Dict, Any, List
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ETL_Pipeline")


class NetflixETLPipeline:
    """
    Production-grade ETL pipeline handling raw title catalog data and
    streaming telemetry clickstream data.
    """

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.getenv(
            "DATABASE_URL", 
            "postgresql+psycopg2://netflix_admin:netflix_secure_pass@localhost:5432/netflix_platform"
        )
        self.engine: Optional[Engine] = None
        self._init_engine()

    def _init_engine(self) -> None:
        """Initialize SQLAlchemy database engine with connection pooling and graceful SQLite fallback."""
        try:
            self.engine = create_engine(
                self.db_url,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20
            )
            # Test connectivity
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Successfully connected to primary database.")
        except Exception as e:
            logger.warning(f"Failed to connect to primary DB ({e}). Initializing SQLite fallback.")
            fallback_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "netflix_platform.db")
            os.makedirs(os.path.dirname(fallback_path), exist_ok=True)
            self.db_url = f"sqlite:///{fallback_path}"
            self.engine = create_engine(self.db_url)
            logger.info(f"SQLite fallback engine initialized at {self.db_url}")

    @staticmethod
    def parse_date(val: Any) -> Optional[datetime.date]:
        """Standardize diverse date string formats into standard ISO date (YYYY-MM-DD)."""
        if pd.isna(val) or val is None or str(val).strip() == "":
            return None
        val_str = str(val).strip()
        for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%d-%b-%y", "%m/%d/%Y"):
            try:
                return datetime.datetime.strptime(val_str, fmt).date()
            except ValueError:
                continue
        # If parsing fails, attempt regex extraction of 4-digit year
        match = re.search(r"\b(19\d\d|20\d\d)\b", val_str)
        if match:
            return datetime.date(int(match.group(1)), 1, 1)
        return None

    def clean_titles(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """
        Cleans missing values, standardizes date formats, trims text,
        and standardizes column names.
        """
        logger.info(f"Cleaning raw titles dataset (initial rows: {len(raw_df)})...")
        df = raw_df.copy()

        # Rename 'cast' to 'cast_members' if present for SQL keyword safety
        if "cast" in df.columns and "cast_members" not in df.columns:
            df.rename(columns={"cast": "cast_members"}, inplace=True)

        required_cols = [
            "show_id", "type", "title", "director", "cast_members", 
            "country", "date_added", "release_year", "rating", "duration", 
            "listed_in", "description"
        ]

        # Ensure all columns exist
        for col in required_cols:
            if col not in df.columns:
                df[col] = np.nan

        # 1. Deduplicate by show_id
        df.drop_duplicates(subset=["show_id"], keep="last", inplace=True)

        # 2. Impute missing values
        df["show_id"] = df["show_id"].astype(str).str.strip()
        df["type"] = df["type"].fillna("Movie").astype(str).str.strip()
        df["title"] = df["title"].fillna("Untitled Content").astype(str).str.strip()
        df["director"] = df["director"].fillna("Unknown Director").astype(str).str.strip()
        df["cast_members"] = df["cast_members"].fillna("Unknown Cast").astype(str).str.strip()
        df["country"] = df["country"].fillna("Global / International").astype(str).str.strip()
        df["rating"] = df["rating"].fillna("TV-MA").astype(str).str.strip()
        df["duration"] = df["duration"].fillna("Unknown Duration").astype(str).str.strip()
        df["listed_in"] = df["listed_in"].fillna("General Entertainment").astype(str).str.strip()
        df["description"] = df["description"].fillna("No description available.").astype(str).str.strip()

        # 3. Clean and validate release_year
        df["release_year"] = pd.to_numeric(df["release_year"], errors="coerce").fillna(2022).astype(int)
        df["release_year"] = df["release_year"].apply(lambda y: max(1900, min(2026, y)))

        # 4. Standardize date_added
        df["date_added_parsed"] = df["date_added"].apply(self.parse_date)
        # Fallback date_added to Jan 1st of release_year if missing
        df["date_added"] = df.apply(
            lambda r: r["date_added_parsed"] if r["date_added_parsed"] is not None else datetime.date(r["release_year"], 1, 1),
            axis=1
        )
        df.drop(columns=["date_added_parsed"], inplace=True)

        logger.info(f"Titles dataset cleaned successfully (clean rows: {len(df)}).")
        return df[required_cols]

    def create_schema_tables(self) -> None:
        """Idempotently execute SQL schema against the database."""
        schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "schema.sql")
        if not os.path.exists(schema_path):
            logger.warning(f"Schema file not found at {schema_path}. Creating tables dynamically.")
            return

        with open(schema_path, "r", encoding="utf-8") as f:
            sql_script = f.read()

        logger.info("Applying database schema DDL...")
        with self.engine.begin() as conn:
            # If SQLite, strip pgvector specific statements
            if "sqlite" in self.db_url:
                sqlite_statements = [
                    """CREATE TABLE IF NOT EXISTS titles (
                        show_id VARCHAR(32) PRIMARY KEY,
                        type VARCHAR(32) NOT NULL DEFAULT 'Movie',
                        title VARCHAR(512) NOT NULL,
                        director TEXT,
                        cast_members TEXT,
                        country VARCHAR(256),
                        date_added DATE,
                        release_year INTEGER NOT NULL,
                        rating VARCHAR(32),
                        duration VARCHAR(64),
                        listed_in TEXT NOT NULL,
                        description TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );""",
                    """CREATE TABLE IF NOT EXISTS title_embeddings (
                        show_id VARCHAR(32) PRIMARY KEY REFERENCES titles(show_id) ON DELETE CASCADE,
                        embedding TEXT NOT NULL,
                        model_version VARCHAR(64) NOT NULL DEFAULT 'all-MiniLM-L6-v2',
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );""",
                    """CREATE TABLE IF NOT EXISTS user_interactions (
                        interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id VARCHAR(64) NOT NULL,
                        show_id VARCHAR(32) NOT NULL REFERENCES titles(show_id) ON DELETE CASCADE,
                        interaction_type VARCHAR(32) NOT NULL,
                        watch_duration_pct NUMERIC(5, 2) NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );"""
                ]
                for stmt in sqlite_statements:
                    conn.execute(text(stmt))
            else:
                # PostgreSQL
                conn.execute(text(sql_script))
        logger.info("Schema tables created/verified.")

    def load_titles_batch(self, df: pd.DataFrame, batch_size: int = 500) -> int:
        """Batch upsert title records into database."""
        logger.info(f"Loading {len(df)} titles in batches of {batch_size}...")
        records = df.to_dict(orient="records")
        total_inserted = 0

        is_postgres = "postgresql" in self.db_url

        with self.engine.begin() as conn:
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                if is_postgres:
                    upsert_query = text("""
                        INSERT INTO titles (
                            show_id, type, title, director, cast_members, country,
                            date_added, release_year, rating, duration, listed_in, description
                        ) VALUES (
                            :show_id, :type, :title, :director, :cast_members, :country,
                            :date_added, :release_year, :rating, :duration, :listed_in, :description
                        )
                        ON CONFLICT (show_id) DO UPDATE SET
                            type = EXCLUDED.type,
                            title = EXCLUDED.title,
                            director = EXCLUDED.director,
                            cast_members = EXCLUDED.cast_members,
                            country = EXCLUDED.country,
                            date_added = EXCLUDED.date_added,
                            release_year = EXCLUDED.release_year,
                            rating = EXCLUDED.rating,
                            duration = EXCLUDED.duration,
                            listed_in = EXCLUDED.listed_in,
                            description = EXCLUDED.description,
                            updated_at = CURRENT_TIMESTAMP;
                    """)
                    conn.execute(upsert_query, batch)
                else:
                    # SQLite Replace
                    sqlite_query = text("""
                        INSERT OR REPLACE INTO titles (
                            show_id, type, title, director, cast_members, country,
                            date_added, release_year, rating, duration, listed_in, description
                        ) VALUES (
                            :show_id, :type, :title, :director, :cast_members, :country,
                            :date_added, :release_year, :rating, :duration, :listed_in, :description
                        );
                    """)
                    conn.execute(sqlite_query, batch)
                total_inserted += len(batch)

        logger.info(f"Successfully loaded {total_inserted} titles.")
        return total_inserted

    def load_interactions_batch(self, df: pd.DataFrame, batch_size: int = 1000) -> int:
        """Batch insert user clickstream interactions."""
        logger.info(f"Loading {len(df)} user interaction events in batches of {batch_size}...")
        records = df.to_dict(orient="records")
        total_inserted = 0

        with self.engine.begin() as conn:
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                insert_query = text("""
                    INSERT INTO user_interactions (
                        user_id, show_id, interaction_type, watch_duration_pct, timestamp
                    ) VALUES (
                        :user_id, :show_id, :interaction_type, :watch_duration_pct, :timestamp
                    );
                """)
                conn.execute(insert_query, batch)
                total_inserted += len(batch)

        logger.info(f"Successfully loaded {total_inserted} user interactions.")
        return total_inserted

    def run_pipeline(
        self, 
        raw_titles_csv: str, 
        num_synthetic_users: int = 150
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Executes full end-to-end ETL run."""
        logger.info(f"Starting ETL run using source CSV: {raw_titles_csv}")
        
        # 1. Initialize Tables
        self.create_schema_tables()

        # 2. Extract & Clean Titles
        raw_df = pd.read_csv(raw_titles_csv)
        clean_titles_df = self.clean_titles(raw_df)
        self.load_titles_batch(clean_titles_df)

        # 3. Generate & Ingest Telemetry
        from data.generate_interactions import generate_synthetic_interactions
        interactions_df = generate_synthetic_interactions(clean_titles_df, num_users=num_synthetic_users)
        self.load_interactions_batch(interactions_df)

        logger.info("ETL pipeline run complete.")
        return clean_titles_df, interactions_df


if __name__ == "__main__":
    csv_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw", "netflix_titles.csv")
    pipeline = NetflixETLPipeline()
    pipeline.run_pipeline(csv_file)

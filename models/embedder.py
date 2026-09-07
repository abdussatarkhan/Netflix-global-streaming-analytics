"""
Netflix Streaming Intelligence Platform - Dense Semantic Embedder
Uses sentence-transformers/all-MiniLM-L6-v2 (384 dimensions) for content embedding.
Includes deterministic unit-normalized hash projection fallback for offline/lightweight environments.
"""

import os
import re
import json
import logging
import hashlib
from typing import List, Union, Dict, Any, Optional
import numpy as np
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Embedder")


class ContentEmbedder:
    """
    Dense vector embedding generator for catalog items and natural language search queries.
    Standardized to 384-dimensional unit L2-normalized vectors.
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", dimension: int = 384):
        self.model_name = model_name
        self.dimension = dimension
        self.model = None
        self._load_model()

    def _load_model(self) -> None:
        """Attempt to load the pre-trained SentenceTransformer model."""
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading SentenceTransformer model '{self.model_name}'...")
            self.model = SentenceTransformer(self.model_name)
            logger.info("SentenceTransformer model loaded successfully.")
        except Exception as e:
            logger.warning(
                f"SentenceTransformer not available or failed to load ({e}). "
                "Enabling deterministic normalized semantic hash projection fallback (384-dim)."
            )
            self.model = None

    @staticmethod
    def build_text_representation(row: Union[pd.Series, Dict[str, Any]]) -> str:
        """
        Construct rich semantic text representation for a catalog title.
        Fuses title, content type, genres, director, cast, country, and synopsis.
        """
        title = str(row.get("title", "")).strip()
        c_type = str(row.get("type", "Movie")).strip()
        genres = str(row.get("listed_in", "")).strip()
        director = str(row.get("director", "")).strip()
        cast = str(row.get("cast_members", "") or row.get("cast", "")).strip()
        country = str(row.get("country", "")).strip()
        description = str(row.get("description", "")).strip()

        components = [
            f"Title: {title}",
            f"Content Type: {c_type}",
            f"Genres: {genres}",
        ]
        if director and director != "Unknown Director":
            components.append(f"Director: {director}")
        if cast and cast != "Unknown Cast":
            components.append(f"Starring: {cast}")
        if country and country != "Global / International":
            components.append(f"Country: {country}")
        if description:
            components.append(f"Overview: {description}")

        return " | ".join(components)

    def _fallback_hash_embedding(self, text_input: str) -> np.ndarray:
        """
        Deterministic high-dimensional semantic feature projection.
        Maps text tokens to 384 dimensions with sub-word n-gram hashing and L2 normalization.
        Ensures consistent cosine similarity behavior during offline testing.
        """
        tokens = re.findall(r"\w+", text_input.lower())
        vec = np.zeros(self.dimension, dtype=np.float32)

        if not tokens:
            vec[0] = 1.0
            return vec

        for idx, token in enumerate(tokens):
            # Token hash
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            dim_idx = h % self.dimension
            sign = 1.0 if (h >> 8) % 2 == 0 else -1.0
            weight = 1.0 / (1.0 + np.log1p(idx))
            vec[dim_idx] += sign * weight

            # Bi-gram hashing for local context
            if idx > 0:
                bigram = f"{tokens[idx-1]}_{token}"
                bh = int(hashlib.sha256(bigram.encode("utf-8")).hexdigest(), 16)
                b_dim = bh % self.dimension
                b_sign = 1.0 if (bh >> 8) % 2 == 0 else -1.0
                vec[b_dim] += b_sign * 0.5 * weight

        # L2 normalize to unit length
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        else:
            vec[0] = 1.0
        return vec

    def encode(self, texts: Union[str, List[str]], batch_size: int = 64) -> np.ndarray:
        """
        Encode single text or list of texts into normalized 384-dim numpy array.
        """
        single_input = isinstance(texts, str)
        text_list = [texts] if single_input else texts

        if self.model is not None:
            try:
                embeddings = self.model.encode(
                    text_list,
                    batch_size=batch_size,
                    show_progress_bar=False,
                    normalize_embeddings=True
                )
                embeddings = np.array(embeddings, dtype=np.float32)
                return embeddings[0] if single_input else embeddings
            except Exception as e:
                logger.warning(f"Inference error in SentenceTransformer ({e}). Falling back to hash projection.")

        # Fallback projection
        embeddings_list = [self._fallback_hash_embedding(t) for t in text_list]
        embeddings = np.array(embeddings_list, dtype=np.float32)
        return embeddings[0] if single_input else embeddings

    def index_catalog_embeddings(self, titles_df: pd.DataFrame, engine: Engine, batch_size: int = 100) -> int:
        """
        Generate dense embeddings for all titles and upsert into title_embeddings table.
        """
        logger.info(f"Generating and indexing embeddings for {len(titles_df)} titles...")
        records = titles_df.to_dict(orient="records")
        texts_to_encode = [self.build_text_representation(r) for r in records]
        
        vectors = self.encode(texts_to_encode, batch_size=batch_size)
        is_postgres = "postgresql" in str(engine.url)

        total_indexed = 0
        with engine.begin() as conn:
            for i in range(0, len(records), batch_size):
                batch_records = records[i:i + batch_size]
                batch_vectors = vectors[i:i + batch_size]

                insert_payload = []
                for r, v in zip(batch_records, batch_vectors):
                    v_list = v.tolist()
                    insert_payload.append({
                        "show_id": str(r["show_id"]),
                        "embedding": str(v_list) if is_postgres else json.dumps(v_list),
                        "model_version": self.model_name
                    })

                if is_postgres:
                    upsert_sql = text("""
                        INSERT INTO title_embeddings (show_id, embedding, model_version)
                        VALUES (:show_id, :embedding::vector, :model_version)
                        ON CONFLICT (show_id) DO UPDATE SET
                            embedding = EXCLUDED.embedding,
                            model_version = EXCLUDED.model_version,
                            updated_at = CURRENT_TIMESTAMP;
                    """)
                    conn.execute(upsert_sql, insert_payload)
                else:
                    # SQLite Replace
                    sqlite_sql = text("""
                        INSERT OR REPLACE INTO title_embeddings (show_id, embedding, model_version)
                        VALUES (:show_id, :embedding, :model_version);
                    """)
                    conn.execute(sqlite_sql, insert_payload)

                total_indexed += len(batch_records)

        logger.info(f"Successfully indexed {total_indexed} title embeddings in database.")
        return total_indexed

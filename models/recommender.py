"""
Netflix Streaming Intelligence Platform - Hybrid Personalization Engine
Combines semantic vector embeddings (pgvector cosine similarity) with metadata boosting
(Jaccard genre/cast overlap, director matching) and explicit dual-mode cold-start mitigation.
"""

import json
import math
import logging
from typing import List, Dict, Any, Optional, Set
import numpy as np
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine
from models.embedder import ContentEmbedder

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Recommender")


class HybridRecommender:
    """
    Production-grade hybrid recommendation system featuring:
    1. Semantic Vector Search via pgvector / Cosine Distance
    2. User History Preference Vector Aggregation with Temporal & Telemetry Weighting
    3. Metadata Similarity Boosting (Genres Jaccard, Director Equality, Cast Overlap)
    4. Explicit Cold-Start Handler for new users & new items
    """

    def __init__(
        self,
        engine: Engine,
        embedder: Optional[ContentEmbedder] = None,
        weight_semantic: float = 0.40,
        weight_genre: float = 0.30,
        weight_director: float = 0.15,
        weight_cast: float = 0.15
    ):
        self.engine = engine
        self.embedder = embedder or ContentEmbedder()
        self.w_sem = weight_semantic
        self.w_genre = weight_genre
        self.w_dir = weight_director
        self.w_cast = weight_cast

    # ----------------------------------------------------------------------
    # Helper Utilities
    # ----------------------------------------------------------------------
    @staticmethod
    def _parse_set(val: Optional[str]) -> Set[str]:
        """Parse comma-separated or pipe-separated values into a lowercase set."""
        if not val or val.lower() in ("unknown", "none", "nan", "unknown cast", "unknown director"):
            return set()
        return {item.strip().lower() for item in val.replace("|", ",").split(",") if item.strip()}

    @staticmethod
    def _jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
        """
        Calculate Jaccard similarity coefficient between two sets.
        
        Mathematical Formulation:
            J(A, B) = |A ∩ B| / |A ∪ B|
            
        Where:
            |A ∩ B|: Intersection cardinality (count of shared categorical tokens)
            |A ∪ B|: Union cardinality (count of distinct categorical tokens across both)
            Bounded in [0.0, 1.0], where 1.0 denotes identical categorical metadata.
        """
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return float(intersection / union) if union > 0 else 0.0

    @staticmethod
    def _cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """
        Calculate cosine similarity between two dense semantic embedding vectors.
        
        Mathematical Formulation:
            cos(θ) = (A · B) / (||A||_2 * ||B||_2)
            
        Where:
            (A · B): Inner dot product of 384-dimensional dense vectors
            ||A||_2, ||B||_2: L2 Euclidean norms
            Cosine distance metric for pgvector HNSW indexing: D_cos = 1 - cos(θ)
        """
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))

    def _fetch_all_titles(self) -> pd.DataFrame:
        """Fetch all titles with their embeddings from database."""
        query = """
            SELECT 
                t.show_id, t.type, t.title, t.director, t.cast_members,
                t.country, t.date_added, t.release_year, t.rating,
                t.duration, t.listed_in, t.description,
                te.embedding
            FROM titles t
            LEFT JOIN title_embeddings te ON t.show_id = te.show_id;
        """
        with self.engine.connect() as conn:
            df = pd.read_sql(text(query), conn)

        # Parse vector column if stored as JSON / string
        def parse_vec(val):
            if val is None:
                return np.zeros(self.embedder.dimension, dtype=np.float32)
            if isinstance(val, (list, np.ndarray)):
                return np.array(val, dtype=np.float32)
            if isinstance(val, str):
                try:
                    cleaned = val.strip("[]")
                    return np.array([float(x.strip()) for x in cleaned.split(",") if x.strip()], dtype=np.float32)
                except Exception:
                    return np.zeros(self.embedder.dimension, dtype=np.float32)
            return np.zeros(self.embedder.dimension, dtype=np.float32)

        df["vector"] = df["embedding"].apply(parse_vec)
        return df

    # ----------------------------------------------------------------------
    # 1. Semantic Natural Language Search
    # ----------------------------------------------------------------------
    def get_semantic_recommendations(
        self,
        query: str,
        top_k: int = 10,
        type_filter: Optional[str] = None,
        min_year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute semantic vector search against catalog descriptions and tags.
        Utilizes pgvector cosine distance operator (<=>) in PostgreSQL or in-memory dot product.
        """
        query_vector = self.embedder.encode(query)
        is_postgres = "postgresql" in str(self.engine.url)

        if is_postgres:
            try:
                filters = []
                params = {
                    "qvec": str(query_vector.tolist()),
                    "top_k": top_k
                }
                if type_filter:
                    filters.append("t.type = :type_filter")
                    params["type_filter"] = type_filter
                if min_year:
                    filters.append("t.release_year >= :min_year")
                    params["min_year"] = min_year

                where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
                sql = f"""
                    SELECT 
                        t.show_id, t.type, t.title, t.director, t.cast_members,
                        t.country, t.release_year, t.rating, t.duration,
                        t.listed_in, t.description,
                        1 - (te.embedding <=> :qvec::vector) AS similarity
                    FROM title_embeddings te
                    JOIN titles t ON te.show_id = t.show_id
                    {where_clause}
                    ORDER BY te.embedding <=> :qvec::vector ASC
                    LIMIT :top_k;
                """
                with self.engine.connect() as conn:
                    result = conn.execute(text(sql), params).mappings().all()

                recommendations = []
                for row in result:
                    rec = dict(row)
                    rec["score"] = round(float(rec["similarity"]), 4)
                    rec["match_reason"] = f"Semantic description similarity ({rec['score']:.2f}) to query: '{query}'"
                    recommendations.append(rec)
                return recommendations
            except Exception as e:
                logger.warning(f"PostgreSQL pgvector query error ({e}). Falling back to in-memory cosine search.")

        # In-Memory / SQLite Fallback
        df = self._fetch_all_titles()
        if df.empty:
            return []

        if type_filter:
            df = df[df["type"].str.lower() == type_filter.lower()]
        if min_year:
            df = df[df["release_year"] >= min_year]

        if df.empty:
            return []

        scores = [self._cosine_similarity(query_vector, v) for v in df["vector"]]
        df["similarity"] = scores
        df.sort_values(by="similarity", ascending=False, inplace=True)
        top_df = df.head(top_k)

        recommendations = []
        for _, row in top_df.iterrows():
            sim = float(row["similarity"])
            recommendations.append({
                "show_id": row["show_id"],
                "type": row["type"],
                "title": row["title"],
                "director": row["director"],
                "cast_members": row["cast_members"],
                "country": row["country"],
                "release_year": int(row["release_year"]),
                "rating": row["rating"],
                "duration": row["duration"],
                "listed_in": row["listed_in"],
                "description": row["description"],
                "score": round(sim, 4),
                "match_reason": f"Semantic content similarity ({sim:.2f}) to query: '{query}'"
            })
        return recommendations

    # ----------------------------------------------------------------------
    # 2. Personalized Hybrid Recommendation with Cold-Start Handling
    # ----------------------------------------------------------------------
    def get_user_recommendations(
        self,
        user_id: str,
        top_k: int = 10,
        include_history: bool = False
    ) -> Dict[str, Any]:
        """
        Generate personalized recommendations for a specific user profile.
        Incorporates user watch history, telemetry weighting, metadata affinity, and cold-start fallback.
        """
        # Fetch user watch history
        history_query = text("""
            SELECT 
                ui.show_id, ui.interaction_type, ui.watch_duration_pct, ui.timestamp,
                t.title, t.listed_in, t.director, t.cast_members, t.type,
                te.embedding
            FROM user_interactions ui
            JOIN titles t ON ui.show_id = t.show_id
            LEFT JOIN title_embeddings te ON t.show_id = te.show_id
            WHERE ui.user_id = :user_id
            ORDER BY ui.timestamp DESC;
        """)

        with self.engine.connect() as conn:
            history_rows = conn.execute(history_query, {"user_id": user_id}).mappings().all()

        # ==================================================================
        # CASE A: USER COLD START (No interactions recorded)
        # ==================================================================
        if not history_rows:
            logger.info(f"User '{user_id}' has no interaction history. Invoking Cold Start Strategy.")
            return self._get_cold_start_recommendations(top_k=top_k)

        # ==================================================================
        # CASE B: WARM USER PERSONALIZATION (Hybrid Aggregation)
        # ==================================================================
        all_titles_df = self._fetch_all_titles()
        if all_titles_df.empty:
            return {"user_id": user_id, "strategy": "empty_catalog", "recommendations": []}

        # 1. Compute user profile preference vector & metadata affinity sets
        user_vector = np.zeros(self.embedder.dimension, dtype=np.float32)
        total_weight = 0.0

        user_genres: Set[str] = set()
        user_directors: Set[str] = set()
        user_cast: Set[str] = set()
        consumed_show_ids: Set[str] = set()

        type_weights = {"like": 2.5, "save": 2.0, "watch": 1.0, "skip": 0.1}

        for h in history_rows:
            show_id = str(h["show_id"])
            consumed_show_ids.add(show_id)

            itype = str(h["interaction_type"]).lower()
            base_w = type_weights.get(itype, 1.0)
            completion_multiplier = 0.5 + 0.5 * (float(h["watch_duration_pct"]) / 100.0)
            weight = base_w * completion_multiplier

            # Vector aggregation
            emb = h.get("embedding")
            if emb is not None:
                if isinstance(emb, str):
                    try:
                        v = np.array([float(x.strip()) for x in emb.strip("[]").split(",") if x.strip()], dtype=np.float32)
                    except Exception:
                        v = np.zeros(self.embedder.dimension, dtype=np.float32)
                elif isinstance(emb, (list, np.ndarray)):
                    v = np.array(emb, dtype=np.float32)
                else:
                    v = np.zeros(self.embedder.dimension, dtype=np.float32)

                if np.linalg.norm(v) > 0:
                    user_vector += v * weight
                    total_weight += weight

            # Collect metadata affinities
            user_genres.update(self._parse_set(h["listed_in"]))
            user_directors.update(self._parse_set(h["director"]))
            user_cast.update(self._parse_set(h["cast_members"]))

        # Normalize user preference vector
        if total_weight > 0 and np.linalg.norm(user_vector) > 0:
            user_vector /= np.linalg.norm(user_vector)
        else:
            user_vector = np.zeros(self.embedder.dimension, dtype=np.float32)

        # 2. Score candidate titles
        candidates = all_titles_df.copy()
        if not include_history:
            candidates = candidates[~candidates["show_id"].isin(consumed_show_ids)]

        if candidates.empty:
            candidates = all_titles_df.copy()

        scored_candidates: List[Dict[str, Any]] = []

        for _, row in candidates.iterrows():
            cand_vec = row["vector"]
            cand_genres = self._parse_set(row["listed_in"])
            cand_director = self._parse_set(row["director"])
            cand_cast = self._parse_set(row["cast_members"])

            # Component 1: Semantic Embedding Cosine Score
            sem_score = self._cosine_similarity(user_vector, cand_vec) if np.linalg.norm(user_vector) > 0 else 0.5

            # Component 2: Genre Jaccard Overlap
            genre_score = self._jaccard_similarity(user_genres, cand_genres)

            # Component 3: Director Matching Bonus
            dir_score = 1.0 if bool(cand_director & user_directors) else 0.0

            # Component 4: Cast Jaccard Overlap
            cast_score = self._jaccard_similarity(user_cast, cand_cast)

            # Weighted Hybrid Fusion
            hybrid_score = (
                self.w_sem * sem_score +
                self.w_genre * genre_score +
                self.w_dir * dir_score +
                self.w_cast * cast_score
            )

            # Build transparent match rationale
            reasons = []
            if sem_score > 0.60:
                reasons.append(f"Semantic match ({sem_score:.2f})")
            matched_genres = list(cand_genres & user_genres)
            if matched_genres:
                reasons.append(f"Genre affinity: {', '.join(matched_genres[:2])}")
            if dir_score > 0:
                reasons.append(f"Favorite director: {row['director']}")
            matched_actors = list(cand_cast & user_cast)
            if matched_actors:
                reasons.append(f"Favorite cast: {', '.join(matched_actors[:2])}")

            rationale = " + ".join(reasons) if reasons else "High catalog affinity match"

            scored_candidates.append({
                "show_id": row["show_id"],
                "type": row["type"],
                "title": row["title"],
                "director": row["director"],
                "cast_members": row["cast_members"],
                "country": row["country"],
                "release_year": int(row["release_year"]),
                "rating": row["rating"],
                "duration": row["duration"],
                "listed_in": row["listed_in"],
                "description": row["description"],
                "score": round(float(hybrid_score), 4),
                "score_breakdown": {
                    "semantic_score": round(float(sem_score), 3),
                    "genre_score": round(float(genre_score), 3),
                    "director_score": round(float(dir_score), 3),
                    "cast_score": round(float(cast_score), 3),
                },
                "match_reason": rationale
            })

        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        top_recommendations = scored_candidates[:top_k]

        return {
            "user_id": user_id,
            "strategy": "hybrid_personalization_v1",
            "user_consumed_count": len(consumed_show_ids),
            "recommendations": top_recommendations
        }

    # ----------------------------------------------------------------------
    # 3. Explicit Cold-Start Handler (New User / Popularity & Diversity)
    # ----------------------------------------------------------------------
    def _get_cold_start_recommendations(self, top_k: int = 10) -> Dict[str, Any]:
        """
        Cold-start fallback strategy for newly registered users.
        Returns a diversified set of top-engagement, recent tentpole titles across distinct genres.
        """
        cold_query = text("""
            SELECT 
                t.show_id, t.type, t.title, t.director, t.cast_members,
                t.country, t.release_year, t.rating, t.duration,
                t.listed_in, t.description,
                COALESCE(COUNT(ui.interaction_id), 0) AS engagement_count,
                COALESCE(AVG(ui.watch_duration_pct), 85.0) AS avg_completion
            FROM titles t
            LEFT JOIN user_interactions ui ON t.show_id = ui.show_id
            GROUP BY t.show_id, t.type, t.title, t.director, t.cast_members,
                     t.country, t.release_year, t.rating, t.duration,
                     t.listed_in, t.description
            ORDER BY engagement_count DESC, t.release_year DESC, avg_completion DESC
            LIMIT :limit;
        """)

        with self.engine.connect() as conn:
            rows = conn.execute(cold_query, {"limit": max(top_k * 3, 30)}).mappings().all()

        # Genre-diversity sampling to prevent monogenre recommendations
        seen_primary_genres = set()
        diversified_recs = []

        for r in rows:
            primary_genre = r["listed_in"].split(",")[0].strip()
            # Try to balance genres in top recommendations
            if primary_genre not in seen_primary_genres or len(diversified_recs) >= top_k:
                seen_primary_genres.add(primary_genre)
                item = dict(r)
                item["score"] = round(float(0.95 - len(diversified_recs) * 0.03), 4)
                item["score_breakdown"] = {
                    "popularity_rank": len(diversified_recs) + 1,
                    "avg_completion": float(r["avg_completion"]),
                    "strategy": "cold_start_popularity_diversity"
                }
                item["match_reason"] = f"Global Top Trending ({primary_genre}) - High Audience Engagement"
                diversified_recs.append(item)
                if len(diversified_recs) == top_k:
                    break

        # If diversity check is too strict, fill remaining slots
        if len(diversified_recs) < top_k:
            for r in rows:
                if not any(d["show_id"] == r["show_id"] for d in diversified_recs):
                    item = dict(r)
                    item["score"] = round(float(0.80 - len(diversified_recs) * 0.02), 4)
                    item["match_reason"] = "Global Popular Selection"
                    diversified_recs.append(item)
                    if len(diversified_recs) == top_k:
                        break

        return {
            "user_id": "new_user",
            "strategy": "cold_start_popularity_diversity",
            "user_consumed_count": 0,
            "recommendations": diversified_recs
        }

    # ----------------------------------------------------------------------
    # 4. Item-to-Item Recommendations (Content Page & Item Cold Start)
    # ----------------------------------------------------------------------
    def get_item_recommendations(self, show_id: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Generate similar item recommendations for a given title.
        Mitigates item cold start by relying purely on dense semantic content vectors and metadata.
        """
        df = self._fetch_all_titles()
        if df.empty or show_id not in df["show_id"].values:
            return []

        target_row = df[df["show_id"] == show_id].iloc[0]
        target_vec = target_row["vector"]
        target_genres = self._parse_set(target_row["listed_in"])
        target_director = self._parse_set(target_row["director"])

        candidates = df[df["show_id"] != show_id].copy()
        scored = []

        for _, row in candidates.iterrows():
            cand_vec = row["vector"]
            cand_genres = self._parse_set(row["listed_in"])
            cand_director = self._parse_set(row["director"])

            sem_score = self._cosine_similarity(target_vec, cand_vec)
            genre_score = self._jaccard_similarity(target_genres, cand_genres)
            dir_score = 1.0 if bool(target_director & cand_director) else 0.0

            score = 0.50 * sem_score + 0.35 * genre_score + 0.15 * dir_score

            scored.append({
                "show_id": row["show_id"],
                "type": row["type"],
                "title": row["title"],
                "director": row["director"],
                "cast_members": row["cast_members"],
                "country": row["country"],
                "release_year": int(row["release_year"]),
                "rating": row["rating"],
                "duration": row["duration"],
                "listed_in": row["listed_in"],
                "description": row["description"],
                "score": round(float(score), 4),
                "match_reason": f"Content & thematic similarity to '{target_row['title']}' ({score:.2f})"
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

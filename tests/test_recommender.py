"""
Unit tests for Dense Embedder, Hybrid Recommendation Algorithm, and Cold-Start Mitigation.
"""

import pytest
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from models.embedder import ContentEmbedder
from models.recommender import HybridRecommender
from pipeline.etl import NetflixETLPipeline


@pytest.fixture
def mock_engine():
    """In-memory SQLite engine seeded with sample catalog and interactions."""
    engine = create_engine("sqlite:///:memory:")
    etl = NetflixETLPipeline(db_url="sqlite:///:memory:")
    etl.engine = engine
    etl.create_schema_tables()

    sample_titles = pd.DataFrame([
        {
            "show_id": "s1", "type": "TV Show", "title": "Stranger Things",
            "director": "The Duffer Brothers", "cast_members": "Millie Bobby Brown, Finn Wolfhard",
            "country": "United States", "date_added": "2022-01-01", "release_year": 2022,
            "rating": "TV-14", "duration": "4 Seasons", "listed_in": "Sci-Fi & Fantasy, TV Dramas",
            "description": "Supernatural mystery in a small town with monster experiments."
        },
        {
            "show_id": "s2", "type": "Movie", "title": "Inception",
            "director": "Christopher Nolan", "cast_members": "Leonardo DiCaprio, Joseph Gordon-Levitt",
            "country": "United States", "date_added": "2020-01-01", "release_year": 2010,
            "rating": "PG-13", "duration": "148 min", "listed_in": "Action & Adventure, Sci-Fi",
            "description": "A thief steals corporate secrets through dream-sharing technology."
        },
        {
            "show_id": "s3", "type": "Movie", "title": "Interstellar",
            "director": "Christopher Nolan", "cast_members": "Matthew McConaughey, Anne Hathaway",
            "country": "United States", "date_added": "2020-01-01", "release_year": 2014,
            "rating": "PG-13", "duration": "169 min", "listed_in": "Sci-Fi & Fantasy, Dramas",
            "description": "Astronauts travel through a wormhole in search of a new home."
        },
        {
            "show_id": "s4", "type": "TV Show", "title": "The Crown",
            "director": "Peter Morgan", "cast_members": "Claire Foy, Olivia Colman",
            "country": "United Kingdom", "date_added": "2022-01-01", "release_year": 2023,
            "rating": "TV-MA", "duration": "6 Seasons", "listed_in": "Historical, TV Dramas",
            "description": "Political rivalries and romance of Queen Elizabeth II's reign."
        }
    ])

    sample_clean = etl.clean_titles(sample_titles)
    etl.load_titles_batch(sample_clean)

    # Seed embeddings
    embedder = ContentEmbedder()
    embedder.index_catalog_embeddings(sample_clean, engine=engine)

    # Seed User Interactions: user_01 watched s2 (Inception) with high completion and liked it
    user_interactions = pd.DataFrame([
        {
            "user_id": "user_01",
            "show_id": "s2",
            "interaction_type": "like",
            "watch_duration_pct": 98.0,
            "timestamp": "2024-01-01T12:00:00"
        }
    ])
    etl.load_interactions_batch(user_interactions)

    return engine


def test_embedder_dimension_and_norm():
    """Verify embedder outputs 384-dimensional unit-length L2-normalized vectors."""
    embedder = ContentEmbedder()
    vec = embedder.encode("A dark psychological sci-fi thriller about space time travel")
    assert isinstance(vec, np.ndarray)
    assert vec.shape == (384,)
    assert np.isclose(np.linalg.norm(vec), 1.0, atol=1e-3)

    # Batch test
    batch_vecs = embedder.encode(["Docuseries about nature", "Comedy stand up show"])
    assert batch_vecs.shape == (2, 384)
    assert np.isclose(np.linalg.norm(batch_vecs[0]), 1.0, atol=1e-3)
    assert np.isclose(np.linalg.norm(batch_vecs[1]), 1.0, atol=1e-3)


def test_semantic_recommendation_ranking(mock_engine):
    """Verify natural language semantic query ranks conceptually aligned titles top."""
    embedder = ContentEmbedder()
    recommender = HybridRecommender(engine=mock_engine, embedder=embedder)

    # Query for space travel
    results = recommender.get_semantic_recommendations("astronaut space travel wormhole", top_k=2)
    assert len(results) > 0
    top_title = results[0]["title"]
    assert top_title in ["Interstellar", "Inception", "Stranger Things"]


def test_personalized_hybrid_recommendation_and_metadata_boost(mock_engine):
    """Verify warm user personalization recommends Nolan/Sci-Fi (Interstellar) after liking Inception."""
    embedder = ContentEmbedder()
    recommender = HybridRecommender(engine=mock_engine, embedder=embedder)

    # user_01 liked Inception (Nolan, Sci-Fi)
    res = recommender.get_user_recommendations(user_id="user_01", top_k=2, include_history=False)
    assert res["user_id"] == "user_01"
    assert res["strategy"] == "hybrid_personalization_v1"
    assert len(res["recommendations"]) > 0
    
    # Interstellar shares director (Christopher Nolan) and Sci-Fi genre -> should rank #1
    top_rec = res["recommendations"][0]
    assert top_rec["show_id"] == "s3"  # Interstellar
    assert "score_breakdown" in top_rec
    assert top_rec["score_breakdown"]["director_score"] == 1.0


def test_cold_start_new_user_fallback(mock_engine):
    """Verify cold-start strategy is cleanly invoked for a brand new user with 0 history."""
    embedder = ContentEmbedder()
    recommender = HybridRecommender(engine=mock_engine, embedder=embedder)

    res = recommender.get_user_recommendations(user_id="brand_new_user_999", top_k=2)
    assert res["strategy"] == "cold_start_popularity_diversity"
    assert res["user_consumed_count"] == 0
    assert len(res["recommendations"]) == 2
    assert "match_reason" in res["recommendations"][0]

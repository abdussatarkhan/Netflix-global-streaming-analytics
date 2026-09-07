"""
Unit tests for ETL Pipeline, Data Cleansing, Normalization, and Telemetry Generation.
"""

import datetime
import pandas as pd
import numpy as np
import pytest
from pipeline.etl import NetflixETLPipeline
from data.generate_interactions import generate_synthetic_interactions


@pytest.fixture
def sample_raw_dataframe():
    """Generate a mock raw DataFrame with noisy data to test cleansing."""
    return pd.DataFrame([
        {
            "show_id": "s1",
            "type": "TV Show",
            "title": " Stranger Things ",
            "director": None,
            "cast": "Millie Bobby Brown, Finn Wolfhard",
            "country": "United States",
            "date_added": "July 15, 2016",
            "release_year": "2022",
            "rating": "TV-14",
            "duration": "4 Seasons",
            "listed_in": "Sci-Fi & Fantasy, TV Dramas",
            "description": "A boy vanishes in a small town."
        },
        {
            "show_id": "s2",
            "type": "Movie",
            "title": "Inception",
            "director": "Christopher Nolan",
            "cast": None,
            "country": None,
            "date_added": "2020-01-01",
            "release_year": "invalid_year",
            "rating": None,
            "duration": "148 min",
            "listed_in": "Action & Adventure, Sci-Fi",
            "description": None
        },
        {
            "show_id": "s1",  # Duplicate show_id
            "type": "TV Show",
            "title": "Stranger Things Updated",
            "director": "The Duffer Brothers",
            "cast": "Millie Bobby Brown",
            "country": "United States",
            "date_added": "2022-05-27",
            "release_year": 2022,
            "rating": "TV-14",
            "duration": "4 Seasons",
            "listed_in": "Sci-Fi & Fantasy",
            "description": "Supernatural forces."
        }
    ])


def test_date_parser():
    """Verify robust parsing across multiple date string formats."""
    assert NetflixETLPipeline.parse_date("July 15, 2016") == datetime.date(2016, 7, 15)
    assert NetflixETLPipeline.parse_date("2020-01-01") == datetime.date(2020, 1, 1)
    assert NetflixETLPipeline.parse_date("Dec 23, 2022") == datetime.date(2022, 12, 23)
    assert NetflixETLPipeline.parse_date("invalid_string 2024") == datetime.date(2024, 1, 1)
    assert NetflixETLPipeline.parse_date(None) is None
    assert NetflixETLPipeline.parse_date(np.nan) is None


def test_clean_titles_deduplication_and_imputation(sample_raw_dataframe):
    """Verify deduplication, missing value imputation, and type safety in clean_titles."""
    etl = NetflixETLPipeline(db_url="sqlite:///:memory:")
    clean_df = etl.clean_titles(sample_raw_dataframe)

    # 1. Deduplication (s1 was duplicated)
    assert len(clean_df) == 2
    assert set(clean_df["show_id"]) == {"s1", "s2"}

    # 2. Check s1 updated record retained
    s1_row = clean_df[clean_df["show_id"] == "s1"].iloc[0]
    assert s1_row["director"] == "The Duffer Brothers"

    # 3. Check s2 imputations
    s2_row = clean_df[clean_df["show_id"] == "s2"].iloc[0]
    assert s2_row["director"] == "Christopher Nolan"
    assert s2_row["cast_members"] == "Unknown Cast"
    assert s2_row["country"] == "Global / International"
    assert s2_row["rating"] == "TV-MA"
    assert s2_row["description"] == "No description available."
    assert s2_row["release_year"] == 2022  # Handled invalid_year fallback
    assert isinstance(s2_row["date_added"], datetime.date)


def test_generate_synthetic_interactions(sample_raw_dataframe):
    """Verify generation of synthetic telemetry logs adhering to schemas and constraints."""
    etl = NetflixETLPipeline(db_url="sqlite:///:memory:")
    clean_df = etl.clean_titles(sample_raw_dataframe)

    interactions_df = generate_synthetic_interactions(
        titles_df=clean_df,
        num_users=10,
        min_interactions_per_user=2,
        max_interactions_per_user=5
    )

    assert not interactions_df.empty
    assert "user_id" in interactions_df.columns
    assert "show_id" in interactions_df.columns
    assert "interaction_type" in interactions_df.columns
    assert "watch_duration_pct" in interactions_df.columns
    assert "timestamp" in interactions_df.columns

    # Verify constraints
    assert interactions_df["watch_duration_pct"].min() >= 0.0
    assert interactions_df["watch_duration_pct"].max() <= 100.0
    valid_types = {"watch", "like", "save", "skip"}
    assert set(interactions_df["interaction_type"].unique()).issubset(valid_types)
    assert set(interactions_df["show_id"].unique()).issubset(set(clean_df["show_id"]))

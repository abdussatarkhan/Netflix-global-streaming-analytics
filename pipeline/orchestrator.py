"""
Netflix Platform - End-to-End Orchestrator
Coordinates ETL ingestion, embedding generation, index construction, and health verification.
"""

import os
import sys
import time
import logging
from pipeline.etl import NetflixETLPipeline
from models.embedder import ContentEmbedder
from models.recommender import HybridRecommender

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Orchestrator")


def orchestrate_pipeline():
    """Run end-to-end data pipeline & ML indexing workflow."""
    start_time = time.time()
    logger.info("====================================================================")
    logger.info("STARTING STREAMING INTELLIGENCE & PERSONALIZATION PLATFORM PIPELINE")
    logger.info("====================================================================")

    # 1. ETL Pipeline
    raw_csv = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw", "netflix_titles.csv")
    if not os.path.exists(raw_csv):
        logger.error(f"Raw catalog not found at {raw_csv}")
        sys.exit(1)

    etl = NetflixETLPipeline()
    clean_titles_df, interactions_df = etl.run_pipeline(raw_csv, num_synthetic_users=150)
    logger.info(f"ETL Complete: {len(clean_titles_df)} titles & {len(interactions_df)} interactions ingested.")

    # 2. Embedding Generation & Indexing
    logger.info("Step 2: Generating dense vector embeddings for catalog...")
    embedder = ContentEmbedder()
    embeddings_count = embedder.index_catalog_embeddings(clean_titles_df, engine=etl.engine)
    logger.info(f"Embedding Indexing Complete: {embeddings_count} vectors indexed.")

    # 3. Model & Personalization Verification
    logger.info("Step 3: Verifying Hybrid Recommendation Engine...")
    recommender = HybridRecommender(engine=etl.engine, embedder=embedder)
    
    # Test Semantic Search
    test_query = "mind-bending sci-fi thriller about alternate realities"
    semantic_results = recommender.get_semantic_recommendations(query=test_query, top_k=3)
    logger.info(f"Test Semantic Search for '{test_query}':")
    for r in semantic_results:
        logger.info(f"  -> [{r['score']:.3f}] {r['title']} ({r['release_year']}) - {r['listed_in']}")

    # Test Cold Start User Recommendation
    cold_user_results = recommender.get_user_recommendations(user_id="user_non_existent", top_k=3)
    logger.info(f"Test Cold Start Fallback for new user (Strategy: {cold_user_results['strategy']}):")
    for r in cold_user_results["recommendations"]:
        logger.info(f"  -> [{r['score']:.3f}] {r['title']} ({r['release_year']}) - {r['match_reason']}")

    elapsed = time.time() - start_time
    logger.info(f"End-to-End Orchestration completed successfully in {elapsed:.2f} seconds.")
    logger.info("====================================================================")


if __name__ == "__main__":
    orchestrate_pipeline()

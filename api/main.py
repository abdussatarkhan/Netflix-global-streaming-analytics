"""
Netflix Streaming Intelligence & Personalization Platform - FastAPI Application
Exposes REST endpoints for health, aggregated analytics, semantic vector search,
hybrid personalized recommendations, and telemetry clickstream ingestion.
"""

import os
import datetime
import logging
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from api.database import get_db, engine, check_db_health
from api.schemas import (
    SemanticSearchRequest, SemanticSearchResponse,
    UserRecommendationResponse, InteractionEvent, BatchInteractionRequest,
    InteractionResponse, AnalyticsSummaryResponse, HealthCheckResponse,
    RecommendationItem
)
from models.embedder import ContentEmbedder
from models.recommender import HybridRecommender

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("API")

embedder: Optional[ContentEmbedder] = None
recommender: Optional[HybridRecommender] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global embedder, recommender
    logger.info("Initializing Netflix Platform ML Engine and Services...")
    
    from pipeline.etl import NetflixETLPipeline
    etl = NetflixETLPipeline(db_url=str(engine.url))
    etl.create_schema_tables()
    
    with engine.connect() as conn:
        try:
            count = conn.execute(text("SELECT COUNT(*) FROM titles")).scalar() or 0
        except Exception:
            count = 0
            
    if count == 0:
        logger.info("Database empty. Seeding initial catalog dataset...")
        raw_csv = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw", "netflix_titles.csv")
        if os.path.exists(raw_csv):
            etl.run_pipeline(raw_csv, num_synthetic_users=100)

    embedder = ContentEmbedder()
    recommender = HybridRecommender(engine=engine, embedder=embedder)
    
    with engine.connect() as conn:
        try:
            emb_count = conn.execute(text("SELECT COUNT(*) FROM title_embeddings")).scalar() or 0
        except Exception:
            emb_count = 0
            
    if emb_count == 0:
        logger.info("Indexing embeddings for titles...")
        import pandas as pd
        with engine.connect() as conn:
            titles_df = pd.read_sql(text("SELECT * FROM titles"), conn)
        if not titles_df.empty:
            embedder.index_catalog_embeddings(titles_df, engine=engine)

    logger.info("Application startup complete. Ready for requests.")
    yield
    logger.info("Shutting down Netflix Platform API...")


app = FastAPI(
    title="Netflix Streaming Intelligence & Personalization Platform",
    description="""
    Production-grade, 4-Tier Data Platform and Intelligent Recommendation Engine.
    
    ### Key Features:
    * **Data Engineering & ETL:** Automated catalog cleansing, normalization, and relational modeling.
    * **Vector Search with pgvector:** Sub-millisecond approximate semantic nearest neighbor search via dense sentence embeddings.
    * **Hybrid Personalization:** Fused scoring combining semantic preference vectors, genre Jaccard similarity, director matching, and cast affinity.
    * **Cold-Start Mitigation:** Explicit dual-mode fallbacks for new users (diversity + popularity) and new catalog titles (content semantic clustering).
    * **Streaming Telemetry:** Real-time clickstream event ingestion for continuous online personalization.
    """,
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["Diagnostics"],
    summary="System and Database Connection Health"
)
def get_system_health():
    db_status = check_db_health(engine)
    return HealthCheckResponse(
        status="operational" if db_status["status"] == "healthy" else "degraded",
        service="Netflix Streaming Intelligence API",
        database=db_status,
        embedder_model=embedder.model_name if embedder else "uninitialized",
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    )


@app.get(
    "/analytics/summary",
    response_model=AnalyticsSummaryResponse,
    tags=["Analytics"],
    summary="Catalog Distribution & Telemetry Summary"
)
def get_analytics_summary(db: Session = Depends(get_db)):
    try:
        total_titles = db.execute(text("SELECT COUNT(*) FROM titles")).scalar() or 0
        total_interactions = db.execute(text("SELECT COUNT(*) FROM user_interactions")).scalar() or 0
        total_active_users = db.execute(text("SELECT COUNT(DISTINCT user_id) FROM user_interactions")).scalar() or 0
        avg_completion = db.execute(text("SELECT AVG(watch_duration_pct) FROM user_interactions")).scalar() or 0.0

        type_rows = db.execute(text("""
            SELECT type, COUNT(*) as cnt 
            FROM titles 
            GROUP BY type 
            ORDER BY cnt DESC
        """)).all()
        content_type_dist = [
            {
                "type": r[0],
                "count": r[1],
                "percentage": round((r[1] / total_titles * 100.0) if total_titles > 0 else 0.0, 2)
            }
            for r in type_rows
        ]

        country_rows = db.execute(text("""
            SELECT country, COUNT(*) as cnt 
            FROM titles 
            WHERE country IS NOT NULL AND country != 'Global / International'
            GROUP BY country 
            ORDER BY cnt DESC 
            LIMIT 10
        """)).all()
        top_countries = [{"country": r[0], "count": r[1]} for r in country_rows]

        genres_rows = db.execute(text("SELECT listed_in FROM titles")).all()
        genre_counter: Dict[str, int] = {}
        for r in genres_rows:
            if r[0]:
                for g in str(r[0]).split(","):
                    g_clean = g.strip()
                    if g_clean:
                        genre_counter[g_clean] = genre_counter.get(g_clean, 0) + 1

        sorted_genres = sorted(genre_counter.items(), key=lambda x: x[1], reverse=True)[:10]
        top_genres = [{"genre": g, "count": cnt} for g, cnt in sorted_genres]

        return AnalyticsSummaryResponse(
            total_titles=total_titles,
            total_interactions=total_interactions,
            total_active_users=total_active_users,
            avg_watch_completion_pct=round(float(avg_completion), 2),
            content_type_distribution=content_type_dist,
            top_countries=top_countries,
            top_genres=top_genres
        )
    except Exception as e:
        logger.error(f"Error computing analytics summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute analytics summary: {str(e)}"
        )


@app.post(
    "/recommendations/semantic",
    response_model=SemanticSearchResponse,
    tags=["Recommendations"],
    summary="Semantic Natural Language Content Search"
)
def search_semantic_recommendations(request: SemanticSearchRequest):
    if not recommender:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="ML Recommender is initializing.")

    try:
        results = recommender.get_semantic_recommendations(
            query=request.query,
            top_k=request.top_k,
            type_filter=request.type_filter,
            min_year=request.min_year
        )
        return SemanticSearchResponse(
            query=request.query,
            top_k=request.top_k,
            results_count=len(results),
            recommendations=results
        )
    except Exception as e:
        logger.error(f"Error during semantic vector search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic recommendation failed: {str(e)}"
        )


@app.get(
    "/recommendations/user/{user_id}",
    response_model=UserRecommendationResponse,
    tags=["Recommendations"],
    summary="Personalized Hybrid Recommendations for User"
)
def get_user_personalized_recommendations(
    user_id: str,
    top_k: int = Query(default=10, ge=1, le=50, description="Number of recommendations to return"),
    include_history: bool = Query(default=False, description="Whether to include already watched titles")
):
    if not recommender:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="ML Recommender is initializing.")

    try:
        result = recommender.get_user_recommendations(
            user_id=user_id,
            top_k=top_k,
            include_history=include_history
        )
        return UserRecommendationResponse(
            user_id=result["user_id"],
            strategy=result["strategy"],
            user_consumed_count=result["user_consumed_count"],
            recommendations_count=len(result["recommendations"]),
            recommendations=result["recommendations"]
        )
    except Exception as e:
        logger.error(f"Error generating personalized recommendations for user '{user_id}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Personalization engine error: {str(e)}"
        )


@app.post(
    "/pipeline/simulate-stream",
    response_model=InteractionResponse,
    tags=["Data Pipeline"],
    summary="Push Simulated Telemetry Clickstream Events"
)
def simulate_telemetry_stream(
    payload: BatchInteractionRequest,
    db: Session = Depends(get_db)
):
    if not payload.events:
        return InteractionResponse(
            status="noop",
            ingested_events=0,
            message="No interaction events provided in batch."
        )

    try:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        records_to_insert = []

        for evt in payload.events:
            records_to_insert.append({
                "user_id": evt.user_id,
                "show_id": evt.show_id,
                "interaction_type": evt.interaction_type,
                "watch_duration_pct": evt.watch_duration_pct,
                "timestamp": evt.timestamp or now
            })

        insert_stmt = text("""
            INSERT INTO user_interactions (
                user_id, show_id, interaction_type, watch_duration_pct, timestamp
            ) VALUES (
                :user_id, :show_id, :interaction_type, :watch_duration_pct, :timestamp
            );
        """)

        db.execute(insert_stmt, records_to_insert)
        db.commit()

        logger.info(f"Ingested {len(records_to_insert)} telemetry events into user_interactions.")
        return InteractionResponse(
            status="success",
            ingested_events=len(records_to_insert),
            message=f"Successfully ingested {len(records_to_insert)} clickstream events."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error ingesting telemetry events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Telemetry ingestion failed: {str(e)}"
        )

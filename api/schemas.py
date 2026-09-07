"""
Netflix Platform - Pydantic Request & Response Schemas
Type-safe input validation and response serialization.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
import datetime


# ----------------------------------------------------------------------
# 1. Title Catalog Schemas
# ----------------------------------------------------------------------
class TitleBase(BaseModel):
    show_id: str
    type: str = Field(..., examples=["TV Show"])
    title: str = Field(..., examples=["Stranger Things"])
    director: Optional[str] = None
    cast_members: Optional[str] = None
    country: Optional[str] = None
    release_year: int = Field(..., ge=1900, le=2100)
    rating: Optional[str] = "TV-MA"
    duration: Optional[str] = "4 Seasons"
    listed_in: str = Field(..., examples=["Sci-Fi & Fantasy, TV Dramas"])
    description: str


class TitleResponse(TitleBase):
    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------------------------
# 2. Recommendation Request & Response Schemas
# ----------------------------------------------------------------------
class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, examples=["dark psychological thriller set in Europe"])
    top_k: int = Field(default=10, ge=1, le=50, examples=[5])
    type_filter: Optional[str] = Field(default=None, examples=["Movie"])
    min_year: Optional[int] = Field(default=None, ge=1900, examples=[2015])


class RecommendationItem(BaseModel):
    show_id: str
    type: str
    title: str
    director: Optional[str] = None
    cast_members: Optional[str] = None
    country: Optional[str] = None
    release_year: int
    rating: Optional[str] = None
    duration: Optional[str] = None
    listed_in: str
    description: str
    score: float
    score_breakdown: Optional[Dict[str, Any]] = None
    match_reason: str


class SemanticSearchResponse(BaseModel):
    query: str
    top_k: int
    results_count: int
    recommendations: List[RecommendationItem]


class UserRecommendationResponse(BaseModel):
    user_id: str
    strategy: str
    user_consumed_count: int
    recommendations_count: int
    recommendations: List[RecommendationItem]


# ----------------------------------------------------------------------
# 3. Telemetry Stream Simulation Schemas
# ----------------------------------------------------------------------
class InteractionEvent(BaseModel):
    user_id: str = Field(..., min_length=2, examples=["user_0042"])
    show_id: str = Field(..., min_length=1, examples=["s1"])
    interaction_type: str = Field(..., pattern="^(watch|like|save|skip)$", examples=["watch"])
    watch_duration_pct: float = Field(..., ge=0.0, le=100.0, examples=[92.5])
    timestamp: Optional[str] = None


class BatchInteractionRequest(BaseModel):
    events: List[InteractionEvent]


class InteractionResponse(BaseModel):
    status: str
    ingested_events: int
    message: str


# ----------------------------------------------------------------------
# 4. Analytics Summary Schemas
# ----------------------------------------------------------------------
class ContentTypeCount(BaseModel):
    type: str
    count: int
    percentage: float


class CountryCount(BaseModel):
    country: str
    count: int


class GenreCount(BaseModel):
    genre: str
    count: int


class AnalyticsSummaryResponse(BaseModel):
    total_titles: int
    total_interactions: int
    total_active_users: int
    avg_watch_completion_pct: float
    content_type_distribution: List[ContentTypeCount]
    top_countries: List[CountryCount]
    top_genres: List[GenreCount]


# ----------------------------------------------------------------------
# 5. System Health Schema
# ----------------------------------------------------------------------
class HealthCheckResponse(BaseModel):
    status: str
    service: str
    database: Dict[str, Any]
    embedder_model: str
    timestamp: str
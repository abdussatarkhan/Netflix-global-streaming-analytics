-- ====================================================================
-- Netflix Streaming Intelligence & Personalization Platform Schema
-- PostgreSQL 16 + pgvector Extension DDL
-- ====================================================================

-- 1. Initialize Required Extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Teardown for Idempotent Setup
DROP VIEW IF EXISTS view_content_analytics_summary CASCADE;
DROP TABLE IF EXISTS user_interactions CASCADE;
DROP TABLE IF EXISTS title_embeddings CASCADE;
DROP TABLE IF EXISTS titles CASCADE;

-- 3. Core Catalog Table: titles
CREATE TABLE titles (
    show_id VARCHAR(32) PRIMARY KEY,
    type VARCHAR(32) NOT NULL DEFAULT 'Movie',
    title VARCHAR(512) NOT NULL,
    director TEXT,
    cast_members TEXT,
    country VARCHAR(256),
    date_added DATE,
    release_year INTEGER NOT NULL CHECK (release_year >= 1900 AND release_year <= 2100),
    rating VARCHAR(32) DEFAULT 'TV-MA',
    duration VARCHAR(64),
    listed_in TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- B-tree indexes for high-throughput filtering and analytical slicing
CREATE INDEX idx_titles_release_year ON titles (release_year);
CREATE INDEX idx_titles_type ON titles (type);
CREATE INDEX idx_titles_country ON titles (country);
CREATE INDEX idx_titles_rating ON titles (rating);

-- 4. Dense Vector Embeddings Table: title_embeddings
-- 384 dimensions matching sentence-transformers/all-MiniLM-L6-v2
CREATE TABLE title_embeddings (
    show_id VARCHAR(32) PRIMARY KEY REFERENCES titles(show_id) ON DELETE CASCADE,
    embedding vector(384) NOT NULL,
    model_version VARCHAR(64) NOT NULL DEFAULT 'all-MiniLM-L6-v2',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- HNSW Vector Index for sub-millisecond approximate nearest neighbor (ANN) cosine search
CREATE INDEX idx_title_embeddings_hnsw ON title_embeddings 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 5. User Telemetry & Clickstream Interactions: user_interactions
CREATE TABLE user_interactions (
    interaction_id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    show_id VARCHAR(32) NOT NULL REFERENCES titles(show_id) ON DELETE CASCADE,
    interaction_type VARCHAR(32) NOT NULL CHECK (interaction_type IN ('watch', 'like', 'save', 'skip')),
    watch_duration_pct NUMERIC(5, 2) NOT NULL CHECK (watch_duration_pct >= 0.00 AND watch_duration_pct <= 100.00),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Composite indexes for user-centric recommendation queries and telemetry aggregation
CREATE INDEX idx_user_interactions_user_time ON user_interactions (user_id, timestamp DESC);
CREATE INDEX idx_user_interactions_show ON user_interactions (show_id);
CREATE INDEX idx_user_interactions_type ON user_interactions (interaction_type);

-- 6. Analytical Summary Materialized View / Standard View
CREATE OR REPLACE VIEW view_content_analytics_summary AS
SELECT 
    t.type,
    COUNT(DISTINCT t.show_id) AS total_titles,
    ROUND(AVG(COALESCE(ui.watch_duration_pct, 0)), 2) AS avg_watch_completion,
    COUNT(DISTINCT ui.user_id) AS total_engaged_users
FROM titles t
LEFT JOIN user_interactions ui ON t.show_id = ui.show_id
GROUP BY t.type;

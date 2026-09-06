-- ==============================================================================
-- Netflix Global Streaming Performance Analytics (2021-2025)
-- File: sql/01_schema.sql
-- Star Schema Data Warehouse DDL for PostgreSQL 16
-- ==============================================================================

-- Clean up existing objects if rebuilding
DROP VIEW IF EXISTS vw_executive_monthly_kpi CASCADE;
DROP VIEW IF EXISTS vw_subscriber_growth_trajectory CASCADE;
DROP VIEW IF EXISTS vw_content_roi_quadrant CASCADE;
DROP VIEW IF EXISTS vw_regional_performance_matrix CASCADE;
DROP VIEW IF EXISTS vw_ad_tier_adoption_funnel CASCADE;
DROP VIEW IF EXISTS vw_cohort_retention_heatmap CASCADE;
DROP VIEW IF EXISTS vw_qos_streaming_health CASCADE;
DROP VIEW IF EXISTS vw_top_global_titles CASCADE;

DROP TABLE IF EXISTS fact_daily_streaming CASCADE;
DROP TABLE IF EXISTS fact_cohort_retention CASCADE;
DROP TABLE IF EXISTS fact_financials_monthly CASCADE;
DROP TABLE IF EXISTS fact_content_performance_monthly CASCADE;
DROP TABLE IF EXISTS fact_subscriber_snapshots CASCADE;
DROP TABLE IF EXISTS dim_subscriber CASCADE;
DROP TABLE IF EXISTS dim_content CASCADE;
DROP TABLE IF EXISTS dim_device CASCADE;
DROP TABLE IF EXISTS dim_plan CASCADE;
DROP TABLE IF EXISTS dim_country CASCADE;
DROP TABLE IF EXISTS dim_region CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;

-- ==============================================================================
-- DIMENSION TABLES
-- ==============================================================================

-- 1. Date Dimension
CREATE TABLE dim_date (
    date_key INT PRIMARY KEY,
    full_date DATE NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    year_quarter VARCHAR(10) NOT NULL,
    month INT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    month_abbr VARCHAR(5) NOT NULL,
    year_month VARCHAR(7) NOT NULL,
    day_of_month INT NOT NULL,
    day_of_week INT NOT NULL,
    day_name VARCHAR(15) NOT NULL,
    is_weekend SMALLINT NOT NULL,
    is_holiday_season SMALLINT NOT NULL,
    is_summer_peak SMALLINT NOT NULL,
    is_netflix_release_day SMALLINT NOT NULL
);

-- 2. Region Dimension
CREATE TABLE dim_region (
    region_id INT PRIMARY KEY,
    region_code VARCHAR(10) NOT NULL UNIQUE,
    region_name VARCHAR(100) NOT NULL,
    hq_location VARCHAR(100) NOT NULL,
    currency_code VARCHAR(5) NOT NULL
);

-- 3. Country Dimension
CREATE TABLE dim_country (
    country_id INT PRIMARY KEY,
    region_id INT NOT NULL REFERENCES dim_region(region_id),
    country_code VARCHAR(5) NOT NULL UNIQUE,
    country_name VARCHAR(100) NOT NULL,
    tier VARCHAR(20) NOT NULL,
    broadband_penetration_pct NUMERIC(5,2) NOT NULL,
    sub_base_weight NUMERIC(6,4) NOT NULL,
    avg_arpu_base NUMERIC(6,2) NOT NULL
);

-- 4. Plan Dimension
CREATE TABLE dim_plan (
    plan_id INT PRIMARY KEY,
    plan_code VARCHAR(20) NOT NULL UNIQUE,
    plan_name VARCHAR(100) NOT NULL,
    monthly_price_usd NUMERIC(6,2) NOT NULL,
    simultaneous_streams INT NOT NULL,
    max_resolution VARCHAR(50) NOT NULL,
    is_ad_supported SMALLINT NOT NULL,
    has_downloads SMALLINT NOT NULL,
    allows_extra_members SMALLINT NOT NULL,
    launched_year INT NOT NULL
);

-- 5. Device Dimension
CREATE TABLE dim_device (
    device_id INT PRIMARY KEY,
    device_type VARCHAR(100) NOT NULL,
    device_category VARCHAR(50) NOT NULL,
    stream_share_pct NUMERIC(5,2) NOT NULL,
    avg_bitrate_mbps NUMERIC(5,2) NOT NULL
);

-- 6. Content Dimension
CREATE TABLE dim_content (
    content_id INT PRIMARY KEY,
    title_name VARCHAR(255) NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    genre VARCHAR(100) NOT NULL,
    original_language VARCHAR(50) NOT NULL,
    release_year INT NOT NULL,
    production_budget_m_usd NUMERIC(8,2) NOT NULL,
    imdb_rating NUMERIC(3,1) NOT NULL,
    episodes_count INT NOT NULL,
    is_netflix_original SMALLINT NOT NULL,
    content_tier VARCHAR(50) NOT NULL
);

-- 7. Sampled Subscriber Dimension
CREATE TABLE dim_subscriber (
    subscriber_id BIGINT PRIMARY KEY,
    signup_date_key INT NOT NULL,
    signup_date DATE NOT NULL,
    country_id INT NOT NULL REFERENCES dim_country(country_id),
    region_id INT NOT NULL REFERENCES dim_region(region_id),
    current_plan_id INT NOT NULL REFERENCES dim_plan(plan_id),
    primary_device_id INT NOT NULL REFERENCES dim_device(device_id),
    acquisition_channel VARCHAR(100) NOT NULL,
    subscriber_status VARCHAR(20) NOT NULL,
    churn_date_key INT,
    tenure_months INT NOT NULL,
    extra_members_count INT NOT NULL DEFAULT 0,
    estimated_ltv_usd NUMERIC(10,2) NOT NULL
);

-- ==============================================================================
-- FACT TABLES
-- ==============================================================================

-- 1. Monthly Regional Subscriber Snapshots
CREATE TABLE fact_subscriber_snapshots (
    snapshot_date_key INT NOT NULL,
    year_month VARCHAR(7) NOT NULL,
    region_id INT NOT NULL REFERENCES dim_region(region_id),
    paid_memberships_start_m NUMERIC(10,3) NOT NULL,
    gross_additions_m NUMERIC(10,3) NOT NULL,
    churned_memberships_m NUMERIC(10,3) NOT NULL,
    net_additions_m NUMERIC(10,3) NOT NULL,
    paid_memberships_end_m NUMERIC(10,3) NOT NULL,
    monthly_churn_rate_pct NUMERIC(5,2) NOT NULL,
    avg_revenue_per_membership_usd NUMERIC(6,2) NOT NULL,
    ad_supported_memberships_m NUMERIC(10,3) NOT NULL,
    standard_memberships_m NUMERIC(10,3) NOT NULL,
    premium_memberships_m NUMERIC(10,3) NOT NULL,
    subscription_revenue_m_usd NUMERIC(12,2) NOT NULL,
    advertising_revenue_m_usd NUMERIC(12,2) NOT NULL,
    total_streaming_revenue_m_usd NUMERIC(12,2) NOT NULL,
    PRIMARY KEY (snapshot_date_key, region_id)
);

-- 2. Content Monthly Performance
CREATE TABLE fact_content_performance_monthly (
    performance_date_key INT NOT NULL,
    year_month VARCHAR(7) NOT NULL,
    content_id INT NOT NULL REFERENCES dim_content(content_id),
    monthly_hours_viewed_m NUMERIC(10,2) NOT NULL,
    monthly_views_m NUMERIC(10,2) NOT NULL,
    completion_rate_pct NUMERIC(5,1) NOT NULL,
    repeat_view_share_pct NUMERIC(5,1) NOT NULL,
    monthly_amortization_usd_m NUMERIC(8,2) NOT NULL,
    content_roi_multiplier NUMERIC(6,2) NOT NULL,
    PRIMARY KEY (performance_date_key, content_id)
);

-- 3. Monthly Financials (P&L and FCF)
CREATE TABLE fact_financials_monthly (
    financial_date_key INT PRIMARY KEY,
    year_month VARCHAR(7) NOT NULL UNIQUE,
    subscription_revenue_m_usd NUMERIC(12,2) NOT NULL,
    advertising_revenue_m_usd NUMERIC(12,2) NOT NULL,
    total_revenue_m_usd NUMERIC(12,2) NOT NULL,
    content_amortization_m_usd NUMERIC(12,2) NOT NULL,
    technology_development_m_usd NUMERIC(12,2) NOT NULL,
    marketing_expense_m_usd NUMERIC(12,2) NOT NULL,
    general_admin_expense_m_usd NUMERIC(12,2) NOT NULL,
    total_operating_expenses_m_usd NUMERIC(12,2) NOT NULL,
    operating_income_m_usd NUMERIC(12,2) NOT NULL,
    operating_margin_pct NUMERIC(5,2) NOT NULL,
    free_cash_flow_m_usd NUMERIC(12,2) NOT NULL
);

-- 4. Cohort Retention Matrix
CREATE TABLE fact_cohort_retention (
    cohort_signup_month VARCHAR(7) NOT NULL,
    tenure_month INT NOT NULL,
    evaluation_month VARCHAR(7) NOT NULL,
    initial_cohort_size INT NOT NULL,
    retained_subscribers_count INT NOT NULL,
    retention_rate_pct NUMERIC(5,2) NOT NULL,
    PRIMARY KEY (cohort_signup_month, tenure_month)
);

-- 5. Daily Streaming Quality of Service (QoS)
CREATE TABLE fact_daily_streaming (
    date_key INT PRIMARY KEY,
    full_date DATE NOT NULL,
    total_stream_hours_m NUMERIC(10,2) NOT NULL,
    peak_concurrent_streams_m NUMERIC(8,2) NOT NULL,
    uhd_4k_share_pct NUMERIC(5,2) NOT NULL,
    hdr_share_pct NUMERIC(5,2) NOT NULL,
    rebuffer_ratio_pct NUMERIC(6,3) NOT NULL,
    avg_bitrate_mbps NUMERIC(5,2) NOT NULL,
    non_english_stream_share_pct NUMERIC(5,2) NOT NULL
);

-- ==============================================================================
-- INDEXES FOR PERFORMANCE
-- ==============================================================================
CREATE INDEX idx_snaps_ym ON fact_subscriber_snapshots(year_month);
CREATE INDEX idx_snaps_region ON fact_subscriber_snapshots(region_id);
CREATE INDEX idx_perf_content ON fact_content_performance_monthly(content_id);
CREATE INDEX idx_perf_ym ON fact_content_performance_monthly(year_month);
CREATE INDEX idx_sub_country ON dim_subscriber(country_id);
CREATE INDEX idx_sub_plan ON dim_subscriber(current_plan_id);
CREATE INDEX idx_sub_status ON dim_subscriber(subscriber_status);
CREATE INDEX idx_content_genre ON dim_content(genre);
CREATE INDEX idx_content_tier ON dim_content(content_tier);

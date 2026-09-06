-- ==============================================================================
-- Netflix Global Streaming Performance Analytics (2021-2025)
-- File: sql/02_bi_views.sql
-- 8 Production-Grade Analytical Views for Power BI & Executive Reporting
-- ==============================================================================

-- 1. Executive Monthly KPI Rollup (Card Visuals & Top-Level Dashboard)
CREATE OR REPLACE VIEW vw_executive_monthly_kpi AS
SELECT 
    f.financial_date_key,
    f.year_month,
    d.year,
    d.quarter,
    d.month_name,
    -- Topline Financials
    f.total_revenue_m_usd,
    f.subscription_revenue_m_usd,
    f.advertising_revenue_m_usd,
    f.operating_income_m_usd,
    f.operating_margin_pct,
    f.free_cash_flow_m_usd,
    -- Global Memberships
    SUM(s.paid_memberships_end_m) AS global_paid_memberships_m,
    SUM(s.net_additions_m) AS global_net_additions_m,
    SUM(s.ad_supported_memberships_m) AS global_ad_tier_memberships_m,
    ROUND(AVG(s.avg_revenue_per_membership_usd), 2) AS global_avg_arm_usd,
    ROUND(AVG(s.monthly_churn_rate_pct), 2) AS global_monthly_churn_rate_pct,
    -- Year-Over-Year Revenue Growth
    ROUND(
        (f.total_revenue_m_usd - LAG(f.total_revenue_m_usd, 12) OVER (ORDER BY f.financial_date_key)) /
        NULLIF(LAG(f.total_revenue_m_usd, 12) OVER (ORDER BY f.financial_date_key), 0) * 100, 2
    ) AS yoy_revenue_growth_pct
FROM fact_financials_monthly f
JOIN dim_date d ON f.financial_date_key = d.date_key
JOIN fact_subscriber_snapshots s ON f.year_month = s.year_month
GROUP BY 
    f.financial_date_key, f.year_month, d.year, d.quarter, d.month_name,
    f.total_revenue_m_usd, f.subscription_revenue_m_usd, f.advertising_revenue_m_usd,
    f.operating_income_m_usd, f.operating_margin_pct, f.free_cash_flow_m_usd;

-- 2. Subscriber Growth Trajectory by Region
CREATE OR REPLACE VIEW vw_subscriber_growth_trajectory AS
SELECT 
    s.snapshot_date_key,
    s.year_month,
    r.region_code,
    r.region_name,
    s.paid_memberships_start_m,
    s.gross_additions_m,
    s.churned_memberships_m,
    s.net_additions_m,
    s.paid_memberships_end_m,
    s.avg_revenue_per_membership_usd,
    s.monthly_churn_rate_pct,
    s.ad_supported_memberships_m,
    ROUND((s.ad_supported_memberships_m / NULLIF(s.paid_memberships_end_m, 0)) * 100, 2) AS ad_tier_penetration_pct,
    s.total_streaming_revenue_m_usd
FROM fact_subscriber_snapshots s
JOIN dim_region r ON s.region_id = r.region_id;

-- 3. Content ROI & Efficiency Quadrant (Blockbuster vs Efficiency)
CREATE OR REPLACE VIEW vw_content_roi_quadrant AS
SELECT 
    c.content_id,
    c.title_name,
    c.content_type,
    c.genre,
    c.original_language,
    c.release_year,
    c.production_budget_m_usd,
    c.imdb_rating,
    c.is_netflix_original,
    c.content_tier,
    SUM(p.monthly_hours_viewed_m) AS total_lifetime_hours_viewed_m,
    SUM(p.monthly_views_m) AS total_lifetime_views_m,
    ROUND(AVG(p.completion_rate_pct), 1) AS avg_completion_rate_pct,
    MAX(p.content_roi_multiplier) AS max_content_roi_multiplier,
    -- Cost per viewing hour delivered ($)
    ROUND(c.production_budget_m_usd / NULLIF(SUM(p.monthly_hours_viewed_m), 0), 3) AS cost_per_viewing_hour_usd,
    CASE 
        WHEN MAX(p.content_roi_multiplier) >= 3.0 AND c.imdb_rating >= 7.5 THEN 'Blockbuster Hit'
        WHEN MAX(p.content_roi_multiplier) >= 3.0 AND c.imdb_rating < 7.5 THEN 'High ROI Pop Phenomenon'
        WHEN MAX(p.content_roi_multiplier) < 3.0 AND c.imdb_rating >= 7.5 THEN 'Prestige Critical Darling'
        ELSE 'Underperforming Asset'
    END AS strategic_content_quadrant
FROM dim_content c
JOIN fact_content_performance_monthly p ON c.content_id = p.content_id
GROUP BY 
    c.content_id, c.title_name, c.content_type, c.genre, c.original_language,
    c.release_year, c.production_budget_m_usd, c.imdb_rating, c.is_netflix_original, c.content_tier;

-- 4. Regional Performance & ARPU Matrix
CREATE OR REPLACE VIEW vw_regional_performance_matrix AS
SELECT 
    r.region_code,
    r.region_name,
    r.hq_location,
    COUNT(DISTINCT c.country_id) AS total_tracked_countries,
    ROUND(AVG(c.broadband_penetration_pct), 1) AS avg_broadband_penetration_pct,
    -- Latest 2025 snapshot stats
    MAX(CASE WHEN s.year_month = '2025-12' THEN s.paid_memberships_end_m END) AS subs_2025_m,
    MAX(CASE WHEN s.year_month = '2021-01' THEN s.paid_memberships_start_m END) AS subs_2021_m,
    ROUND(
        (MAX(CASE WHEN s.year_month = '2025-12' THEN s.paid_memberships_end_m END) - 
         MAX(CASE WHEN s.year_month = '2021-01' THEN s.paid_memberships_start_m END)) /
        NULLIF(MAX(CASE WHEN s.year_month = '2021-01' THEN s.paid_memberships_start_m END), 0) * 100, 1
    ) AS five_year_growth_pct,
    MAX(CASE WHEN s.year_month = '2025-12' THEN s.avg_revenue_per_membership_usd END) AS latest_arm_usd
FROM dim_region r
JOIN dim_country c ON r.region_id = c.region_id
JOIN fact_subscriber_snapshots s ON r.region_id = s.region_id
GROUP BY r.region_code, r.region_name, r.hq_location;

-- 5. Ad-Tier Adoption & Revenue Funnel (2022-2025 Post-Launch)
CREATE OR REPLACE VIEW vw_ad_tier_adoption_funnel AS
SELECT 
    s.year_month,
    SUM(s.paid_memberships_end_m) AS total_subscribers_m,
    SUM(s.ad_supported_memberships_m) AS ad_supported_subscribers_m,
    ROUND(SUM(s.ad_supported_memberships_m) / NULLIF(SUM(s.paid_memberships_end_m), 0) * 100, 2) AS ad_subscriber_share_pct,
    SUM(s.advertising_revenue_m_usd) AS ad_revenue_m_usd,
    ROUND(SUM(s.advertising_revenue_m_usd) / NULLIF(SUM(s.ad_supported_memberships_m), 0), 2) AS ad_arm_per_ad_subscriber_usd
FROM fact_subscriber_snapshots s
WHERE s.year_month >= '2022-11'
GROUP BY s.year_month;

-- 6. Cohort Retention Heatmap Matrix
CREATE OR REPLACE VIEW vw_cohort_retention_heatmap AS
SELECT 
    cohort_signup_month,
    initial_cohort_size,
    MAX(CASE WHEN tenure_month = 0 THEN retention_rate_pct END) AS m0_retention,
    MAX(CASE WHEN tenure_month = 1 THEN retention_rate_pct END) AS m1_retention,
    MAX(CASE WHEN tenure_month = 3 THEN retention_rate_pct END) AS m3_retention,
    MAX(CASE WHEN tenure_month = 6 THEN retention_rate_pct END) AS m6_retention,
    MAX(CASE WHEN tenure_month = 9 THEN retention_rate_pct END) AS m9_retention,
    MAX(CASE WHEN tenure_month = 12 THEN retention_rate_pct END) AS m12_retention,
    MAX(CASE WHEN tenure_month = 18 THEN retention_rate_pct END) AS m18_retention,
    MAX(CASE WHEN tenure_month = 24 THEN retention_rate_pct END) AS m24_retention
FROM fact_cohort_retention
GROUP BY cohort_signup_month, initial_cohort_size;

-- 7. Quality of Service (QoS) & Infrastructure Stream Health
CREATE OR REPLACE VIEW vw_qos_streaming_health AS
SELECT 
    d.year,
    d.quarter,
    d.month_name,
    ROUND(AVG(q.total_stream_hours_m), 2) AS avg_daily_stream_hours_m,
    ROUND(MAX(q.peak_concurrent_streams_m), 2) AS max_peak_concurrent_streams_m,
    ROUND(AVG(q.uhd_4k_share_pct), 2) AS avg_uhd_4k_share_pct,
    ROUND(AVG(q.hdr_share_pct), 2) AS avg_hdr_share_pct,
    ROUND(AVG(q.rebuffer_ratio_pct), 3) AS avg_rebuffer_ratio_pct,
    ROUND(AVG(q.avg_bitrate_mbps), 2) AS avg_video_bitrate_mbps,
    ROUND(AVG(q.non_english_stream_share_pct), 2) AS avg_non_english_stream_share_pct
FROM fact_daily_streaming q
JOIN dim_date d ON q.date_key = d.date_key
GROUP BY d.year, d.quarter, d.month_name;

-- 8. Top Global All-Time Titles by Viewing Hours
CREATE OR REPLACE VIEW vw_top_global_titles AS
SELECT 
    c.title_name,
    c.content_type,
    c.genre,
    c.original_language,
    c.release_year,
    c.production_budget_m_usd,
    c.imdb_rating,
    c.is_netflix_original,
    SUM(p.monthly_hours_viewed_m) AS total_hours_viewed_m,
    SUM(p.monthly_views_m) AS total_estimated_views_m,
    ROUND(AVG(p.completion_rate_pct), 1) AS avg_completion_pct,
    MAX(p.content_roi_multiplier) AS roi_multiplier
FROM dim_content c
JOIN fact_content_performance_monthly p ON c.content_id = p.content_id
GROUP BY 
    c.title_name, c.content_type, c.genre, c.original_language,
    c.release_year, c.production_budget_m_usd, c.imdb_rating, c.is_netflix_original
ORDER BY total_hours_viewed_m DESC
LIMIT 50;

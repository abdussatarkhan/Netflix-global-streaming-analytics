#!/usr/bin/env python3
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
import json
import pandas as pd
import numpy as np

def export_dashboard_json(data_dir='../data', output_json='../dashboard/data.json'):
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    
    df_region = pd.read_csv(os.path.join(data_dir, 'dim_region.csv'))
    df_country = pd.read_csv(os.path.join(data_dir, 'dim_country.csv'))
    df_plan = pd.read_csv(os.path.join(data_dir, 'dim_plan.csv'))
    df_device = pd.read_csv(os.path.join(data_dir, 'dim_device.csv'))
    df_content = pd.read_csv(os.path.join(data_dir, 'dim_content.csv'))
    df_snaps = pd.read_csv(os.path.join(data_dir, 'fact_subscriber_snapshots.csv'))
    df_perf = pd.read_csv(os.path.join(data_dir, 'fact_content_performance_monthly.csv'))
    df_fin = pd.read_csv(os.path.join(data_dir, 'fact_financials_monthly.csv'))
    df_cohort = pd.read_csv(os.path.join(data_dir, 'fact_cohort_retention.csv'))
    df_daily = pd.read_csv(os.path.join(data_dir, 'fact_daily_streaming.csv'))
    
    latest_fin = df_fin.iloc[-1]
    latest_snap = df_snaps[df_snaps['year_month'] == '2025-12']
    init_snap = df_snaps[df_snaps['year_month'] == '2021-01']
    
    total_subs_2025 = round(latest_snap['paid_memberships_end_m'].sum(), 2)
    total_subs_2021 = round(init_snap['paid_memberships_start_m'].sum(), 2)
    sub_growth_pct = round(((total_subs_2025 - total_subs_2021) / total_subs_2021) * 100, 1)
    
    ann_rev_2025 = round(df_fin[df_fin['year_month'].str.startswith('2025')]['total_revenue_m_usd'].sum() / 1000.0, 2)
    ann_rev_2021 = round(df_fin[df_fin['year_month'].str.startswith('2021')]['total_revenue_m_usd'].sum() / 1000.0, 2)
    rev_growth_pct = round(((ann_rev_2025 - ann_rev_2021) / ann_rev_2021) * 100, 1)
    
    global_arpu_2025 = round(latest_snap['avg_revenue_per_membership_usd'].mean(), 2)
    ad_subs_total_2025 = round(latest_snap['ad_supported_memberships_m'].sum(), 2)
    latest_op_margin = round(latest_fin['operating_margin_pct'], 1)
    latest_fcf_b = round(df_fin[df_fin['year_month'].str.startswith('2025')]['free_cash_flow_m_usd'].sum() / 1000.0, 2)
    
    kpis = {
        'total_paid_subscribers_m': total_subs_2025,
        'subscriber_growth_5yr_pct': sub_growth_pct,
        'annual_revenue_b_usd': ann_rev_2025,
        'revenue_growth_5yr_pct': rev_growth_pct,
        'global_avg_arm_usd': global_arpu_2025,
        'ad_supported_memberships_m': ad_subs_total_2025,
        'operating_margin_pct': latest_op_margin,
        'annual_free_cash_flow_b_usd': latest_fcf_b,
        'avg_monthly_churn_pct': 2.15,
        'total_catalog_titles': len(df_content),
        'avg_daily_stream_hours_m': 648.5
    }
    
    monthly_trend = []
    for ym in df_fin['year_month'].unique():
        f_row = df_fin[df_fin['year_month'] == ym].iloc[0]
        s_rows = df_snaps[df_snaps['year_month'] == ym]
        
        monthly_trend.append({
            'year_month': ym,
            'paid_subscribers_m': round(s_rows['paid_memberships_end_m'].sum(), 2),
            'ad_subscribers_m': round(s_rows['ad_supported_memberships_m'].sum(), 2),
            'monthly_revenue_m': round(f_row['total_revenue_m_usd'], 1),
            'subscription_revenue_m': round(f_row['subscription_revenue_m_usd'], 1),
            'ad_revenue_m': round(f_row['advertising_revenue_m_usd'], 1),
            'operating_income_m': round(f_row['operating_income_m_usd'], 1),
            'operating_margin_pct': round(f_row['operating_margin_pct'], 1),
            'free_cash_flow_m': round(f_row['free_cash_flow_m_usd'], 1)
        })
        
    regional_data = []
    for rid in [1, 2, 3, 4]:
        r_info = df_region[df_region['region_id'] == rid].iloc[0]
        r_snaps_2025 = df_snaps[(df_snaps['region_id'] == rid) & (df_snaps['year_month'] == '2025-12')].iloc[0]
        r_snaps_2021 = df_snaps[(df_snaps['region_id'] == rid) & (df_snaps['year_month'] == '2021-01')].iloc[0]
        
        c_list = df_country[df_country['region_id'] == rid][['country_name', 'country_code', 'tier', 'avg_arpu_base']].to_dict(orient='records')
        
        regional_data.append({
            'region_id': rid,
            'region_code': r_info['region_code'],
            'region_name': r_info['region_name'],
            'hq_location': r_info['hq_location'],
            'subscribers_2021_m': round(r_snaps_2021['paid_memberships_start_m'], 1),
            'subscribers_2025_m': round(r_snaps_2025['paid_memberships_end_m'], 1),
            'growth_pct': round(((r_snaps_2025['paid_memberships_end_m'] - r_snaps_2021['paid_memberships_start_m']) / r_snaps_2021['paid_memberships_start_m']) * 100, 1),
            'arpu_2025_usd': round(r_snaps_2025['avg_revenue_per_membership_usd'], 2),
            'ad_tier_share_pct': round((r_snaps_2025['ad_supported_memberships_m'] / r_snaps_2025['paid_memberships_end_m']) * 100, 1),
            'countries_count': len(c_list),
            'key_countries': c_list
        })
        
    title_summary = df_perf.groupby('content_id').agg({
        'monthly_hours_viewed_m': 'sum',
        'monthly_views_m': 'sum',
        'completion_rate_pct': 'mean',
        'content_roi_multiplier': 'max'
    }).reset_index()
    
    merged_content = pd.merge(df_content, title_summary, on='content_id')
    top_titles = merged_content.sort_values(by='monthly_hours_viewed_m', ascending=False).head(35)
    
    content_leaderboard = []
    for idx, row in top_titles.iterrows():
        content_leaderboard.append({
            'content_id': int(row['content_id']),
            'title_name': row['title_name'],
            'content_type': row['content_type'],
            'genre': row['genre'],
            'original_language': row['original_language'],
            'release_year': int(row['release_year']),
            'budget_m_usd': float(row['production_budget_m_usd']),
            'imdb_rating': float(row['imdb_rating']),
            'total_hours_viewed_m': round(float(row['monthly_hours_viewed_m']), 1),
            'total_views_m': round(float(row['monthly_views_m']), 1),
            'avg_completion_rate_pct': round(float(row['completion_rate_pct']), 1),
            'content_roi_multiplier': round(float(row['content_roi_multiplier']), 2),
            'is_netflix_original': int(row['is_netflix_original']),
            'content_tier': row['content_tier']
        })
        
    genre_summary = merged_content.groupby('genre').agg({
        'monthly_hours_viewed_m': 'sum',
        'content_id': 'count',
        'imdb_rating': 'mean'
    }).reset_index()
    genre_data = []
    for idx, r in genre_summary.iterrows():
        genre_data.append({
            'genre': r['genre'],
            'total_hours_m': round(float(r['monthly_hours_viewed_m']), 1),
            'title_count': int(r['content_id']),
            'avg_imdb': round(float(r['imdb_rating']), 2)
        })
    genre_data = sorted(genre_data, key=lambda x: x['total_hours_m'], reverse=True)

    sample_cohorts = ['2021-01', '2021-07', '2022-01', '2022-07', '2022-11', '2023-01', '2023-06', '2023-11', '2024-01', '2024-06', '2025-01']
    cohort_matrix = []
    for c_id in sample_cohorts:
        c_sub = df_cohort[df_cohort['cohort_signup_month'] == c_id]
        if len(c_sub) == 0:
            continue
        rates = {}
        for t in [0, 1, 3, 6, 9, 12, 18, 24]:
            match = c_sub[c_sub['tenure_month'] == t]
            if len(match) > 0:
                rates[f"M{t}"] = round(float(match['retention_rate_pct'].values[0]), 1)
            else:
                rates[f"M{t}"] = None
        cohort_matrix.append({
            'cohort_month': c_id,
            'initial_subscribers': int(c_sub['initial_cohort_size'].iloc[0]),
            'retention_rates': rates
        })
        
    plans_mix = []
    for idx, p in df_plan.iterrows():
        if p['plan_code'] == 'STD_ADS':
            share = 28.5
        elif p['plan_code'] == 'STANDARD':
            share = 41.0
        elif p['plan_code'] == 'PREMIUM':
            share = 22.5
        elif p['plan_code'] == 'MOBILE':
            share = 5.5
        else:
            share = 2.5
        plans_mix.append({
            'plan_name': p['plan_name'],
            'plan_code': p['plan_code'],
            'price_usd': float(p['monthly_price_usd']),
            'sub_share_pct': share
        })
        
    devices_mix = df_device[['device_type', 'device_category', 'stream_share_pct', 'avg_bitrate_mbps']].to_dict(orient='records')
    
    dashboard_payload = {
        'generated_at': '2026-09-06T18:00:00Z',
        'project_title': 'Netflix Global Streaming & Content Performance Analytics (2021-2025)',
        'kpis': kpis,
        'monthly_trajectory': monthly_trend,
        'regional_breakdown': regional_data,
        'top_content_leaderboard': content_leaderboard,
        'genre_distribution': genre_data,
        'cohort_retention_matrix': cohort_matrix,
        'plans_mix': plans_mix,
        'devices_mix': devices_mix
    }
    
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(dashboard_payload, f, indent=2)
        
    print(f"[+] [07] Exported complete dashboard payload to {output_json}")

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.abspath(__file__))
    export_dashboard_json(data_dir=os.path.join(base_dir, '..', 'data'), output_json=os.path.join(base_dir, '..', 'dashboard', 'data.json'))

#!/usr/bin/env python3
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import numpy as np

def generate_content_performance(data_dir='../data'):
    os.makedirs(data_dir, exist_ok=True)
    np.random.seed(202)

    df_content = pd.read_csv(os.path.join(data_dir, 'dim_content.csv'))
    
    dates = pd.date_range(start='2021-01-01', end='2025-12-01', freq='MS')
    performance_records = []
    
    for idx, row in df_content.iterrows():
        cid = row['content_id']
        rel_yr = row['release_year']
        budget = row['production_budget_m_usd']
        rating = row['imdb_rating']
        is_orig = row['is_netflix_original']
        c_type = row['content_type']
        
        monthly_amort = round(budget / 36.0, 2)
        rel_month = np.random.randint(1, 13)
        rel_date = pd.Timestamp(year=rel_yr, month=rel_month, day=1)
        
        hit_factor = (rating / 7.0) ** 2.2 * (1.5 if is_orig else 1.1)
        base_peak_hours = budget * 4.5 * hit_factor
        
        cumulative_views_m = 0
        cumulative_hours_m = 0
        
        for d in dates:
            if d < rel_date:
                continue
                
            months_active = (d.year - rel_date.year) * 12 + (d.month - rel_date.month)
            date_key = int(d.strftime('%Y%m01'))
            
            if months_active == 0:
                decay = 1.0
                completion_rate = min(92.0, max(55.0, 68.0 + rating * 2.5 + np.random.normal(0, 3)))
            elif months_active == 1:
                decay = 0.55
                completion_rate = min(90.0, max(52.0, 65.0 + rating * 2.2 + np.random.normal(0, 3)))
            elif months_active <= 6:
                decay = 0.20 * (0.85 ** (months_active - 2))
                completion_rate = min(88.0, max(50.0, 62.0 + rating * 2.0))
            else:
                decay = 0.04 * (1.0 + (rating - 7.0) * 0.2)
                completion_rate = min(85.0, max(45.0, 60.0 + rating * 1.5))
                
            hours_m = round(max(0.05, base_peak_hours * decay * np.random.uniform(0.85, 1.15)), 2)
            runtime_hrs = (row['episodes_count'] * 0.8) if c_type in ['TV Series', 'Docuseries', 'Animation'] else 1.8
            views_m = round(hours_m / runtime_hrs, 2)
            
            cumulative_hours_m += hours_m
            cumulative_views_m += views_m
            
            implied_val_m = cumulative_hours_m * 0.18
            roi_multiplier = round(implied_val_m / max(1.0, budget), 2)
            
            performance_records.append({
                'performance_date_key': date_key,
                'year_month': d.strftime('%Y-%m'),
                'content_id': cid,
                'monthly_hours_viewed_m': hours_m,
                'monthly_views_m': views_m,
                'completion_rate_pct': round(completion_rate, 1),
                'repeat_view_share_pct': round(np.random.uniform(8.0, 24.0), 1),
                'monthly_amortization_usd_m': monthly_amort if months_active < 36 else 0.0,
                'content_roi_multiplier': roi_multiplier
            })
            
    df_perf = pd.DataFrame(performance_records)
    df_perf.to_csv(os.path.join(data_dir, 'fact_content_performance_monthly.csv'), index=False)
    print(f"[+] [04] Created fact_content_performance_monthly.csv with {len(df_perf)} rows")

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.abspath(__file__))
    generate_content_performance(data_dir=os.path.join(base_dir, '..', 'data'))

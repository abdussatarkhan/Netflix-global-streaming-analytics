#!/usr/bin/env python3
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import numpy as np

def generate_daily_streaming(data_dir='../data'):
    os.makedirs(data_dir, exist_ok=True)
    np.random.seed(404)

    df_date = pd.read_csv(os.path.join(data_dir, 'dim_date.csv'))
    records = []
    
    for idx, row in df_date.iterrows():
        d_key = row['date_key']
        f_date = row['full_date']
        year = row['year']
        month = row['month']
        is_wknd = row['is_weekend']
        is_holiday = row['is_holiday_season']
        is_rel_day = row['is_netflix_release_day']
        
        base_hrs = 420.0 + ((year - 2021) * 55.0) + (month * 1.5)
        wknd_mult = 1.32 if is_wknd else 1.00
        hol_mult = 1.25 if is_holiday else 1.00
        rel_mult = 1.12 if is_rel_day else 1.00
        
        total_stream_hours_m = round(base_hrs * wknd_mult * hol_mult * rel_mult * np.random.uniform(0.96, 1.04), 2)
        peak_concurrent_m = round(total_stream_hours_m * 0.125 * np.random.uniform(0.95, 1.05), 2)
        uhd_4k_share_pct = round(min(45.0, 18.0 + (year - 2021) * 6.5 + np.random.normal(0, 0.5)), 2)
        hdr_share_pct = round(uhd_4k_share_pct * 0.72, 2)
        rebuffer_ratio_pct = round(max(0.08, 0.28 - (year - 2021) * 0.035 + np.random.normal(0, 0.02)), 3)
        avg_bitrate_mbps = round(11.5 - ((year - 2021) * 0.4) + np.random.normal(0, 0.2), 2)
        non_english_share_pct = round(min(52.0, 32.0 + (year - 2021) * 4.2 + (5.0 if year >= 2022 else 0)), 2)
        
        records.append({
            'date_key': d_key,
            'full_date': f_date,
            'total_stream_hours_m': total_stream_hours_m,
            'peak_concurrent_streams_m': peak_concurrent_m,
            'uhd_4k_share_pct': uhd_4k_share_pct,
            'hdr_share_pct': hdr_share_pct,
            'rebuffer_ratio_pct': rebuffer_ratio_pct,
            'avg_bitrate_mbps': avg_bitrate_mbps,
            'non_english_stream_share_pct': non_english_share_pct
        })
        
    df_daily = pd.DataFrame(records)
    df_daily.to_csv(os.path.join(data_dir, 'fact_daily_streaming.csv'), index=False)
    print(f"[+] [06] Created fact_daily_streaming.csv with {len(df_daily)} daily QoS records")

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.abspath(__file__))
    generate_daily_streaming(data_dir=os.path.join(base_dir, '..', 'data'))

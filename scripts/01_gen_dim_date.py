#!/usr/bin/env python3
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
from datetime import datetime, timedelta

def generate_dim_date(start_date='2021-01-01', end_date='2025-12-31', output_path='../data/dim_date.csv'):
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    dates = []
    curr = start
    while curr <= end:
        dates.append(curr)
        curr += timedelta(days=1)
        
    records = []
    for d in dates:
        date_key = int(d.strftime('%Y%m%d'))
        full_date = d.strftime('%Y-%m-%d')
        year = d.year
        month = d.month
        month_name = d.strftime('%B')
        month_abbr = d.strftime('%b')
        quarter = (month - 1) // 3 + 1
        year_quarter = f"{year}-Q{quarter}"
        year_month = d.strftime('%Y-%m')
        day_of_month = d.day
        day_of_week = d.isoweekday()
        day_name = d.strftime('%A')
        is_weekend = 1 if day_of_week in [6, 7] else 0
        is_holiday_season = 1 if (month == 12) or (month == 11 and day_of_month >= 20) or (month == 1 and day_of_month <= 5) else 0
        is_summer_peak = 1 if (month == 7) or (month == 6 and day_of_month >= 15) or (month == 8 and day_of_month <= 20) else 0
        is_netflix_release_day = 1 if day_of_week == 5 else 0
        
        records.append({
            'date_key': date_key,
            'full_date': full_date,
            'year': year,
            'quarter': quarter,
            'year_quarter': year_quarter,
            'month': month,
            'month_name': month_name,
            'month_abbr': month_abbr,
            'year_month': year_month,
            'day_of_month': day_of_month,
            'day_of_week': day_of_week,
            'day_name': day_name,
            'is_weekend': is_weekend,
            'is_holiday_season': is_holiday_season,
            'is_summer_peak': is_summer_peak,
            'is_netflix_release_day': is_netflix_release_day
        })
        
    df = pd.DataFrame(records)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"[+] [01] Generated {len(df)} rows in {output_path}")

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(base_dir, '..', 'data', 'dim_date.csv')
    generate_dim_date(output_path=out)

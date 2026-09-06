#!/usr/bin/env python3
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_subscribers_and_snapshots(data_dir='../data'):
    os.makedirs(data_dir, exist_ok=True)
    np.random.seed(101)

    df_countries = pd.read_csv(os.path.join(data_dir, 'dim_country.csv'))
    df_plans = pd.read_csv(os.path.join(data_dir, 'dim_plan.csv'))
    df_devices = pd.read_csv(os.path.join(data_dir, 'dim_device.csv'))
    
    n_subs = 25000
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2025, 12, 31)
    
    country_weights = df_countries['sub_base_weight'].values
    country_weights = country_weights / country_weights.sum()
    
    country_ids = np.random.choice(df_countries['country_id'].values, size=n_subs, p=country_weights)
    
    acquisition_channels = ['Organic Word of Mouth', 'Search & SEO', 'Social Media Campaign', 'Smart TV Pre-install', 'ISP / Telco Bundle', 'Referral']
    channels = np.random.choice(acquisition_channels, size=n_subs, p=[0.35, 0.20, 0.18, 0.12, 0.10, 0.05])
    
    subscribers = []
    days_range = (end_date - start_date).days
    
    for i in range(n_subs):
        sub_id = 100000 + i + 1
        cid = country_ids[i]
        c_info = df_countries[df_countries['country_id'] == cid].iloc[0]
        
        random_days = np.random.randint(0, days_range)
        signup_dt = start_date + timedelta(days=random_days)
        signup_date_key = int(signup_dt.strftime('%Y%m%d'))
        
        if signup_dt >= datetime(2022, 11, 1):
            plan_p = [0.10, 0.05, 0.32, 0.35, 0.18]
        else:
            plan_p = [0.15, 0.18, 0.00, 0.42, 0.25]
        plan_id = int(np.random.choice(df_plans['plan_id'].values, p=plan_p))
        
        dev_id = int(np.random.choice(df_devices['device_id'].values, p=df_devices['stream_share_pct'].values / 100.0))
        
        tenure_months = max(1, (end_date.year - signup_dt.year) * 12 + (end_date.month - signup_dt.month))
        is_churned = 1 if np.random.rand() < min(0.40, tenure_months * 0.015) else 0
        
        if is_churned:
            churn_days = np.random.randint(30, max(31, int((end_date - signup_dt).days)))
            churn_dt = signup_dt + timedelta(days=churn_days)
            churn_date_key = int(churn_dt.strftime('%Y%m%d'))
            sub_status = 'Churned'
            active_months = max(1, (churn_dt.year - signup_dt.year) * 12 + (churn_dt.month - signup_dt.month))
        else:
            churn_date_key = None
            sub_status = 'Active'
            active_months = tenure_months
            
        extra_members = 0
        if plan_id in [4, 5] and signup_dt >= datetime(2023, 5, 1) and sub_status == 'Active':
            if np.random.rand() < 0.22:
                extra_members = np.random.choice([1, 2], p=[0.75, 0.25])
                
        base_price = df_plans[df_plans['plan_id'] == plan_id]['monthly_price_usd'].values[0]
        arpu = base_price + (extra_members * 7.99)
        ltv_usd = round(active_months * arpu, 2)
        
        subscribers.append({
            'subscriber_id': sub_id,
            'signup_date_key': signup_date_key,
            'signup_date': signup_dt.strftime('%Y-%m-%d'),
            'country_id': cid,
            'region_id': int(c_info['region_id']),
            'current_plan_id': plan_id,
            'primary_device_id': dev_id,
            'acquisition_channel': channels[i],
            'subscriber_status': sub_status,
            'churn_date_key': churn_date_key,
            'tenure_months': active_months,
            'extra_members_count': extra_members,
            'estimated_ltv_usd': ltv_usd
        })
        
    df_sub = pd.DataFrame(subscribers)
    df_sub.to_csv(os.path.join(data_dir, 'dim_subscriber.csv'), index=False)
    print(f"[+] [03] Created dim_subscriber.csv with {len(df_sub)} profiles")

    dates = pd.date_range(start='2021-01-01', end='2025-12-01', freq='MS')
    
    regional_base = {1: 73.9, 2: 66.7, 3: 37.5, 4: 25.6}
    regional_arpu = {1: 14.50, 2: 11.20, 3: 7.60, 4: 9.80}

    snapshots = []
    
    for rid in [1, 2, 3, 4]:
        curr_subs = regional_base[rid]
        curr_arpu = regional_arpu[rid]
        
        for d in dates:
            month_str = d.strftime('%Y-%m')
            date_key = int(d.strftime('%Y%m01'))
            year = d.year
            month = d.month
            
            growth_rate = 0.012
            if year == 2022 and month in [1, 2, 3, 4, 5, 6]:
                growth_rate = -0.002 if rid in [1, 2] else 0.003
            elif year == 2023 and month in [5, 6, 7, 8, 9, 10, 11, 12]:
                growth_rate = 0.024
            elif year >= 2024:
                growth_rate = 0.015 if rid in [3, 4] else 0.011
                
            if month in [11, 12]:
                growth_rate += 0.006
            elif month in [4, 5]:
                growth_rate -= 0.004
                
            if year == 2022 and month == 1:
                curr_arpu *= 1.05
            elif year == 2023 and month == 10:
                curr_arpu *= 1.06
            elif year == 2024 and month == 11:
                curr_arpu *= 1.04
                
            paid_start = curr_subs
            churn_rate = 0.021 + np.random.normal(0, 0.002)
            churn_subs = paid_start * churn_rate
            gross_adds = paid_start * (churn_rate + growth_rate)
            net_adds = gross_adds - churn_subs
            paid_end = paid_start + net_adds
            
            ad_tier_share = 0.0
            if d >= datetime(2022, 11, 1):
                months_since_ad = (year - 2022) * 12 + (month - 11) + 1
                ad_tier_share = min(0.38, 0.04 + months_since_ad * 0.011)
                
            ad_subs_m = paid_end * ad_tier_share
            standard_subs_m = paid_end * (1 - ad_tier_share) * 0.55
            premium_subs_m = paid_end * (1 - ad_tier_share) * 0.35
            basic_mobile_subs_m = paid_end * (1 - ad_tier_share) * 0.10
            
            ad_rev_per_sub = 7.50 if rid in [1, 2] else 3.20
            sub_rev_m = (paid_end * curr_arpu)
            ad_rev_m = (ad_subs_m * ad_rev_per_sub) if d >= datetime(2022, 11, 1) else 0.0
            total_rev_m = sub_rev_m + ad_rev_m
            
            snapshots.append({
                'snapshot_date_key': date_key,
                'year_month': month_str,
                'region_id': rid,
                'paid_memberships_start_m': round(paid_start, 3),
                'gross_additions_m': round(gross_adds, 3),
                'churned_memberships_m': round(churn_subs, 3),
                'net_additions_m': round(net_adds, 3),
                'paid_memberships_end_m': round(paid_end, 3),
                'monthly_churn_rate_pct': round(churn_rate * 100, 2),
                'avg_revenue_per_membership_usd': round(curr_arpu, 2),
                'ad_supported_memberships_m': round(ad_subs_m, 3),
                'standard_memberships_m': round(standard_subs_m, 3),
                'premium_memberships_m': round(premium_subs_m, 3),
                'subscription_revenue_m_usd': round(sub_rev_m, 2),
                'advertising_revenue_m_usd': round(ad_rev_m, 2),
                'total_streaming_revenue_m_usd': round(total_rev_m, 2)
            })
            
            curr_subs = paid_end
            
    df_snap = pd.DataFrame(snapshots)
    df_snap.to_csv(os.path.join(data_dir, 'fact_subscriber_snapshots.csv'), index=False)
    print(f"[+] [03] Created fact_subscriber_snapshots.csv with {len(df_snap)} monthly rows")

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.abspath(__file__))
    generate_subscribers_and_snapshots(data_dir=os.path.join(base_dir, '..', 'data'))

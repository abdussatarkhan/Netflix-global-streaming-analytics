#!/usr/bin/env python3
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import numpy as np

def generate_financials_and_cohorts(data_dir='../data'):
    os.makedirs(data_dir, exist_ok=True)
    np.random.seed(303)

    df_snaps = pd.read_csv(os.path.join(data_dir, 'fact_subscriber_snapshots.csv'))
    grouped = df_snaps.groupby('year_month').agg({
        'subscription_revenue_m_usd': 'sum',
        'advertising_revenue_m_usd': 'sum',
        'total_streaming_revenue_m_usd': 'sum',
        'paid_memberships_end_m': 'sum'
    }).reset_index()

    financials = []
    for idx, row in grouped.iterrows():
        ym = row['year_month']
        year = int(ym.split('-')[0])
        month = int(ym.split('-')[1])
        date_key = int(f"{year}{month:02d}01")
        
        sub_rev = row['subscription_revenue_m_usd']
        ad_rev = row['advertising_revenue_m_usd']
        tot_rev = row['total_streaming_revenue_m_usd']
        
        amort_pct = 0.52 - ((year - 2021) * 0.024)
        content_amort = round(tot_rev * amort_pct, 2)
        
        tech_dev = round(tot_rev * 0.085, 2)
        mktg_pct = 0.095 if month in [10, 11, 12] else 0.078
        marketing = round(tot_rev * mktg_pct, 2)
        ga_exp = round(tot_rev * 0.045, 2)
        
        total_opex = content_amort + tech_dev + marketing + ga_exp
        operating_income = round(tot_rev - total_opex, 2)
        operating_margin = round((operating_income / tot_rev) * 100, 2)
        
        fcf_margin = 0.04 + ((year - 2021) * 0.045) + (0.03 if month == 12 else 0)
        fcf = round(tot_rev * fcf_margin * np.random.uniform(0.92, 1.08), 2)
        
        financials.append({
            'financial_date_key': date_key,
            'year_month': ym,
            'subscription_revenue_m_usd': round(sub_rev, 2),
            'advertising_revenue_m_usd': round(ad_rev, 2),
            'total_revenue_m_usd': round(tot_rev, 2),
            'content_amortization_m_usd': content_amort,
            'technology_development_m_usd': tech_dev,
            'marketing_expense_m_usd': marketing,
            'general_admin_expense_m_usd': ga_exp,
            'total_operating_expenses_m_usd': round(total_opex, 2),
            'operating_income_m_usd': operating_income,
            'operating_margin_pct': operating_margin,
            'free_cash_flow_m_usd': fcf
        })
        
    df_fin = pd.DataFrame(financials)
    df_fin.to_csv(os.path.join(data_dir, 'fact_financials_monthly.csv'), index=False)
    print(f"[+] [05] Created fact_financials_monthly.csv with {len(df_fin)} months")

    cohort_months = pd.date_range(start='2021-01-01', end='2025-12-01', freq='MS')
    cohort_rows = []
    
    for c_date in cohort_months:
        cohort_id = c_date.strftime('%Y-%m')
        initial_sub_size = int(np.random.normal(loc=3400000, scale=350000))
        
        for tenure in range(0, 25):
            eval_date = c_date + pd.DateOffset(months=tenure)
            if eval_date > pd.Timestamp('2025-12-01'):
                break
                
            if tenure == 0:
                ret_pct = 100.0
            else:
                decay = np.exp(-0.028 * tenure) * 0.92 + 0.05
                noise = np.random.normal(0, 0.004)
                ret_pct = round(float(decay + noise) * 100, 2)
                ret_pct = min(100.0, max(50.0, ret_pct))
                
            active_subs = int(initial_sub_size * (ret_pct / 100.0))
            
            cohort_rows.append({
                'cohort_signup_month': cohort_id,
                'tenure_month': tenure,
                'evaluation_month': eval_date.strftime('%Y-%m'),
                'initial_cohort_size': initial_sub_size,
                'retained_subscribers_count': active_subs,
                'retention_rate_pct': ret_pct
            })
            
    df_cohort = pd.DataFrame(cohort_rows)
    df_cohort.to_csv(os.path.join(data_dir, 'fact_cohort_retention.csv'), index=False)
    print(f"[+] [05] Created fact_cohort_retention.csv with {len(df_cohort)} cohort records")

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.abspath(__file__))
    generate_financials_and_cohorts(data_dir=os.path.join(base_dir, '..', 'data'))

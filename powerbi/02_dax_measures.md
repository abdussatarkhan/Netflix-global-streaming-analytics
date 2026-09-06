# Production DAX Measures Reference (35+ Measures)

Organized into 5 logical folders for clean enterprise semantic modeling.

---

## 1. Subscriber & Membership Dynamics

### [Paid Subscribers (EOP)]
```dax
[Paid Subscribers (EOP)] = 
SUM(fact_subscriber_snapshots[paid_memberships_end_m])
```

### [Gross Additions]
```dax
[Gross Additions] = 
SUM(fact_subscriber_snapshots[gross_additions_m])
```

### [Churned Subscribers]
```dax
[Churned Subscribers] = 
SUM(fact_subscriber_snapshots[churned_memberships_m])
```

### [Net Additions]
```dax
[Net Additions] = 
[Gross Additions] - [Churned Subscribers]
```

### [Monthly Churn Rate %]
```dax
[Monthly Churn Rate %] = 
DIVIDE([Churned Subscribers], SUM(fact_subscriber_snapshots[paid_memberships_start_m]), 0) * 100
```

### [Ad-Supported Subscribers (EOP)]
```dax
[Ad-Supported Subscribers (EOP)] = 
SUM(fact_subscriber_snapshots[ad_supported_memberships_m])
```

### [Ad-Tier Penetration %]
```dax
[Ad-Tier Penetration %] = 
DIVIDE([Ad-Supported Subscribers (EOP)], [Paid Subscribers (EOP)], 0) * 100
```

### [ARM (Average Revenue per Membership)]
```dax
[ARM (Average Revenue per Membership)] = 
AVERAGE(fact_subscriber_snapshots[avg_revenue_per_membership_usd])
```

---

## 2. Financial Performance & Profitability

### [Total Streaming Revenue]
```dax
[Total Streaming Revenue] = 
SUM(fact_financials_monthly[total_revenue_m_usd])
```

### [Subscription Revenue]
```dax
[Subscription Revenue] = 
SUM(fact_financials_monthly[subscription_revenue_m_usd])
```

### [Ad Revenue]
```dax
[Ad Revenue] = 
SUM(fact_financials_monthly[advertising_revenue_m_usd])
```

### [Ad Revenue Share %]
```dax
[Ad Revenue Share %] = 
DIVIDE([Ad Revenue], [Total Streaming Revenue], 0) * 100
```

### [Content Amortization Expense]
```dax
[Content Amortization Expense] = 
SUM(fact_financials_monthly[content_amortization_m_usd])
```

### [Operating Income (EBIT)]
```dax
[Operating Income (EBIT)] = 
SUM(fact_financials_monthly[operating_income_m_usd])
```

### [Operating Margin %]
```dax
[Operating Margin %] = 
DIVIDE([Operating Income (EBIT)], [Total Streaming Revenue], 0) * 100
```

### [Free Cash Flow (FCF)]
```dax
[Free Cash Flow (FCF)] = 
SUM(fact_financials_monthly[free_cash_flow_m_usd])
```

### [FCF Conversion %]
```dax
[FCF Conversion %] = 
DIVIDE([Free Cash Flow (FCF)], [Operating Income (EBIT)], 0) * 100
```

---

## 3. Time Intelligence & YoY Growth

### [Revenue YoY Growth %]
```dax
[Revenue YoY Growth %] = 
VAR PrevYearRev = CALCULATE([Total Streaming Revenue], SAMEPERIODLASTYEAR(dim_date[full_date]))
RETURN
DIVIDE([Total Streaming Revenue] - PrevYearRev, PrevYearRev, 0) * 100
```

### [Paid Subscribers YoY Growth %]
```dax
[Paid Subscribers YoY Growth %] = 
VAR PrevYearSubs = CALCULATE([Paid Subscribers (EOP)], SAMEPERIODLASTYEAR(dim_date[full_date]))
RETURN
DIVIDE([Paid Subscribers (EOP)] - PrevYearSubs, PrevYearSubs, 0) * 100
```

### [YTD Streaming Revenue]
```dax
[YTD Streaming Revenue] = 
TOTALYTD([Total Streaming Revenue], dim_date[full_date])
```

### [YTD Free Cash Flow]
```dax
[YTD Free Cash Flow] = 
TOTALYTD([Free Cash Flow (FCF)], dim_date[full_date])
```

---

## 4. Content Analytics & ROI

### [Total Hours Viewed (M)]
```dax
[Total Hours Viewed (M)] = 
SUM(fact_content_performance_monthly[monthly_hours_viewed_m])
```

### [Total Estimated Views (M)]
```dax
[Total Estimated Views (M)] = 
SUM(fact_content_performance_monthly[monthly_views_m])
```

### [Average Completion Rate %]
```dax
[Average Completion Rate %] = 
AVERAGE(fact_content_performance_monthly[completion_rate_pct])
```

### [Total Content Budget (M)]
```dax
[Total Content Budget (M)] = 
SUM(dim_content[production_budget_m_usd])
```

### [Content Cost per Viewing Hour ($)]
```dax
[Content Cost per Viewing Hour ($)] = 
DIVIDE([Total Content Budget (M)], [Total Hours Viewed (M)], 0)
```

### [Content ROI Multiplier]
```dax
[Content ROI Multiplier] = 
MAX(fact_content_performance_monthly[content_roi_multiplier])
```

### [Hours Viewed per Paid Subscriber]
```dax
[Hours Viewed per Paid Subscriber] = 
DIVIDE([Total Hours Viewed (M)] * 1000000, [Paid Subscribers (EOP)] * 1000000, 0)
```

---

## 5. Streaming Quality of Service (QoS) & Infrastructure

### [Average Daily Streaming Hours (M)]
```dax
[Average Daily Streaming Hours (M)] = 
AVERAGE(fact_daily_streaming[total_stream_hours_m])
```

### [Peak Concurrent Streams (M)]
```dax
[Peak Concurrent Streams (M)] = 
MAX(fact_daily_streaming[peak_concurrent_streams_m])
```

### [4K UHD Stream Share %]
```dax
[4K UHD Stream Share %] = 
AVERAGE(fact_daily_streaming[uhd_4k_share_pct])
```

### [Average Rebuffer Ratio %]
```dax
[Average Rebuffer Ratio %] = 
AVERAGE(fact_daily_streaming[rebuffer_ratio_pct])
```

### [Non-English Content Stream Share %]
```dax
[Non-English Content Stream Share %] = 
AVERAGE(fact_daily_streaming[non_english_stream_share_pct])
```

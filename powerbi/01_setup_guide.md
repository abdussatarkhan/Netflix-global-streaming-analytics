# Power BI Setup & Semantic Modeling Guide

This guide walks you through building the **Netflix Global Streaming & Content Performance Analytics** semantic model in Power BI Desktop from scratch.

---

## 1. Data Connection Options

### Option A: Connect directly to PostgreSQL Data Warehouse (Recommended)
1. Open **Power BI Desktop** → click **Get Data** → **PostgreSQL Database**.
2. **Server**: `localhost:5432` (or your host IP).
3. **Database**: `netflix_dw`.
4. **Data Connectivity mode**: Select **Import** (for best DAX performance and custom hierarchies).
5. In the Navigator, select all 6 Dimensions and 5 Facts (or select the pre-built `vw_*` views from `/sql/02_bi_views.sql`).

### Option B: Load directly from CSV files in `/data`
1. Open **Power BI Desktop** → **Get Data** → **Folder** (or individual **CSV** connectors).
2. Browse to the `/data` folder in this repository.
3. Load the following files:
   - `dim_date.csv`
   - `dim_region.csv`
   - `dim_country.csv`
   - `dim_plan.csv`
   - `dim_device.csv`
   - `dim_content.csv`
   - `dim_subscriber.csv`
   - `fact_subscriber_snapshots.csv`
   - `fact_content_performance_monthly.csv`
   - `fact_financials_monthly.csv`
   - `fact_cohort_retention.csv`
   - `fact_daily_streaming.csv`

---

## 2. Star Schema Relationships (Model View)

Switch to the **Model View** tab and configure 1-to-many (`1:*`) single-direction relationships:

| From Table (Dimension 1) | Dimension Key | To Table (Fact Many *) | Fact Foreign Key | Cross Filter | Cardinality |
|---|---|---|---|---|---|
| `dim_date` | `date_key` | `fact_financials_monthly` | `financial_date_key` | Single | 1 : * |
| `dim_date` | `date_key` | `fact_daily_streaming` | `date_key` | Single | 1 : * |
| `dim_region` | `region_id` | `fact_subscriber_snapshots` | `region_id` | Single | 1 : * |
| `dim_region` | `region_id` | `dim_country` | `region_id` | Single | 1 : * |
| `dim_content` | `content_id` | `fact_content_performance_monthly` | `content_id` | Single | 1 : * |
| `dim_country` | `country_id` | `dim_subscriber` | `country_id` | Single | 1 : * |
| `dim_plan` | `plan_id` | `dim_subscriber` | `current_plan_id` | Single | 1 : * |
| `dim_device` | `device_id` | `dim_subscriber` | `primary_device_id` | Single | 1 : * |

---

## 3. Date Table & Sorting Configuration

1. Right-click `dim_date` → **Mark as Date Table** → choose `full_date`.
2. Set Sort-By columns:
   - `month_name` → Sort by `month`
   - `year_quarter` → Sort by `year_quarter` (or `date_key`)
   - `year_month` → Sort by `year_month`

---

## 4. Import the Netflix Executive Theme

1. Go to the **View** ribbon tab → click the theme dropdown arrow → **Browse for themes**.
2. Select `powerbi/netflix_theme.json`.
3. This applies the Netflix dark cinematic palette, high-contrast typography, and accent colors.

---

## 5. Add DAX Measures

1. Create a dedicated measure holding table: **Home** → **Enter Data** → Name table `_Measures`.
2. Copy and paste the DAX formulas from `powerbi/02_dax_measures.md` into new measures.

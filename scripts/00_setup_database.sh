#!/usr/bin/env bash
# ==============================================================================
# 00_setup_database.sh
# End-to-end PostgreSQL Data Warehouse Initialization & Ingestion Script
# Usage: ./scripts/00_setup_database.sh [DB_NAME] [DB_USER] [DB_HOST] [DB_PORT]
# ==============================================================================

set -e

DB_NAME=${1:-netflix_dw}
DB_USER=${2:-postgres}
DB_HOST=${3:-localhost}
DB_PORT=${4:-5432}

echo "======================================================================"
echo "🎬 Initializing Netflix Streaming Performance Analytics Warehouse"
echo "Target Database : $DB_NAME"
echo "Database User   : $DB_USER"
echo "Host & Port     : $DB_HOST:$DB_PORT"
echo "======================================================================"

# 1. Create Database if not exists
echo "[1/4] Creating database '$DB_NAME'..."
psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -c "CREATE DATABASE $DB_NAME WITH OWNER = $DB_USER ENCODING = 'UTF8';"

# 2. Execute DDL Schema
echo "[2/4] Executing star schema DDL (sql/01_schema.sql)..."
psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -f sql/01_schema.sql

# 3. Ingest CSV Data Files
echo "[3/4] Ingesting dimension and fact CSV datasets..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/../data"

psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -c "\copy dim_date FROM '$DATA_DIR/dim_date.csv' WITH (FORMAT csv, HEADER true);"
psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -c "\copy dim_region FROM '$DATA_DIR/dim_region.csv' WITH (FORMAT csv, HEADER true);"
psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -c "\copy dim_country FROM '$DATA_DIR/dim_country.csv' WITH (FORMAT csv, HEADER true);"
psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -c "\copy dim_plan FROM '$DATA_DIR/dim_plan.csv' WITH (FORMAT csv, HEADER true);"
psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -c "\copy dim_device FROM '$DATA_DIR/dim_device.csv' WITH (FORMAT csv, HEADER true);"
psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -c "\copy dim_content FROM '$DATA_DIR/dim_content.csv' WITH (FORMAT csv, HEADER true);"
psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -c "\copy dim_subscriber FROM '$DATA_DIR/dim_subscriber.csv' WITH (FORMAT csv, HEADER true);"
psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -c "\copy fact_subscriber_snapshots FROM '$DATA_DIR/fact_subscriber_snapshots.csv' WITH (FORMAT csv, HEADER true);"
psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -c "\copy fact_content_performance_monthly FROM '$DATA_DIR/fact_content_performance_monthly.csv' WITH (FORMAT csv, HEADER true);"
psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -c "\copy fact_financials_monthly FROM '$DATA_DIR/fact_financials_monthly.csv' WITH (FORMAT csv, HEADER true);"
psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -c "\copy fact_cohort_retention FROM '$DATA_DIR/fact_cohort_retention.csv' WITH (FORMAT csv, HEADER true);"
psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -c "\copy fact_daily_streaming FROM '$DATA_DIR/fact_daily_streaming.csv' WITH (FORMAT csv, HEADER true);"

# 4. Create Analytical Views
echo "[4/4] Creating BI analytical views (sql/02_bi_views.sql)..."
psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -f sql/02_bi_views.sql

echo "======================================================================"
echo "✅ Database setup complete! Connected successfully to $DB_NAME"
echo "======================================================================"

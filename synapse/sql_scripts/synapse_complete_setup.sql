-- ============================================================
-- UK Traffic Intelligence — Synapse Complete Setup Script
-- ============================================================
-- Workspace: syn-bd-training-uk
-- Pool: Built-in (serverless)
-- Storage: subiradls2026 (ADLS Gen2)
--
-- HOW TO RUN:
-- 1. Open Synapse Studio → Develop → + SQL script
-- 2. Connect to: Built-in | Database: master
-- 3. Run PART 1 (create database)
-- 4. Switch database dropdown to: uk_traffic_db
-- 5. Run PART 2-6 one by one (highlight each block → Run)
--
-- This script covers BOTH batch and streaming pipelines.
-- ============================================================


-- ============================================================
-- PART 1: Create Database
-- (Run with database = master)
-- ============================================================

CREATE DATABASE uk_traffic_db;


-- ============================================================
-- PART 2: Create Master Key & Credentials
-- (Switch database to uk_traffic_db before running)
-- ============================================================

CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'Str0ngP@ssw0rd!2026';
GO

-- SAS token from: Azure Portal → subiradls2026
-- → Security + networking → Shared access signature
-- Settings: Blob ✓, Container ✓, Object ✓, Read ✓, List ✓
CREATE DATABASE SCOPED CREDENTIAL StorageCredential
WITH IDENTITY = 'SHARED ACCESS SIGNATURE',
SECRET = '<PASTE_YOUR_SAS_TOKEN_HERE>';
GO


-- ============================================================
-- PART 3: Create Data Sources
-- One for batch Gold, one for streaming Gold
-- ============================================================

-- Batch Gold data source
CREATE EXTERNAL DATA SOURCE GoldDataLake
WITH (
    LOCATION = 'abfss://gold@subiradls2026.dfs.core.windows.net/',
    CREDENTIAL = StorageCredential
);
GO

-- Streaming Gold data source
CREATE EXTERNAL DATA SOURCE StreamingGoldDataLake
WITH (
    LOCATION = 'abfss://gold@subiradls2026.dfs.core.windows.net/streaming/',
    CREDENTIAL = StorageCredential
);
GO


-- ============================================================
-- PART 4: BATCH Views (8 views)
-- Source: UK DfT Road Traffic API
-- Pipeline: ADF Copy → Databricks (Bronze → Silver → Gold)
-- ============================================================

-- Fact: Traffic Volume Summary by Region, Road Type, Year
-- Columns: region_name, road_type, year, total_cars, total_buses,
--          total_lgvs, total_hgvs, total_cycles, total_motorcycles,
--          total_motor_vehicles, total_all_vehicles, count_points_observed,
--          avg_hgv_pct, freight_vehicles, green_transport_index,
--          prev_year_vehicles, yoy_change_pct
CREATE OR ALTER VIEW vw_traffic_summary AS
SELECT * FROM OPENROWSET(
    BULK 'fact_traffic_summary/**',
    DATA_SOURCE = 'GoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- Fact: CO2 Emissions Estimate by Region, Road Type, Year
-- Columns: region_name, road_type, year, total_co2_tonnes,
--          car_co2_tonnes, hgv_co2_tonnes, total_vehicle_count,
--          co2_per_vehicle_kg
CREATE OR ALTER VIEW vw_co2_emissions AS
SELECT * FROM OPENROWSET(
    BULK 'fact_co2_emissions/**',
    DATA_SOURCE = 'GoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- Fact: Vehicle Mix & Green Transport Index by Region, Year
-- Columns: region_name, year, cycles, motorcycles, cars, buses,
--          lgvs, hgvs, total, car_share_pct, cycle_share_pct,
--          hgv_share_pct, bus_share_pct, green_transport_index,
--          prev_green_index, green_index_change
CREATE OR ALTER VIEW vw_vehicle_mix AS
SELECT * FROM OPENROWSET(
    BULK 'fact_vehicle_mix/**',
    DATA_SOURCE = 'GoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- Fact: Road Category Analysis
-- Columns: region_name, road_class, road_name, year,
--          total_motor_vehicles, total_hgvs, total_cycles,
--          avg_link_length_km, count_points, vehicles_per_km
CREATE OR ALTER VIEW vw_road_analysis AS
SELECT * FROM OPENROWSET(
    BULK 'fact_road_analysis/**',
    DATA_SOURCE = 'GoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- Fact: COVID Impact & Recovery (2019 baseline, join-based)
-- Columns: region_name, road_type, year, total_vehicles,
--          total_cycles, total_hgvs, baseline_2019,
--          recovery_pct, yoy_change
CREATE OR ALTER VIEW vw_covid_impact AS
SELECT * FROM OPENROWSET(
    BULK 'fact_covid_impact/**',
    DATA_SOURCE = 'GoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- Fact: Top Busiest Roads with Map Coordinates (2023 data)
-- Columns: region_name, road_name, road_type, latitude,
--          longitude, total_vehicles, total_hgvs, total_cycles, rank
CREATE OR ALTER VIEW vw_busiest_roads AS
SELECT * FROM OPENROWSET(
    BULK 'fact_busiest_roads/**',
    DATA_SOURCE = 'GoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- Dimension: Count Point Locations
-- Columns: count_point_id, road_name, road_type, road_category,
--          region_name, local_authority_name, latitude, longitude, road_class
CREATE OR ALTER VIEW vw_dim_location AS
SELECT * FROM OPENROWSET(
    BULK 'dim_location/**',
    DATA_SOURCE = 'GoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- Dimension: Date (2000-2025)
-- Columns: date, year, month, quarter, day_name, month_name, is_weekend
CREATE OR ALTER VIEW vw_dim_date AS
SELECT * FROM OPENROWSET(
    BULK 'dim_date/**',
    DATA_SOURCE = 'GoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO


-- ============================================================
-- PART 5: STREAMING Views (4 views)
-- Source: UK Carbon Intensity API (real-time)
-- Pipeline: Producer → Event Hub → Databricks → Gold
-- ============================================================

-- National Carbon Intensity Timeline
-- Columns: data_timestamp, period_from, period_to, forecast,
--          actual, intensity_index, forecast_vs_actual, intensity_category
CREATE OR ALTER VIEW vw_stream_national_intensity AS
SELECT * FROM OPENROWSET(
    BULK 'gold_national_intensity/**',
    DATA_SOURCE = 'StreamingGoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- Energy Generation Mix (solar, wind, gas, nuclear, etc.)
-- Columns: data_timestamp, period_from, period_to, fuel_type,
--          fuel_percentage, energy_category
CREATE OR ALTER VIEW vw_stream_generation_mix AS
SELECT * FROM OPENROWSET(
    BULK 'gold_generation_mix/**',
    DATA_SOURCE = 'StreamingGoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- Regional Carbon Intensity Comparison (17 UK regions)
-- Columns: data_timestamp, period_from, period_to, region_id,
--          region_name, dno_region, forecast, intensity_index,
--          intensity_category
CREATE OR ALTER VIEW vw_stream_regional_intensity AS
SELECT * FROM OPENROWSET(
    BULK 'gold_regional_intensity/**',
    DATA_SOURCE = 'StreamingGoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- Renewable vs Fossil Fuel Summary
-- Columns: period_from, energy_category, total_percentage
CREATE OR ALTER VIEW vw_stream_renewable_summary AS
SELECT * FROM OPENROWSET(
    BULK 'gold_renewable_summary/**',
    DATA_SOURCE = 'StreamingGoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO


-- ============================================================
-- PART 6: Test All Views
-- ============================================================

-- Batch views
SELECT 'vw_traffic_summary' AS view_name, COUNT(*) AS rows FROM vw_traffic_summary
UNION ALL SELECT 'vw_co2_emissions', COUNT(*) FROM vw_co2_emissions
UNION ALL SELECT 'vw_vehicle_mix', COUNT(*) FROM vw_vehicle_mix
UNION ALL SELECT 'vw_road_analysis', COUNT(*) FROM vw_road_analysis
UNION ALL SELECT 'vw_covid_impact', COUNT(*) FROM vw_covid_impact
UNION ALL SELECT 'vw_busiest_roads', COUNT(*) FROM vw_busiest_roads
UNION ALL SELECT 'vw_dim_location', COUNT(*) FROM vw_dim_location
UNION ALL SELECT 'vw_dim_date', COUNT(*) FROM vw_dim_date;

-- Streaming views
SELECT 'vw_stream_national_intensity' AS view_name, COUNT(*) AS rows FROM vw_stream_national_intensity
UNION ALL SELECT 'vw_stream_generation_mix', COUNT(*) FROM vw_stream_generation_mix
UNION ALL SELECT 'vw_stream_regional_intensity', COUNT(*) FROM vw_stream_regional_intensity
UNION ALL SELECT 'vw_stream_renewable_summary', COUNT(*) FROM vw_stream_renewable_summary;

-- Verify year column in batch tables
SELECT TOP 5 year, region_name, total_all_vehicles FROM vw_traffic_summary ORDER BY region_name, year;

-- Verify streaming data
SELECT * FROM vw_stream_generation_mix ORDER BY fuel_type;


-- ============================================================
-- PART 7: Power BI Connection Details
-- ============================================================
-- Server: syn-bd-training-uk-ondemand.sql.azuresynapse.net
-- Database: uk_traffic_db
-- Authentication: Organizational account (Microsoft sign-in)
--
-- Batch Dashboard: Import 8 batch views
-- Streaming Dashboard: Import 4 streaming views
--
-- Batch Data Model (Star Schema):
--   vw_dim_date (year) → vw_traffic_summary (year)
--   vw_dim_date (year) → vw_co2_emissions (year)
--   vw_dim_date (year) → vw_vehicle_mix (year)
--   vw_dim_date (year) → vw_covid_impact (year)
--   vw_dim_date (year) → vw_road_analysis (year)
--
-- Streaming: No relationships needed (standalone tables)


-- ============================================================
-- CLEANUP (if needed — run in this order)
-- ============================================================
/*
-- Drop streaming views
DROP VIEW IF EXISTS vw_stream_national_intensity;
DROP VIEW IF EXISTS vw_stream_generation_mix;
DROP VIEW IF EXISTS vw_stream_regional_intensity;
DROP VIEW IF EXISTS vw_stream_renewable_summary;

-- Drop batch views
DROP VIEW IF EXISTS vw_traffic_summary;
DROP VIEW IF EXISTS vw_co2_emissions;
DROP VIEW IF EXISTS vw_vehicle_mix;
DROP VIEW IF EXISTS vw_road_analysis;
DROP VIEW IF EXISTS vw_covid_impact;
DROP VIEW IF EXISTS vw_busiest_roads;
DROP VIEW IF EXISTS vw_dim_location;
DROP VIEW IF EXISTS vw_dim_date;

-- Drop data sources
DROP EXTERNAL DATA SOURCE StreamingGoldDataLake;
DROP EXTERNAL DATA SOURCE GoldDataLake;

-- Drop credential
DROP DATABASE SCOPED CREDENTIAL StorageCredential;
*/


-- ============================================================
-- RECREATE VIEWS (after Databricks Gold refresh)
-- ============================================================
/*
-- Batch: Drop and recreate to pick up schema changes
DROP VIEW vw_traffic_summary;
DROP VIEW vw_co2_emissions;
DROP VIEW vw_road_analysis;
DROP VIEW vw_covid_impact;
GO

CREATE OR ALTER VIEW vw_traffic_summary AS
SELECT * FROM OPENROWSET(BULK 'fact_traffic_summary/**', DATA_SOURCE = 'GoldDataLake', FORMAT = 'PARQUET') AS r;
GO
CREATE OR ALTER VIEW vw_co2_emissions AS
SELECT * FROM OPENROWSET(BULK 'fact_co2_emissions/**', DATA_SOURCE = 'GoldDataLake', FORMAT = 'PARQUET') AS r;
GO
CREATE OR ALTER VIEW vw_road_analysis AS
SELECT * FROM OPENROWSET(BULK 'fact_road_analysis/**', DATA_SOURCE = 'GoldDataLake', FORMAT = 'PARQUET') AS r;
GO
CREATE OR ALTER VIEW vw_covid_impact AS
SELECT * FROM OPENROWSET(BULK 'fact_covid_impact/**', DATA_SOURCE = 'GoldDataLake', FORMAT = 'PARQUET') AS r;
GO

-- Streaming: Drop and recreate
DROP VIEW vw_stream_national_intensity;
DROP VIEW vw_stream_generation_mix;
DROP VIEW vw_stream_regional_intensity;
DROP VIEW vw_stream_renewable_summary;
GO

CREATE OR ALTER VIEW vw_stream_national_intensity AS
SELECT * FROM OPENROWSET(BULK 'gold_national_intensity/**', DATA_SOURCE = 'StreamingGoldDataLake', FORMAT = 'PARQUET') AS r;
GO
CREATE OR ALTER VIEW vw_stream_generation_mix AS
SELECT * FROM OPENROWSET(BULK 'gold_generation_mix/**', DATA_SOURCE = 'StreamingGoldDataLake', FORMAT = 'PARQUET') AS r;
GO
CREATE OR ALTER VIEW vw_stream_regional_intensity AS
SELECT * FROM OPENROWSET(BULK 'gold_regional_intensity/**', DATA_SOURCE = 'StreamingGoldDataLake', FORMAT = 'PARQUET') AS r;
GO
CREATE OR ALTER VIEW vw_stream_renewable_summary AS
SELECT * FROM OPENROWSET(BULK 'gold_renewable_summary/**', DATA_SOURCE = 'StreamingGoldDataLake', FORMAT = 'PARQUET') AS r;
GO
*/

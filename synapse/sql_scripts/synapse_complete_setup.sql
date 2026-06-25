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
-- 3. Run Step 1 (create database)
-- 4. Switch database dropdown to: uk_traffic_db
-- 5. Run Steps 2-5 one by one (highlight each block → Run)
--
-- IMPORTANT NOTES:
-- - Gold tables are written WITHOUT partitionBy to preserve year column
-- - Views use OPENROWSET with /** wildcard to read all Parquet files
-- - SAS token must be generated from Azure Portal → subiradls2026
--   → Security + networking → Shared access signature
-- ============================================================


-- ============================================================
-- STEP 1: Create Database
-- (Run with database = master)
-- ============================================================

CREATE DATABASE uk_traffic_db;


-- ============================================================
-- STEP 2: Create Master Key
-- (Switch database to uk_traffic_db before running)
-- ============================================================

CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'Str0ngP@ssw0rd!2026';


-- ============================================================
-- STEP 3: Create Credential & Data Source
-- Generate SAS token from:
--   Azure Portal → subiradls2026 → Security + networking
--   → Shared access signature
--   Settings: Blob ✓, Container ✓, Object ✓, Read ✓, List ✓
--   Copy SAS token (remove leading '?' if present)
-- ============================================================

CREATE DATABASE SCOPED CREDENTIAL StorageCredential
WITH IDENTITY = 'SHARED ACCESS SIGNATURE',
SECRET = '<PASTE_YOUR_SAS_TOKEN_HERE>';
GO

CREATE EXTERNAL DATA SOURCE GoldDataLake
WITH (
    LOCATION = 'abfss://gold@subiradls2026.dfs.core.windows.net/',
    CREDENTIAL = StorageCredential
);
GO


-- ============================================================
-- STEP 4: Create Views on Gold Layer Tables
-- These views are consumed by Power BI
--
-- Gold Tables (8 total):
--   Fact Tables: fact_traffic_summary, fact_co2_emissions,
--                fact_vehicle_mix, fact_road_analysis,
--                fact_covid_impact, fact_busiest_roads
--   Dimension Tables: dim_location, dim_date
--
-- All fact tables contain 'year' column for Power BI filtering
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

-- Fact: Road Category Analysis (vehicles per km, HGV share)
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

-- Fact: COVID Impact & Recovery (2019 baseline comparison)
-- Columns: region_name, road_type, year, total_vehicles,
--          total_cycles, total_hgvs, baseline_2019,
--          recovery_pct, yoy_change
-- Note: Uses join-based baseline (not window function)
CREATE OR ALTER VIEW vw_covid_impact AS
SELECT * FROM OPENROWSET(
    BULK 'fact_covid_impact/**',
    DATA_SOURCE = 'GoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- Fact: Top 500 Busiest Roads with Map Coordinates (2023 data)
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
--          region_name, local_authority_name, latitude, longitude,
--          road_class
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
-- STEP 5: Test All Views
-- ============================================================

-- Row counts
SELECT 'vw_traffic_summary' AS view_name, COUNT(*) AS rows FROM vw_traffic_summary
UNION ALL SELECT 'vw_co2_emissions', COUNT(*) FROM vw_co2_emissions
UNION ALL SELECT 'vw_vehicle_mix', COUNT(*) FROM vw_vehicle_mix
UNION ALL SELECT 'vw_road_analysis', COUNT(*) FROM vw_road_analysis
UNION ALL SELECT 'vw_covid_impact', COUNT(*) FROM vw_covid_impact
UNION ALL SELECT 'vw_busiest_roads', COUNT(*) FROM vw_busiest_roads
UNION ALL SELECT 'vw_dim_location', COUNT(*) FROM vw_dim_location
UNION ALL SELECT 'vw_dim_date', COUNT(*) FROM vw_dim_date;

-- Verify year column in key tables
SELECT TOP 5 year, region_name, total_all_vehicles FROM vw_traffic_summary ORDER BY region_name, year;
SELECT TOP 5 year, region_name, total_co2_tonnes FROM vw_co2_emissions ORDER BY region_name, year;
SELECT TOP 5 year, region_name, recovery_pct FROM vw_covid_impact ORDER BY region_name, year;


-- ============================================================
-- STEP 6: Power BI Connection Details
-- ============================================================
-- Server: syn-bd-training-uk-ondemand.sql.azuresynapse.net
-- Database: uk_traffic_db
-- Authentication: Organizational account (Microsoft sign-in)
-- Import all 8 views
--
-- Data Model (Star Schema):
--   vw_dim_date (year) → vw_traffic_summary (year)
--   vw_dim_date (year) → vw_co2_emissions (year)
--   vw_dim_date (year) → vw_vehicle_mix (year)
--   vw_dim_date (year) → vw_covid_impact (year)
--   vw_dim_date (year) → vw_road_analysis (year)


-- ============================================================
-- CLEANUP (if needed — run in this order)
-- ============================================================
/*
DROP VIEW IF EXISTS vw_traffic_summary;
DROP VIEW IF EXISTS vw_co2_emissions;
DROP VIEW IF EXISTS vw_vehicle_mix;
DROP VIEW IF EXISTS vw_road_analysis;
DROP VIEW IF EXISTS vw_covid_impact;
DROP VIEW IF EXISTS vw_busiest_roads;
DROP VIEW IF EXISTS vw_dim_location;
DROP VIEW IF EXISTS vw_dim_date;

DROP EXTERNAL DATA SOURCE GoldDataLake;

DROP DATABASE SCOPED CREDENTIAL StorageCredential;
*/


-- ============================================================
-- RECREATE VIEWS (if Gold tables are updated in Databricks)
-- Run this after any Gold layer refresh to pick up schema changes
-- ============================================================
/*
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
*/

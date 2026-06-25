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
-- ============================================================

-- Fact: Traffic Volume Summary by Region, Road Type, Year
CREATE OR ALTER VIEW vw_traffic_summary AS
SELECT * FROM OPENROWSET(
    BULK 'fact_traffic_summary/**',
    DATA_SOURCE = 'GoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- Fact: CO2 Emissions Estimate by Region, Road Type, Year
CREATE OR ALTER VIEW vw_co2_emissions AS
SELECT * FROM OPENROWSET(
    BULK 'fact_co2_emissions/**',
    DATA_SOURCE = 'GoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- Fact: Vehicle Mix & Green Transport Index by Region, Year
CREATE OR ALTER VIEW vw_vehicle_mix AS
SELECT * FROM OPENROWSET(
    BULK 'fact_vehicle_mix/**',
    DATA_SOURCE = 'GoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- Fact: Road Category Analysis (vehicles per km, HGV share)
CREATE OR ALTER VIEW vw_road_analysis AS
SELECT * FROM OPENROWSET(
    BULK 'fact_road_analysis/**',
    DATA_SOURCE = 'GoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- Fact: COVID Impact & Recovery (2019 baseline comparison)
CREATE OR ALTER VIEW vw_covid_impact AS
SELECT * FROM OPENROWSET(
    BULK 'fact_covid_impact/**',
    DATA_SOURCE = 'GoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- Fact: Top 500 Busiest Roads with Map Coordinates
CREATE OR ALTER VIEW vw_busiest_roads AS
SELECT * FROM OPENROWSET(
    BULK 'fact_busiest_roads/**',
    DATA_SOURCE = 'GoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- Dimension: Count Point Locations
CREATE OR ALTER VIEW vw_dim_location AS
SELECT * FROM OPENROWSET(
    BULK 'dim_location/**',
    DATA_SOURCE = 'GoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- Dimension: Date
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

-- Preview traffic summary
SELECT * FROM vw_traffic_summary ORDER BY region_name, year;

-- Preview CO2 emissions
SELECT * FROM vw_co2_emissions ORDER BY region_name, year;

-- Preview COVID recovery
SELECT * FROM vw_covid_impact ORDER BY region_name, year;

-- Preview busiest roads
SELECT * FROM vw_busiest_roads ORDER BY total_vehicles DESC;


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

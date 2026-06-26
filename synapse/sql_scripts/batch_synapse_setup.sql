-- ============================================================
-- BATCH Pipeline — Synapse Setup Script
-- ============================================================
-- Source: UK DfT Road Traffic API (roadtraffic.dft.gov.uk)
-- Pipeline: ADF Copy → Databricks (Bronze → Silver → Gold) → Synapse
-- Database: uk_traffic_db
-- ============================================================


-- STEP 1: Create Database (run on master)
CREATE DATABASE uk_traffic_db;


-- STEP 2: Create Master Key (switch to uk_traffic_db)
CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'Str0ngP@ssw0rd!2026';
GO


-- STEP 3: Create Credential with SAS token
-- Generate from: Azure Portal → subiradls2026 → Shared access signature
CREATE DATABASE SCOPED CREDENTIAL StorageCredential
WITH IDENTITY = 'SHARED ACCESS SIGNATURE',
SECRET = '<PASTE_YOUR_SAS_TOKEN_HERE>';
GO


-- STEP 4: Create Data Source for Batch Gold
CREATE EXTERNAL DATA SOURCE GoldDataLake
WITH (
    LOCATION = 'abfss://gold@subiradls2026.dfs.core.windows.net/',
    CREDENTIAL = StorageCredential
);
GO


-- STEP 5: Create 8 Batch Views

-- Fact: Traffic Volume Summary (286 rows)
CREATE OR ALTER VIEW vw_traffic_summary AS
SELECT * FROM OPENROWSET(
    BULK 'fact_traffic_summary/**',
    DATA_SOURCE = 'GoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- Fact: CO2 Emissions Estimate (286 rows)
CREATE OR ALTER VIEW vw_co2_emissions AS
SELECT * FROM OPENROWSET(
    BULK 'fact_co2_emissions/**',
    DATA_SOURCE = 'GoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- Fact: Vehicle Mix & Green Transport Index (286 rows)
CREATE OR ALTER VIEW vw_vehicle_mix AS
SELECT * FROM OPENROWSET(
    BULK 'fact_vehicle_mix/**',
    DATA_SOURCE = 'GoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- Fact: Road Category Analysis (1,704 rows)
CREATE OR ALTER VIEW vw_road_analysis AS
SELECT * FROM OPENROWSET(
    BULK 'fact_road_analysis/**',
    DATA_SOURCE = 'GoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- Fact: COVID Impact & Recovery (77 rows)
CREATE OR ALTER VIEW vw_covid_impact AS
SELECT * FROM OPENROWSET(
    BULK 'fact_covid_impact/**',
    DATA_SOURCE = 'GoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- Fact: Top Busiest Roads (95 rows)
CREATE OR ALTER VIEW vw_busiest_roads AS
SELECT * FROM OPENROWSET(
    BULK 'fact_busiest_roads/**',
    DATA_SOURCE = 'GoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- Dimension: Count Point Locations (123 rows)
CREATE OR ALTER VIEW vw_dim_location AS
SELECT * FROM OPENROWSET(
    BULK 'dim_location/**',
    DATA_SOURCE = 'GoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- Dimension: Date 2000-2025 (9,497 rows)
CREATE OR ALTER VIEW vw_dim_date AS
SELECT * FROM OPENROWSET(
    BULK 'dim_date/**',
    DATA_SOURCE = 'GoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO


-- STEP 6: Test Batch Views
SELECT 'vw_traffic_summary' AS view_name, COUNT(*) AS rows FROM vw_traffic_summary
UNION ALL SELECT 'vw_co2_emissions', COUNT(*) FROM vw_co2_emissions
UNION ALL SELECT 'vw_vehicle_mix', COUNT(*) FROM vw_vehicle_mix
UNION ALL SELECT 'vw_road_analysis', COUNT(*) FROM vw_road_analysis
UNION ALL SELECT 'vw_covid_impact', COUNT(*) FROM vw_covid_impact
UNION ALL SELECT 'vw_busiest_roads', COUNT(*) FROM vw_busiest_roads
UNION ALL SELECT 'vw_dim_location', COUNT(*) FROM vw_dim_location
UNION ALL SELECT 'vw_dim_date', COUNT(*) FROM vw_dim_date;

-- Verify year column
SELECT TOP 5 year, region_name, total_all_vehicles FROM vw_traffic_summary ORDER BY region_name, year;


-- Power BI Connection:
-- Server: syn-bd-training-uk-ondemand.sql.azuresynapse.net
-- Database: uk_traffic_db
-- Data Model: vw_dim_date (year) → all fact tables (year)

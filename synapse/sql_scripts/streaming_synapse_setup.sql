-- ============================================================
-- STREAMING Pipeline — Synapse Setup Script
-- ============================================================
-- Source: UK Carbon Intensity API (api.carbonintensity.org.uk)
-- Pipeline: Producer → Event Hub → Databricks (Bronze → Silver → Gold) → Synapse
-- Database: uk_traffic_db (same as batch)
--
-- PREREQUISITE: Run batch_synapse_setup.sql first
-- (creates database, master key, and credential)
-- ============================================================


-- STEP 1: Create Data Source for Streaming Gold
-- Uses same credential as batch (StorageCredential)
CREATE EXTERNAL DATA SOURCE StreamingGoldDataLake
WITH (
    LOCATION = 'abfss://gold@subiradls2026.dfs.core.windows.net/streaming/',
    CREDENTIAL = StorageCredential
);
GO


-- STEP 2: Create 4 Streaming Views

-- National Carbon Intensity Timeline
-- Shows real-time CO2 intensity (gCO2/kWh) with forecast vs actual
CREATE OR ALTER VIEW vw_stream_national_intensity AS
SELECT * FROM OPENROWSET(
    BULK 'gold_national_intensity/**',
    DATA_SOURCE = 'StreamingGoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- Energy Generation Mix (solar, wind, gas, nuclear, etc.)
-- Shows what percentage of UK energy comes from each fuel type
CREATE OR ALTER VIEW vw_stream_generation_mix AS
SELECT * FROM OPENROWSET(
    BULK 'gold_generation_mix/**',
    DATA_SOURCE = 'StreamingGoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- Regional Carbon Intensity Comparison (17 UK regions)
-- Compares carbon intensity across UK regions
CREATE OR ALTER VIEW vw_stream_regional_intensity AS
SELECT * FROM OPENROWSET(
    BULK 'gold_regional_intensity/**',
    DATA_SOURCE = 'StreamingGoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- Renewable vs Fossil Fuel Summary
-- Aggregates fuel types into Renewable, Fossil Fuel, Nuclear, Other
CREATE OR ALTER VIEW vw_stream_renewable_summary AS
SELECT * FROM OPENROWSET(
    BULK 'gold_renewable_summary/**',
    DATA_SOURCE = 'StreamingGoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO


-- STEP 3: Test Streaming Views
SELECT 'vw_stream_national_intensity' AS view_name, COUNT(*) AS rows FROM vw_stream_national_intensity
UNION ALL SELECT 'vw_stream_generation_mix', COUNT(*) FROM vw_stream_generation_mix
UNION ALL SELECT 'vw_stream_regional_intensity', COUNT(*) FROM vw_stream_regional_intensity
UNION ALL SELECT 'vw_stream_renewable_summary', COUNT(*) FROM vw_stream_renewable_summary;

-- Preview generation mix
SELECT * FROM vw_stream_generation_mix ORDER BY fuel_type;

-- Preview regional intensity
SELECT region_name, forecast, intensity_index, intensity_category
FROM vw_stream_regional_intensity
ORDER BY forecast DESC;


-- Power BI Connection:
-- Server: syn-bd-training-uk-ondemand.sql.azuresynapse.net
-- Database: uk_traffic_db
-- No relationships needed for streaming tables (standalone)

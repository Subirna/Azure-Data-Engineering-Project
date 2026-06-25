-- ============================================================
-- Streaming Pipeline — Synapse Views for Power BI
-- ============================================================
-- Run on: Built-in (serverless) pool, database: uk_traffic_db
-- These views read from the streaming Gold tables in ADLS Gen2
-- ============================================================


-- Data source for streaming Gold (reuses same credential)
CREATE EXTERNAL DATA SOURCE StreamingGoldDataLake
WITH (
    LOCATION = 'abfss://gold@subiradls2026.dfs.core.windows.net/streaming/',
    CREDENTIAL = StorageCredential
);
GO


-- View: National Carbon Intensity Timeline
CREATE OR ALTER VIEW vw_stream_national_intensity AS
SELECT * FROM OPENROWSET(
    BULK 'gold_national_intensity/**',
    DATA_SOURCE = 'StreamingGoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- View: Energy Generation Mix (solar, wind, gas, nuclear, etc.)
CREATE OR ALTER VIEW vw_stream_generation_mix AS
SELECT * FROM OPENROWSET(
    BULK 'gold_generation_mix/**',
    DATA_SOURCE = 'StreamingGoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- View: Regional Carbon Intensity Comparison
CREATE OR ALTER VIEW vw_stream_regional_intensity AS
SELECT * FROM OPENROWSET(
    BULK 'gold_regional_intensity/**',
    DATA_SOURCE = 'StreamingGoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- View: Regional Energy Generation Mix
CREATE OR ALTER VIEW vw_stream_regional_generation AS
SELECT * FROM OPENROWSET(
    BULK 'gold_regional_generation/**',
    DATA_SOURCE = 'StreamingGoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO

-- View: Renewable vs Fossil Fuel Summary
CREATE OR ALTER VIEW vw_stream_renewable_summary AS
SELECT * FROM OPENROWSET(
    BULK 'gold_renewable_summary/**',
    DATA_SOURCE = 'StreamingGoldDataLake',
    FORMAT = 'PARQUET'
) AS r;
GO


-- Test queries
SELECT * FROM vw_stream_national_intensity ORDER BY period_from DESC;
SELECT * FROM vw_stream_generation_mix ORDER BY period_from DESC, fuel_type;
SELECT * FROM vw_stream_regional_intensity ORDER BY period_from DESC, region_name;

-- External tables pointing to Gold layer Delta tables in ADLS Gen2
-- These allow Synapse SQL to query Databricks Gold outputs directly

-- ============================================
-- Data Source & File Format
-- ============================================

CREATE EXTERNAL DATA SOURCE GoldDataLake
WITH (
    LOCATION = 'abfss://gold@uktrafficdldev.dfs.core.windows.net/',
    TYPE = HADOOP
);
GO

CREATE EXTERNAL FILE FORMAT DeltaParquetFormat
WITH (
    FORMAT_TYPE = PARQUET,
    DATA_COMPRESSION = 'org.apache.hadoop.io.compress.SnappyCodec'
);
GO

-- ============================================
-- Traffic Analysis Tables
-- ============================================

CREATE EXTERNAL TABLE [gold].[fact_daily_traffic] (
    count_point_id          INT,
    [year]                  INT,
    count_date              DATE,
    direction_of_travel     NVARCHAR(50),
    total_pedal_cycles      BIGINT,
    total_motorcycles       BIGINT,
    total_cars              BIGINT,
    total_buses             BIGINT,
    total_lgvs              BIGINT,
    total_hgvs              BIGINT,
    total_all_vehicles      BIGINT,
    avg_hgv_percentage      DECIMAL(5,2),
    hours_counted           INT,
    motorised_vehicles      BIGINT,
    active_travel_vehicles  BIGINT,
    freight_vehicles        BIGINT
)
WITH (
    LOCATION = '/traffic_analysis/fact_daily_traffic/',
    DATA_SOURCE = GoldDataLake,
    FILE_FORMAT = DeltaParquetFormat
);
GO

CREATE EXTERNAL TABLE [gold].[fact_hourly_peaks] (
    count_point_id      INT,
    [year]              INT,
    [hour]              INT,
    time_period         NVARCHAR(50),
    avg_vehicles        DECIMAL(10,2),
    max_vehicles        INT,
    min_vehicles        INT,
    avg_cars            DECIMAL(10,2),
    avg_hgvs            DECIMAL(10,2),
    observation_count   INT,
    congestion_index    DECIMAL(5,3)
)
WITH (
    LOCATION = '/traffic_analysis/fact_hourly_peaks/',
    DATA_SOURCE = GoldDataLake,
    FILE_FORMAT = DeltaParquetFormat
);
GO

CREATE EXTERNAL TABLE [gold].[fact_yoy_regional] (
    region_name             NVARCHAR(100),
    road_type               NVARCHAR(50),
    [year]                  INT,
    total_vehicles          BIGINT,
    total_cars              BIGINT,
    total_hgvs              BIGINT,
    total_cycles            BIGINT,
    count_points_observed   INT,
    prev_year_vehicles      BIGINT,
    yoy_change_pct          DECIMAL(5,2)
)
WITH (
    LOCATION = '/traffic_analysis/fact_yoy_regional/',
    DATA_SOURCE = GoldDataLake,
    FILE_FORMAT = DeltaParquetFormat
);
GO

CREATE EXTERNAL TABLE [gold].[dim_count_point] (
    count_point_id          INT,
    road_name               NVARCHAR(100),
    road_type               NVARCHAR(50),
    region_name             NVARCHAR(100),
    local_authority_name    NVARCHAR(100),
    latitude                DECIMAL(9,6),
    longitude               DECIMAL(9,6),
    road_category           NVARCHAR(50)
)
WITH (
    LOCATION = '/traffic_analysis/dim_count_point/',
    DATA_SOURCE = GoldDataLake,
    FILE_FORMAT = DeltaParquetFormat
);
GO

CREATE EXTERNAL TABLE [gold].[dim_date] (
    [date]          DATE,
    [year]          INT,
    [month]         INT,
    [day]           INT,
    [quarter]       INT,
    day_of_week     INT,
    day_name        NVARCHAR(20),
    month_name      NVARCHAR(20),
    is_weekend      BIT,
    fiscal_year     INT,
    fiscal_quarter  INT
)
WITH (
    LOCATION = '/traffic_analysis/dim_date/',
    DATA_SOURCE = GoldDataLake,
    FILE_FORMAT = DeltaParquetFormat
);
GO

-- ============================================
-- Road Safety Tables
-- ============================================

CREATE EXTERNAL TABLE [gold].[fact_accident_summary] (
    collision_year              INT,
    collision_month             INT,
    severity_label              NVARCHAR(20),
    weather_label               NVARCHAR(50),
    light_condition_label       NVARCHAR(50),
    is_urban                    BIT,
    speed_limit                 INT,
    total_collisions            INT,
    total_casualties            INT,
    total_vehicles_involved     INT,
    avg_casualties_per_collision DECIMAL(5,2),
    fatal_count                 INT,
    serious_count               INT,
    slight_count                INT,
    ksi_count                   INT,
    ksi_rate                    DECIMAL(5,2)
)
WITH (
    LOCATION = '/road_safety/fact_accident_summary/',
    DATA_SOURCE = GoldDataLake,
    FILE_FORMAT = DeltaParquetFormat
);
GO

CREATE EXTERNAL TABLE [gold].[fact_accident_hotspots] (
    lat_grid                DECIMAL(5,2),
    lon_grid                DECIMAL(5,2),
    collision_year          INT,
    total_incidents         INT,
    fatal_incidents         INT,
    serious_incidents       INT,
    total_casualties        INT,
    avg_speed_limit         DECIMAL(5,1),
    is_urban                BIT,
    severity_score          INT,
    hotspot_rank            INT
)
WITH (
    LOCATION = '/road_safety/fact_accident_hotspots/',
    DATA_SOURCE = GoldDataLake,
    FILE_FORMAT = DeltaParquetFormat
);
GO

-- ============================================
-- Environmental Tables
-- ============================================

CREATE EXTERNAL TABLE [gold].[fact_co2_emissions] (
    region_name             NVARCHAR(100),
    local_authority_name    NVARCHAR(100),
    road_type               NVARCHAR(50),
    [year]                  INT,
    total_co2_tonnes        DECIMAL(12,2),
    car_co2_tonnes          DECIMAL(12,2),
    hgv_co2_tonnes          DECIMAL(12,2),
    bus_co2_tonnes          DECIMAL(12,2),
    lgv_co2_tonnes          DECIMAL(12,2),
    total_vehicle_count     BIGINT,
    total_cycle_count       BIGINT,
    observation_points      INT,
    co2_per_vehicle_kg      DECIMAL(8,2)
)
WITH (
    LOCATION = '/environmental/fact_co2_emissions/',
    DATA_SOURCE = GoldDataLake,
    FILE_FORMAT = DeltaParquetFormat
);
GO

CREATE EXTERNAL TABLE [gold].[fact_vehicle_mix] (
    region_name             NVARCHAR(100),
    [year]                  INT,
    cycles                  BIGINT,
    motorcycles             BIGINT,
    cars                    BIGINT,
    buses                   BIGINT,
    lgvs                    BIGINT,
    hgvs                    BIGINT,
    total                   BIGINT,
    car_share_pct           DECIMAL(5,2),
    cycle_share_pct         DECIMAL(5,2),
    hgv_share_pct           DECIMAL(5,2),
    bus_share_pct           DECIMAL(5,2),
    green_transport_index   DECIMAL(5,2),
    green_index_change      DECIMAL(5,2)
)
WITH (
    LOCATION = '/environmental/fact_vehicle_mix/',
    DATA_SOURCE = GoldDataLake,
    FILE_FORMAT = DeltaParquetFormat
);
GO

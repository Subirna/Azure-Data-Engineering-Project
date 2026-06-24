-- Power BI View: Infrastructure Planning & Capacity Analysis
-- Provides congestion and capacity metrics for the Infrastructure Planning dashboard page

CREATE OR ALTER VIEW [reporting].[vw_congestion_analysis]
AS
SELECT
    hp.[year],
    hp.[hour],
    hp.time_period,
    cp.region_name,
    cp.local_authority_name,
    cp.road_name,
    cp.road_type,
    cp.road_category,
    cp.latitude,
    cp.longitude,
    hp.avg_vehicles,
    hp.max_vehicles,
    hp.min_vehicles,
    hp.avg_cars,
    hp.avg_hgvs,
    hp.observation_count,
    hp.congestion_index,
    CASE
        WHEN hp.congestion_index >= 0.9 THEN 'Severely Congested'
        WHEN hp.congestion_index >= 0.75 THEN 'Congested'
        WHEN hp.congestion_index >= 0.5 THEN 'Moderate'
        ELSE 'Free Flow'
    END AS congestion_level,
    CASE
        WHEN hp.time_period = 'morning_peak' THEN 1
        WHEN hp.time_period = 'evening_peak' THEN 2
        WHEN hp.time_period = 'inter_peak' THEN 3
        WHEN hp.time_period = 'evening' THEN 4
        ELSE 5
    END AS time_period_sort_order
FROM [gold].[fact_hourly_peaks] hp
INNER JOIN [gold].[dim_count_point] cp
    ON hp.count_point_id = cp.count_point_id;
GO

CREATE OR ALTER VIEW [reporting].[vw_capacity_utilisation]
AS
SELECT
    cp.region_name,
    cp.road_type,
    cp.road_category,
    hp.[year],
    COUNT(DISTINCT hp.count_point_id) AS total_count_points,
    AVG(hp.congestion_index) AS avg_congestion_index,
    SUM(CASE WHEN hp.congestion_index >= 0.9 THEN 1 ELSE 0 END) AS severely_congested_count,
    SUM(CASE WHEN hp.congestion_index >= 0.75 THEN 1 ELSE 0 END) AS congested_count,
    SUM(CASE WHEN hp.congestion_index < 0.5 THEN 1 ELSE 0 END) AS free_flow_count,
    CAST(SUM(CASE WHEN hp.congestion_index >= 0.75 THEN 1 ELSE 0 END) AS DECIMAL(5,2))
        / NULLIF(COUNT(*), 0) * 100 AS pct_congested
FROM [gold].[fact_hourly_peaks] hp
INNER JOIN [gold].[dim_count_point] cp
    ON hp.count_point_id = cp.count_point_id
WHERE hp.time_period IN ('morning_peak', 'evening_peak')
GROUP BY cp.region_name, cp.road_type, cp.road_category, hp.[year];
GO

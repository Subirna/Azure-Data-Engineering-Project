-- Power BI View: Accident Hotspots & Road Safety
-- Provides geospatial and severity data for the Road Safety dashboard page

CREATE OR ALTER VIEW [reporting].[vw_accident_hotspots]
AS
SELECT
    h.lat_grid,
    h.lon_grid,
    h.collision_year,
    h.total_incidents,
    h.fatal_incidents,
    h.serious_incidents,
    h.total_casualties,
    h.avg_speed_limit,
    h.is_urban,
    h.severity_score,
    h.hotspot_rank,
    CASE
        WHEN h.hotspot_rank <= 10 THEN 'Critical'
        WHEN h.hotspot_rank <= 50 THEN 'High'
        WHEN h.hotspot_rank <= 200 THEN 'Medium'
        ELSE 'Low'
    END AS risk_category
FROM [gold].[fact_accident_hotspots] h;
GO

CREATE OR ALTER VIEW [reporting].[vw_accident_trends]
AS
SELECT
    a.collision_year,
    a.collision_month,
    a.severity_label,
    a.weather_label,
    a.light_condition_label,
    a.is_urban,
    a.speed_limit,
    a.total_collisions,
    a.total_casualties,
    a.fatal_count,
    a.serious_count,
    a.slight_count,
    a.ksi_count,
    a.ksi_rate,
    CASE
        WHEN a.speed_limit <= 30 THEN '20-30 mph'
        WHEN a.speed_limit <= 50 THEN '40-50 mph'
        WHEN a.speed_limit <= 60 THEN '60 mph'
        ELSE '70+ mph'
    END AS speed_band,
    CASE
        WHEN a.is_urban = 1 THEN 'Urban'
        ELSE 'Rural'
    END AS area_type
FROM [gold].[fact_accident_summary] a;
GO

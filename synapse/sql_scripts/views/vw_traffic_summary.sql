-- Power BI View: Traffic Volume Summary
-- Provides a flattened, ready-to-consume view for the Traffic Analysis dashboard page

CREATE OR ALTER VIEW [reporting].[vw_traffic_summary]
AS
SELECT
    dt.[year],
    dt.[month],
    dt.month_name,
    dt.quarter,
    dt.fiscal_year,
    dt.day_name,
    dt.is_weekend,
    cp.region_name,
    cp.local_authority_name,
    cp.road_name,
    cp.road_type,
    cp.road_category,
    cp.latitude,
    cp.longitude,
    ft.total_all_vehicles,
    ft.total_cars,
    ft.total_hgvs,
    ft.total_buses,
    ft.total_lgvs,
    ft.total_pedal_cycles,
    ft.total_motorcycles,
    ft.motorised_vehicles,
    ft.freight_vehicles,
    ft.active_travel_vehicles,
    ft.avg_hgv_percentage,
    ft.hours_counted,
    yoy.yoy_change_pct,
    yoy.total_vehicles AS annual_total_vehicles
FROM [gold].[fact_daily_traffic] ft
INNER JOIN [gold].[dim_count_point] cp
    ON ft.count_point_id = cp.count_point_id
INNER JOIN [gold].[dim_date] dt
    ON ft.count_date = dt.[date]
LEFT JOIN [gold].[fact_yoy_regional] yoy
    ON cp.region_name = yoy.region_name
    AND cp.road_type = yoy.road_type
    AND dt.[year] = yoy.[year];
GO

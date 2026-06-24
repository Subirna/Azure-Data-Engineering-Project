-- Power BI View: Environmental Impact & Sustainability
-- Provides CO2 emissions and green transport metrics for the Environmental dashboard page

CREATE OR ALTER VIEW [reporting].[vw_co2_emissions]
AS
SELECT
    e.region_name,
    e.local_authority_name,
    e.road_type,
    e.[year],
    e.total_co2_tonnes,
    e.car_co2_tonnes,
    e.hgv_co2_tonnes,
    e.bus_co2_tonnes,
    e.lgv_co2_tonnes,
    e.total_vehicle_count,
    e.total_cycle_count,
    e.observation_points,
    e.co2_per_vehicle_kg,
    CASE
        WHEN e.co2_per_vehicle_kg <= 1.5 THEN 'Low Emission'
        WHEN e.co2_per_vehicle_kg <= 2.5 THEN 'Medium Emission'
        ELSE 'High Emission'
    END AS emission_category
FROM [gold].[fact_co2_emissions] e;
GO

CREATE OR ALTER VIEW [reporting].[vw_green_transport]
AS
SELECT
    vm.region_name,
    vm.[year],
    vm.cycles,
    vm.motorcycles,
    vm.cars,
    vm.buses,
    vm.lgvs,
    vm.hgvs,
    vm.total,
    vm.car_share_pct,
    vm.cycle_share_pct,
    vm.hgv_share_pct,
    vm.bus_share_pct,
    vm.green_transport_index,
    vm.green_index_change,
    CASE
        WHEN vm.green_transport_index >= 10 THEN 'Leading'
        WHEN vm.green_transport_index >= 5 THEN 'Progressing'
        ELSE 'Lagging'
    END AS sustainability_tier
FROM [gold].[fact_vehicle_mix] vm;
GO

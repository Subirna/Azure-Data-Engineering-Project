# Power BI Data Model — UK Traffic Intelligence Dashboard

## Connection
Connect Power BI to Azure Synapse Analytics using **DirectQuery** or **Import** mode.
- Server: `syn-uk-traffic-dev.sql.azuresynapse.net`
- Database: `traffic_dwh`
- Use the `reporting` schema views for all dashboard pages.

## Star Schema

```
                    ┌──────────────┐
                    │  dim_date    │
                    │──────────────│
                    │ date (PK)    │
                    │ year         │
                    │ month        │
                    │ quarter      │
                    │ day_name     │
                    │ is_weekend   │
                    │ fiscal_year  │
                    └──────┬───────┘
                           │
┌──────────────────┐  ┌────┴──────────────┐  ┌──────────────────────┐
│ dim_count_point  │──│ fact_daily_traffic │  │ fact_accident_summary│
│──────────────────│  │───────────────────│  │──────────────────────│
│ count_point_id   │  │ count_point_id    │  │ collision_year       │
│ road_name        │  │ count_date        │  │ severity_label       │
│ road_type        │  │ year              │  │ total_collisions     │
│ region_name      │  │ total_cars        │  │ total_casualties     │
│ local_authority  │  │ total_hgvs        │  │ ksi_count            │
│ latitude         │  │ total_all_vehicles│  │ ksi_rate             │
│ longitude        │  │ freight_vehicles  │  └──────────────────────┘
│ road_category    │  └───────────────────┘
└──────────────────┘
```

## Dashboard Pages

### Page 1: Traffic Volume Overview
**Views Used:** `reporting.vw_traffic_summary`

| Visual | Type | Fields |
|--------|------|--------|
| Total Vehicles Card | Card | SUM(total_all_vehicles) |
| Traffic by Region | Bar Chart | region_name, SUM(total_all_vehicles) |
| YoY Growth Trend | Line Chart | year, SUM(total_all_vehicles) by region |
| Vehicle Type Breakdown | Donut Chart | total_cars, total_hgvs, total_buses, total_cycles |
| Peak Hour Heatmap | Matrix | day_name (rows), hour (columns), AVG(total_vehicles) |
| COVID Recovery Tracker | Line Chart | year (2019-2025), SUM(total_all_vehicles) |
| Map: Traffic Density | Map | latitude, longitude, SUM(total_all_vehicles) |

**Slicers:** Year, Region, Road Type, Weekend/Weekday

### Page 2: Road Safety Intelligence
**Views Used:** `reporting.vw_accident_hotspots`, `reporting.vw_accident_trends`

| Visual | Type | Fields |
|--------|------|--------|
| KSI Count Card | Card | SUM(ksi_count) |
| Fatality Trend | Line Chart | collision_year, SUM(fatal_count) |
| Accident Hotspot Map | Map | lat_grid, lon_grid, severity_score (bubble size) |
| Severity by Weather | Stacked Bar | weather_label, fatal/serious/slight counts |
| Speed Band Analysis | Clustered Bar | speed_band, SUM(total_collisions) by severity |
| Urban vs Rural | Donut Chart | area_type, SUM(total_collisions) |
| Time-of-Day Pattern | Heatmap | day_of_week, hour, collision_count |

**Slicers:** Year, Severity, Urban/Rural, Weather

### Page 3: Environmental Impact
**Views Used:** `reporting.vw_co2_emissions`, `reporting.vw_green_transport`

| Visual | Type | Fields |
|--------|------|--------|
| Total CO2 Tonnes Card | Card | SUM(total_co2_tonnes) |
| CO2 by Region | Bar Chart | region_name, SUM(total_co2_tonnes) |
| CO2 by Vehicle Type | Stacked Area | year, car/hgv/bus/lgv co2 tonnes |
| Green Transport Index | Line Chart | year, green_transport_index by region |
| Cycle Mode Share | Line Chart | year, cycle_share_pct by region |
| Emission Category Map | Map | region, emission_category (colour) |
| Sustainability Tier Table | Table | region, year, green_transport_index, tier |

**Slicers:** Year, Region, Road Type

### Page 4: Infrastructure Planning
**Views Used:** `reporting.vw_congestion_analysis`, `reporting.vw_capacity_utilisation`

| Visual | Type | Fields |
|--------|------|--------|
| Congestion Index Card | Card | AVG(congestion_index) |
| Congestion Heatmap | Map | latitude, longitude, congestion_level (colour) |
| Peak vs Off-Peak | Clustered Bar | time_period, AVG(avg_vehicles) |
| Capacity Utilisation | Gauge | pct_congested per region |
| Congestion Trend | Line Chart | year, AVG(congestion_index) by region |
| Investment Priority Table | Table | region, road_type, pct_congested, ranking |

**Slicers:** Year, Region, Road Type, Time Period

## DAX Measures

```dax
// KPI: Total Traffic Volume
Total Traffic = SUM('fact_daily_traffic'[total_all_vehicles])

// KPI: Year-over-Year Change
YoY Change % = 
VAR CurrentYear = SUM('fact_yoy_regional'[total_vehicles])
VAR PrevYear = SUM('fact_yoy_regional'[prev_year_vehicles])
RETURN DIVIDE(CurrentYear - PrevYear, PrevYear, 0) * 100

// KPI: Killed or Seriously Injured Rate
KSI Rate = DIVIDE(SUM('fact_accident_summary'[ksi_count]), SUM('fact_accident_summary'[total_collisions]), 0) * 100

// KPI: Green Transport Index
Green Index = DIVIDE(
    SUM('fact_vehicle_mix'[cycles]) + SUM('fact_vehicle_mix'[buses]),
    SUM('fact_vehicle_mix'[total]), 0
) * 100

// KPI: CO2 per Vehicle
CO2 Per Vehicle = DIVIDE(SUM('fact_co2_emissions'[total_co2_tonnes]) * 1000, SUM('fact_co2_emissions'[total_vehicle_count]), 0)

// KPI: COVID Recovery Index (vs 2019 baseline)
COVID Recovery % = 
VAR Baseline2019 = CALCULATE(SUM('fact_daily_traffic'[total_all_vehicles]), 'dim_date'[year] = 2019)
VAR Current = SUM('fact_daily_traffic'[total_all_vehicles])
RETURN DIVIDE(Current, Baseline2019, 0) * 100
```

## Relationships
- `fact_daily_traffic[count_point_id]` → `dim_count_point[count_point_id]` (Many-to-One)
- `fact_daily_traffic[count_date]` → `dim_date[date]` (Many-to-One)
- `fact_hourly_peaks[count_point_id]` → `dim_count_point[count_point_id]` (Many-to-One)

## Refresh Schedule
- **Import Mode:** Daily at 6:00 AM UTC (after ADF pipeline completes)
- **DirectQuery:** Real-time (use for large datasets)

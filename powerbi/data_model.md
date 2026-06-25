# Power BI Data Model — UK Traffic Intelligence Dashboard

## Connection
- **Server:** `syn-bd-training-uk-ondemand.sql.azuresynapse.net`
- **Database:** `uk_traffic_db`
- **Authentication:** Organizational account (Microsoft sign-in)
- **Mode:** Import

---

## Star Schema Data Model

```
                         ┌─────────────────────┐
                         │    vw_dim_date       │
                         │    (DIMENSION)       │
                         │─────────────────────│
                         │ date                 │
                         │ year (PK)  ──────────┼──────────────────────────────┐
                         │ month                │                              │
                         │ quarter              │                              │
                         │ day_name             │                              │
                         │ month_name           │                              │
                         │ is_weekend           │                              │
                         └──────┬──────┬────────┘                              │
                                │      │                                       │
              ┌─────────────────┤      ├─────────────────┐                     │
              │ (year)          │      │ (year)           │ (year)             │ (year)
              ▼                 │      ▼                  ▼                    ▼
┌─────────────────────┐  │  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ vw_traffic_summary  │  │  │ vw_co2_emissions │ │  vw_vehicle_mix  │ │ vw_covid_impact  │
│      (FACT)         │  │  │     (FACT)       │ │     (FACT)       │ │     (FACT)       │
│─────────────────────│  │  │──────────────────│ │──────────────────│ │──────────────────│
│ region_name         │  │  │ region_name      │ │ region_name      │ │ region_name      │
│ road_type           │  │  │ road_type        │ │ year (FK)        │ │ road_type        │
│ year (FK)           │  │  │ year (FK)        │ │ cycles           │ │ year (FK)        │
│ total_cars          │  │  │ total_co2_tonnes │ │ motorcycles      │ │ total_vehicles   │
│ total_buses         │  │  │ car_co2_tonnes   │ │ cars             │ │ total_cycles     │
│ total_lgvs          │  │  │ hgv_co2_tonnes   │ │ buses            │ │ total_hgvs       │
│ total_hgvs          │  │  │ total_vehicle_   │ │ lgvs             │ │ baseline_2019    │
│ total_cycles        │  │  │   count          │ │ hgvs             │ │ recovery_pct     │
│ total_motorcycles   │  │  │ co2_per_vehicle  │ │ total            │ │ yoy_change       │
│ total_motor_vehicles│  │  │   _kg            │ │ car_share_pct    │ └──────────────────┘
│ total_all_vehicles  │  │  └──────────────────┘ │ cycle_share_pct  │
│ count_points_       │  │                       │ hgv_share_pct    │
│   observed          │  │                       │ bus_share_pct    │
│ avg_hgv_pct         │  │                       │ green_transport_ │
│ freight_vehicles    │  │                       │   index          │
│ green_transport_    │  │                       │ prev_green_index │
│   index             │  │                       │ green_index_     │
│ prev_year_vehicles  │  │                       │   change         │
│ yoy_change_pct      │  │                       └──────────────────┘
└─────────────────────┘  │
                         │ (year)
                         ▼
                ┌──────────────────┐
                │ vw_road_analysis │
                │     (FACT)       │
                │──────────────────│
                │ region_name      │
                │ road_class       │
                │ road_name        │
                │ year (FK)        │
                │ total_motor_     │
                │   vehicles       │
                │ total_hgvs       │
                │ total_cycles     │
                │ avg_link_length  │
                │   _km            │
                │ count_points     │
                │ vehicles_per_km  │
                └──────────────────┘


    ┌──────────────────┐         ┌──────────────────┐
    │ vw_busiest_roads │         │  vw_dim_location  │
    │ (STANDALONE FACT)│         │   (DIMENSION)     │
    │──────────────────│         │──────────────────│
    │ region_name      │         │ count_point_id    │
    │ road_name        │         │ road_name         │
    │ road_type        │         │ road_type         │
    │ latitude         │         │ road_category     │
    │ longitude        │         │ region_name       │
    │ total_vehicles   │         │ local_authority_  │
    │ total_hgvs       │         │   name            │
    │ total_cycles     │         │ latitude          │
    │ rank             │         │ longitude         │
    └──────────────────┘         │ road_class        │
                                 └──────────────────┘
```

---

## Relationships

| # | From Table | Column | To Table | Column | Type | Status |
|---|-----------|--------|----------|--------|------|--------|
| 1 | vw_dim_date | year | vw_traffic_summary | year | Many-to-Many | Active |
| 2 | vw_dim_date | year | vw_co2_emissions | year | Many-to-Many | Active |
| 3 | vw_dim_date | year | vw_vehicle_mix | year | Many-to-Many | Active |
| 4 | vw_dim_date | year | vw_covid_impact | year | Many-to-Many | Active |
| 5 | vw_dim_date | year | vw_road_analysis | year | Many-to-Many | Active |

**Note:** `vw_busiest_roads` and `vw_dim_location` are standalone (no relationships needed).

---

## Gold Layer Tables in ADLS Gen2

**Storage:** `abfss://gold@subiradls2026.dfs.core.windows.net/`

| # | Folder | Type | Rows | Description |
|---|--------|------|------|-------------|
| 1 | fact_traffic_summary/ | Fact | 80 | Traffic by region, road type, year. YoY trends |
| 2 | fact_co2_emissions/ | Fact | 80 | CO2 estimates using UK BEIS emission factors |
| 3 | fact_vehicle_mix/ | Fact | 80 | Vehicle type breakdown, green transport index |
| 4 | fact_road_analysis/ | Fact | 174 | Road category comparison, vehicles per km |
| 5 | fact_covid_impact/ | Fact | 28 | COVID recovery vs 2019 baseline |
| 6 | fact_busiest_roads/ | Fact | 12 | Top busiest roads with coordinates (2023) |
| 7 | dim_date/ | Dimension | 9,497 | Date dimension (2000-2025) |
| 8 | dim_location/ | Dimension | 12 | Count point locations with lat/lon |

---

## Dashboard: UK Road Traffic Intelligence (1 Page)

### Slicers

| Slicer | Table | Field | Type |
|--------|-------|-------|------|
| Year | vw_dim_date | year | Dropdown (multi-select) |
| Region | vw_traffic_summary | region_name | Dropdown (multi-select) |

### KPI Cards (Top Row)

| # | Title | Table | Field | Aggregation | Example Value |
|---|-------|-------|-------|-------------|---------------|
| 1 | Total Vehicles | vw_traffic_summary | total_all_vehicles | Sum | 16bn |
| 2 | Total CO2 Tonnes | vw_co2_emissions | total_co2_tonnes | Sum | 43.61M |
| 3 | Green Transport Index | vw_vehicle_mix | green_transport_index | Average | 3.81 |
| 4 | COVID Recovery % | vw_covid_impact | recovery_pct | Average | 92.45 |

### Charts (2x2 Grid)

| # | Title | Visual Type | Table | Config |
|---|-------|-------------|-------|--------|
| 1 | Traffic Trend by Region | Line Chart | vw_vehicle_mix | X: year, Y: total, Legend: region_name |
| 2 | Vehicle Type Breakdown | Donut Chart | vw_vehicle_mix | Values: cars, hgvs, lgvs, buses, cycles |
| 3 | CO2 Emissions by Region | Clustered Bar | vw_co2_emissions | Y: region_name, X: total_co2_tonnes |
| 4 | Green Transport Index Trend | Line Chart | vw_vehicle_mix | X: year, Y: green_transport_index, Legend: region_name |

### Theme
- Dark theme applied
- Professional executive layout

---

## DAX Measures (Optional Enhancements)

```dax
// Total Traffic Volume
Total Traffic = SUM(vw_traffic_summary[total_all_vehicles])

// Year-over-Year Change %
YoY Change % = AVERAGE(vw_traffic_summary[yoy_change_pct])

// KSI Rate (if accident data added)
// KSI Rate = DIVIDE(SUM([ksi_count]), SUM([total_collisions]), 0) * 100

// Green Transport Index
Green Index = AVERAGE(vw_vehicle_mix[green_transport_index])

// CO2 Per Vehicle
CO2 Per Vehicle = AVERAGE(vw_co2_emissions[co2_per_vehicle_kg])

// COVID Recovery vs 2019
COVID Recovery = AVERAGE(vw_covid_impact[recovery_pct])
```

---

## Data Flow

```
UK Gov DfT API (roadtraffic.dft.gov.uk)
        │
        ▼
Databricks: 02_bronze_ingestion.py
        │ (600,750 rows → Parquet)
        ▼
ADLS Gen2: bronze/traffic/counts_clean/
        │
        ▼
Databricks: 03_silver_transform.py
        │ (type-cast, cleanse, validate)
        ▼
ADLS Gen2: silver/traffic/counts/
        │
        ▼
Databricks: 04_gold_transform.py
        │ (aggregate, KPIs, 8 tables)
        ▼
ADLS Gen2: gold/ (8 folders)
        │
        ▼
Synapse: 8 SQL views (OPENROWSET)
        │
        ▼
Power BI: 1-page executive dashboard
```

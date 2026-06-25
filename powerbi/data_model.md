# Power BI Data Model — UK Traffic Intelligence Dashboard

## Connection
- **Server:** `syn-bd-training-uk-ondemand.sql.azuresynapse.net`
- **Database:** `uk_traffic_db`
- **Authentication:** Organizational account (Microsoft sign-in)
- **Mode:** Import

---

## Source Tables (Bronze Layer — Raw from UK DfT API)

### Source: UK Department for Transport — Road Traffic Statistics
**Base URL:** `https://roadtraffic.dft.gov.uk/api`

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                         SOURCE TABLES (RAW API DATA)                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║  ┌─────────────────────────────┐     ┌──────────────────────────────────┐   ║
║  │  regions                    │     │  local_authorities               │   ║
║  │  (Reference Table)          │     │  (Reference Table)               │   ║
║  │  API: /api/regions          │     │  API: /api/local-authorities     │   ║
║  │  Rows: 11                   │     │  Rows: 214                       │   ║
║  ├─────────────────────────────┤     ├──────────────────────────────────┤   ║
║  │ PK  id          INT        │     │ PK  id              INT         │   ║
║  │     name        STRING     │◄────│ FK  region_id       INT         │   ║
║  │     slug        STRING     │     │     name            STRING      │   ║
║  └─────────────────────────────┘     │     slug            STRING      │   ║
║           │                          │     ita_id          INT         │   ║
║           │ 1:M                      └──────────────────────────────────┘   ║
║           │                                    │                            ║
║           │                                    │ 1:M                        ║
║           ▼                                    ▼                            ║
║  ┌──────────────────────────────────────────────────────────────────────┐   ║
║  │  count_points                                                        │   ║
║  │  (Reference Table — Physical Traffic Counting Locations)             │   ║
║  │  API: /api/count-points (paginated, 46,754 rows)                     │   ║
║  ├──────────────────────────────────────────────────────────────────────┤   ║
║  │ PK  count_point_id       INT       Unique ID for counting location  │   ║
║  │ FK  region_id            INT       Links to regions.id              │   ║
║  │ FK  local_authority_id   INT       Links to local_authorities.id    │   ║
║  │     road_name            STRING    Road identifier (e.g. A3111, M4) │   ║
║  │     road_category        STRING    PA, TM, TA, M                    │   ║
║  │     road_type            STRING    Major / Minor                     │   ║
║  │     start_junction       STRING    Start junction description        │   ║
║  │     end_junction         STRING    End junction description          │   ║
║  │     easting              INT       OS grid easting                   │   ║
║  │     northing             INT       OS grid northing                  │   ║
║  │     latitude             DOUBLE    GPS latitude                      │   ║
║  │     longitude            DOUBLE    GPS longitude                     │   ║
║  │     link_length_km       DOUBLE    Road link length in km            │   ║
║  │     link_length_miles    DOUBLE    Road link length in miles         │   ║
║  └──────────────────────────────────────────────────────────────────────┘   ║
║           │                                                                  ║
║           │ 1:M (one count point has many yearly readings)                   ║
║           ▼                                                                  ║
║  ┌──────────────────────────────────────────────────────────────────────┐   ║
║  │  traffic_counts (Average Annual Daily Flow — AADF)                   │   ║
║  │  (MAIN FACT TABLE — Vehicle Counts by Year)                          │   ║
║  │  API: /api/average-annual-daily-flow (paginated, 600,750 rows)       │   ║
║  ├──────────────────────────────────────────────────────────────────────┤   ║
║  │ PK  id                        INT       Unique record ID             │   ║
║  │ FK  count_point_id            INT       Links to count_points        │   ║
║  │ FK  region_id                 INT       Links to regions.id          │   ║
║  │ FK  local_authority_id        INT       Links to local_authorities   │   ║
║  │     year                      INT       Survey year (2000-2025)      │   ║
║  │     road_name                 STRING    Road identifier              │   ║
║  │     road_category             STRING    PA, TM, TA, M                │   ║
║  │     road_type                 STRING    Major / Minor                │   ║
║  │     link_length_km            DOUBLE    Road link length             │   ║
║  │     estimation_method         STRING    Counted / Estimated          │   ║
║  │     estimation_method_detailed STRING   Detailed method description  │   ║
║  │     latitude                  DOUBLE    GPS latitude                 │   ║
║  │     longitude                 DOUBLE    GPS longitude                │   ║
║  │     easting                   INT       OS grid easting              │   ║
║  │     northing                  INT       OS grid northing             │   ║
║  │  ── Vehicle Type Counts (Annual Average Daily Flow) ──               │   ║
║  │     pedal_cycles              INT       Bicycles per day             │   ║
║  │     two_wheeled_motor_vehicles INT      Motorcycles per day          │   ║
║  │     cars_and_taxis            INT       Cars & taxis per day         │   ║
║  │     buses_and_coaches         INT       Buses per day                │   ║
║  │     lgvs                      INT       Light goods vehicles/day     │   ║
║  │     hgvs_2_rigid_axle         INT       HGV 2-axle rigid per day    │   ║
║  │     hgvs_3_rigid_axle         INT       HGV 3-axle rigid per day    │   ║
║  │     hgvs_4_or_more_rigid_axle INT       HGV 4+ axle rigid per day   │   ║
║  │     hgvs_3_or_4_articulated   INT       HGV 3-4 axle artic per day  │   ║
║  │     hgvs_5_articulated_axle   INT       HGV 5-axle artic per day    │   ║
║  │     hgvs_6_articulated_axle   INT       HGV 6-axle artic per day    │   ║
║  │     all_hgvs                  INT       Total HGVs per day           │   ║
║  │     all_motor_vehicles        INT       Total motor vehicles per day │   ║
║  └──────────────────────────────────────────────────────────────────────┘   ║
║                                                                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### Source to Gold Data Lineage

```
SOURCE (Bronze)                    SILVER                    GOLD
───────────────                    ──────                    ────

regions (11 rows)          →   regions/ (cleansed)     ─┐
  • id, name                                             │
                                                         ├──► fact_traffic_summary (80 rows)
local_authorities (214)    →   local_authorities/      │     • region_name, road_type, year
  • id, name, region_id                                 │     • total_cars, total_hgvs, yoy_change_pct
                                                         │
count_points (46,754)      →   count_points/           ├──► fact_co2_emissions (80 rows)
  • count_point_id, lat,                                │     • region_name, year, total_co2_tonnes
    lon, road_name                                      │
                                                         ├──► fact_vehicle_mix (80 rows)
traffic_counts (600,750)   →   counts/ (600,750)       │     • region_name, year, green_transport_index
  • All vehicle type counts     • Type-cast to INT      │
  • year, region_id             • UK coordinate filter  ├──► fact_road_analysis (174 rows)
  • latitude, longitude         • Derived: total_       │     • road_class, vehicles_per_km
                                  vehicles, hgv_pct     │
                                                         ├──► fact_covid_impact (28 rows)
                                                         │     • recovery_pct vs 2019 baseline
                                                         │
                                                         ├──► fact_busiest_roads (12 rows)
                                                         │     • Top roads ranked by total_vehicles
                                                         │
                                                         ├──► dim_location (12 rows)
                                                         │     • count_point_id, lat, lon, region
                                                         │
                                                         └──► dim_date (9,497 rows)
                                                               • Generated: 2000-01-01 to 2025-12-31
```

---

## Entity Relationship Diagram (ERD)

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                     UK TRAFFIC INTELLIGENCE — DATA MODEL                    ║
║                          Star Schema (Snowflake)                            ║
╚══════════════════════════════════════════════════════════════════════════════╝


                            ┌───────────────────────────┐
                            │      vw_dim_date          │
                            │      (DIMENSION)          │
                            ├───────────────────────────┤
                            │ PK  date        DATE      │
                            │ PK  year        INT    ◄──┼────────────────────────────┐
                            │     month       INT       │                            │
                            │     quarter     INT       │                            │
                            │     day_name    STRING    │                            │
                            │     month_name  STRING    │                            │
                            │     is_weekend  BOOLEAN   │                            │
                            └─────┬─────┬─────┬─────┬──┘                            │
                                  │     │     │     │                                │
                     1:M          │     │     │     │          1:M                   │
          ┌───────────────────────┘     │     │     └────────────────────────┐       │
          │              1:M           │     │           1:M                │       │
          │               ┌────────────┘     └──────────────┐              │       │
          ▼               ▼                                 ▼              ▼       │
┌─────────────────┐ ┌─────────────────┐          ┌─────────────────┐ ┌────────────────┐
│vw_traffic_      │ │vw_co2_          │          │vw_vehicle_mix   │ │vw_covid_       │
│  summary        │ │  emissions      │          │                 │ │  impact        │
│ (FACT)          │ │ (FACT)          │          │ (FACT)          │ │ (FACT)         │
├─────────────────┤ ├─────────────────┤          ├─────────────────┤ ├────────────────┤
│     region_name │ │     region_name │          │     region_name │ │    region_name │
│     road_type   │ │     road_type   │          │ FK  year ───────┼─┤ FK year ───────┤
│ FK  year ───────┤ │ FK  year ───────┤          │     cycles      │ │    road_type   │
│     total_cars  │ │     total_co2_  │          │     motorcycles │ │    total_      │
│     total_buses │ │       tonnes    │          │     cars        │ │      vehicles  │
│     total_lgvs  │ │     car_co2_    │          │     buses       │ │    total_      │
│     total_hgvs  │ │       tonnes    │          │     lgvs        │ │      cycles    │
│     total_      │ │     hgv_co2_    │          │     hgvs        │ │    total_hgvs  │
│       cycles    │ │       tonnes    │          │     total       │ │    baseline_   │
│     total_      │ │     total_      │          │     car_share_  │ │      2019      │
│       motor_    │ │       vehicle_  │          │       pct       │ │    recovery_   │
│       cycles    │ │       count     │          │     cycle_share_│ │      pct       │
│     total_      │ │     co2_per_    │          │       pct       │ │    yoy_change  │
│       motor_    │ │       vehicle_  │          │     hgv_share_  │ └────────────────┘
│       vehicles  │ │       kg        │          │       pct       │
│     total_all_  │ └─────────────────┘          │     bus_share_  │
│       vehicles  │                              │       pct       │
│     count_      │                              │     green_      │
│       points_   │                              │       transport_│
│       observed  │                              │       index     │
│     avg_hgv_pct │                              │     prev_green_ │
│     freight_    │                              │       index     │
│       vehicles  │                              │     green_index_│
│     green_      │                              │       change    │
│       transport_│                              └─────────────────┘
│       index     │
│     prev_year_  │          ┌─────────────────┐
│       vehicles  │          │vw_road_analysis │
│     yoy_change_ │          │ (FACT)          │
│       pct       │          ├─────────────────┤
└─────────────────┘          │     region_name │
                             │     road_class  │
                             │     road_name   │
                             │ FK  year ───────┼── ► vw_dim_date.year (1:M)
                             │     total_motor_│
                             │       vehicles  │
                             │     total_hgvs  │
                             │     total_cycles│
                             │     avg_link_   │
                             │       length_km │
                             │     count_points│
                             │     vehicles_   │
                             │       per_km    │
                             └─────────────────┘


  ┌─────────────────────┐              ┌─────────────────────┐
  │  vw_busiest_roads   │              │   vw_dim_location   │
  │  (STANDALONE FACT)  │              │    (DIMENSION)      │
  ├─────────────────────┤              ├─────────────────────┤
  │     region_name     │              │ PK  count_point_id  │
  │     road_name       │              │     road_name       │
  │     road_type       │              │     road_type       │
  │     latitude        │              │     road_category   │
  │     longitude       │              │     region_name     │
  │     total_vehicles  │              │     local_authority_│
  │     total_hgvs      │              │       name          │
  │     total_cycles    │              │     latitude        │
  │     rank            │              │     longitude       │
  │                     │              │     road_class      │
  │ (No FK — 2023 only) │              │                     │
  └─────────────────────┘              │ (No FK — reference  │
                                       │  data only)         │
                                       └─────────────────────┘
```

---

## Relationship Details

```
╔════════════════════════════════════════════════════════════════════════════╗
║                         RELATIONSHIP DIAGRAM                              ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║                          vw_dim_date                                      ║
║                         ┌────────┐                                        ║
║                         │  year  │                                        ║
║                         │  (PK)  │                                        ║
║                         └───┬────┘                                        ║
║                             │                                             ║
║              ┌──────────────┼──────────────┬──────────────┬────────────┐  ║
║              │              │              │              │            │  ║
║              │ 1:M          │ 1:M          │ 1:M          │ 1:M       │  ║
║              ▼              ▼              ▼              ▼           ▼  ║
║        ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ ┌───────┐ ║
║        │ traffic  │  │  co2     │  │ vehicle  │  │  covid   │ │ road  │ ║
║        │ summary  │  │emissions │  │   mix    │  │ impact   │ │analysi│ ║
║        │  (FK:    │  │  (FK:    │  │  (FK:    │  │  (FK:    │ │  (FK: │ ║
║        │   year)  │  │   year)  │  │   year)  │  │   year)  │ │  year)│ ║
║        └──────────┘  └──────────┘  └──────────┘  └──────────┘ └───────┘ ║
║                                                                           ║
║   Standalone (no FK):                                                     ║
║        ┌──────────┐  ┌──────────┐                                        ║
║        │ busiest  │  │   dim    │                                        ║
║        │  roads   │  │ location │                                        ║
║        └──────────┘  └──────────┘                                        ║
║                                                                           ║
╚════════════════════════════════════════════════════════════════════════════╝
```

---

## Relationship Table

| # | Relationship | From (PK) | To (FK) | Cardinality | Direction | Active |
|---|-------------|-----------|---------|-------------|-----------|--------|
| 1 | dim_date → traffic_summary | vw_dim_date.year | vw_traffic_summary.year | One-to-Many (1:M) | Single | Yes |
| 2 | dim_date → co2_emissions | vw_dim_date.year | vw_co2_emissions.year | One-to-Many (1:M) | Single | Yes |
| 3 | dim_date → vehicle_mix | vw_dim_date.year | vw_vehicle_mix.year | One-to-Many (1:M) | Single | Yes |
| 4 | dim_date → covid_impact | vw_dim_date.year | vw_covid_impact.year | One-to-Many (1:M) | Single | Yes |
| 5 | dim_date → road_analysis | vw_dim_date.year | vw_road_analysis.year | One-to-Many (1:M) | Single | Yes |
| — | No relationship | — | vw_busiest_roads | Standalone | — | — |
| — | No relationship | — | vw_dim_location | Standalone | — | — |

### Key Definitions

| Key Type | Description | Example |
|----------|-------------|---------|
| **PK (Primary Key)** | Uniquely identifies a row in the dimension table | `vw_dim_date.year` = 2023 |
| **FK (Foreign Key)** | References the PK in the dimension table | `vw_traffic_summary.year` = 2023 |
| **1:M (One-to-Many)** | One year in dim_date relates to many rows in fact tables | Year 2023 → 4 region rows in traffic_summary |
| **Standalone** | Table not connected via FK — filtered independently | vw_busiest_roads (2023 data only) |

### Why 1:M (One-to-Many)?

```
vw_dim_date (1 side)          vw_traffic_summary (Many side)
┌──────┐                      ┌───────────────────────────────┐
│ 2019 │ ──────────────────►  │ Wales, Major, 2019            │
│      │                      │ Scotland, Major, 2019         │
│      │                      │ South West, Major, 2019       │
│      │                      │ East Midlands, Major, 2019    │
├──────┤                      ├───────────────────────────────┤
│ 2020 │ ──────────────────►  │ Wales, Major, 2020            │
│      │                      │ Scotland, Major, 2020         │
│      │                      │ South West, Major, 2020       │
│      │                      │ East Midlands, Major, 2020    │
└──────┘                      └───────────────────────────────┘

1 year → 4 regions = One-to-Many (1:M)
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

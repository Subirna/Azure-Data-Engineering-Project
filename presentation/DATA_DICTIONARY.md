# Complete Data Dictionary — Source to Gold

## 1. SOURCE TABLES (Raw from UK Government APIs)

### Source 1: traffic_counts (AADF — Average Annual Daily Flow)
**API:** `https://roadtraffic.dft.gov.uk/api/average-annual-daily-flow`
**Rows:** 602,250 | **Fetched by:** Databricks Bronze notebook (region by region)

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INT | Unique record ID | 1 |
| count_point_id | INT | Physical counting location ID | 51 |
| year | INT | Survey year | 2023 |
| region_id | INT | FK → regions.id | 1 |
| local_authority_id | INT | FK → local_authorities.id | 1 |
| road_name | STRING | Road identifier | A3111, M4, A1 |
| road_category | STRING | PA=Principal A, TM=Trunk Motorway, TA=Trunk A, M=Motorway | PA |
| road_type | STRING | Major or Minor | Major |
| start_junction_road_name | STRING | Start junction description | Pierhead, Hugh Town |
| end_junction_road_name | STRING | End junction description | A3112 |
| easting | INT | OS grid easting | 90200 |
| northing | INT | OS grid northing | 10585 |
| latitude | DOUBLE | GPS latitude | 49.915 |
| longitude | DOUBLE | GPS longitude | -6.317 |
| link_length_km | DOUBLE | Road segment length in km | 0.3 |
| link_length_miles | DOUBLE | Road segment length in miles | 0.2 |
| estimation_method | STRING | Counted or Estimated | Estimated |
| estimation_method_detailed | STRING | Detailed estimation method | Estimated using AADF from previous year |
| pedal_cycles | INT | Bicycles per day | 105 |
| two_wheeled_motor_vehicles | INT | Motorcycles per day | 87 |
| cars_and_taxis | INT | Cars and taxis per day | 837 |
| buses_and_coaches | INT | Buses per day | 25 |
| lgvs | INT | Light goods vehicles per day | 451 |
| hgvs_2_rigid_axle | INT | HGV 2-axle rigid per day | 30 |
| hgvs_3_rigid_axle | INT | HGV 3-axle rigid per day | 0 |
| hgvs_4_or_more_rigid_axle | INT | HGV 4+ axle rigid per day | 0 |
| hgvs_3_or_4_articulated_axle | INT | HGV 3-4 axle articulated per day | 0 |
| hgvs_5_articulated_axle | INT | HGV 5-axle articulated per day | 0 |
| hgvs_6_articulated_axle | INT | HGV 6-axle articulated per day | 0 |
| all_hgvs | INT | Total HGVs per day (sum of all HGV types) | 30 |
| all_motor_vehicles | INT | Total motor vehicles per day | 1430 |

---

### Source 2: regions
**API:** `https://roadtraffic.dft.gov.uk/api/regions`
**Rows:** 11 | **Format:** Plain JSON list

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INT | Region ID (PK) | 1 |
| name | STRING | Region name | South West |
| ons_code | STRING | ONS geographic code | E12000009 |
| country_id | INT | Country (1=England, 6=Scotland, 7=Wales) | 1 |

**All 11 Regions:**
1=South West, 2=East Midlands, 3=Scotland, 4=Wales, 5=North West,
6=London, 7=East of England, 8=Yorkshire, 9=South East, 10=West Midlands, 11=North East

---

### Source 3: local_authorities
**API:** `https://roadtraffic.dft.gov.uk/api/local-authorities`
**Rows:** 214 | **Format:** Plain JSON list

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INT | Local authority ID (PK) | 19 |
| name | STRING | Council name | Cardiff |
| region_id | INT | FK → regions.id | 4 (Wales) |
| ita_id | INT | Integrated Transport Authority ID | NULL |
| ons_code | STRING | ONS geographic code | W06000015 |

---

### Source 4: count_points
**API:** `https://roadtraffic.dft.gov.uk/api/count-points`
**Rows:** 46,754 | **Format:** Paginated JSON (250 per page)

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| count_point_id | INT | Unique location ID (PK) | 501 |
| region_id | INT | FK → regions.id | 4 |
| local_authority_id | INT | FK → local_authorities.id | 6 |
| road_name | STRING | Road identifier | M4 |
| road_category | STRING | PA, TM, TA, M | TM |
| road_type | STRING | Major or Minor | Major |
| latitude | DOUBLE | GPS latitude | 51.579 |
| longitude | DOUBLE | GPS longitude | -3.034 |
| easting | INT | OS grid easting | 332000 |
| northing | INT | OS grid northing | 183000 |

---

### Source 5: Carbon Intensity API (Streaming)
**API:** `https://api.carbonintensity.org.uk`

#### Endpoint: /intensity (National)
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| from | STRING | Period start | 2026-06-25T16:00Z |
| to | STRING | Period end | 2026-06-25T16:30Z |
| intensity.forecast | INT | Predicted gCO2/kWh | 178 |
| intensity.actual | INT | Actual gCO2/kWh | 160 |
| intensity.index | STRING | Level | moderate |

#### Endpoint: /generation (National Energy Mix)
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| from | STRING | Period start | 2026-06-25T16:00Z |
| to | STRING | Period end | 2026-06-25T16:30Z |
| generationmix[].fuel | STRING | Fuel type | wind |
| generationmix[].perc | DOUBLE | Percentage of total | 22.7 |

**9 Fuel Types:** biomass, coal, imports, gas, nuclear, other, hydro, solar, wind

#### Endpoint: /regional (17 UK Energy Regions)
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| regions[].regionid | INT | Region 1-17 | 3 |
| regions[].shortname | STRING | Region name | Scotland |
| regions[].dnoregion | STRING | Distribution operator | SP Distribution |
| regions[].intensity.forecast | INT | Regional gCO2/kWh | 2 |
| regions[].intensity.index | STRING | Regional level | very low |
| regions[].generationmix[] | ARRAY | 9 fuel types per region | wind: 80% |

---

## 2. TRANSFORMATION: SOURCE → BRONZE → SILVER → GOLD

### Bronze Layer (Raw — stored as-is)

| Bronze Table | Source | Rows | What happens |
|-------------|--------|------|-------------|
| counts_clean/ | traffic_counts API | 602,250 | Fetched region by region (1-11), saved as strings via safe_dataframe() |
| regions_clean/ | regions API | 11 | Direct JSON → DataFrame, all columns as strings |
| local_authorities_clean/ | local_authorities API | 214 | Direct JSON → DataFrame, all columns as strings |
| count_points_clean/ | count_points API | 46,754 | Paginated fetch, all columns as strings |
| streaming/raw/ | Event Hub events | Growing | Consumer reads events, appends raw JSON |

---

### Silver Layer (Cleansed)

| Silver Table | Source Bronze | Rows | Transformations Applied |
|-------------|-------------|------|------------------------|
| counts/ | counts_clean/ | 602,250 | Cast strings → INT/DOUBLE, validate UK coords (lat 49-61, lon -8 to 2), UPPER road names, add total_vehicles & hgv_percentage |
| count_points/ | count_points_clean/ | 250 | Cast types, validate coords, dropDuplicates on count_point_id |
| regions/ | regions_clean/ | 11 | Cast id to INT, InitCap names, dropDuplicates on id |
| local_authorities/ | local_authorities_clean/ | 214 | Cast id to INT, InitCap names, dropDuplicates on id |
| streaming/carbon_intensity/ | streaming/raw/ | Latest cycle | Parse JSON, extract fields, partition by event_type |

**Silver counts — New derived columns:**
```
total_vehicles = pedal_cycles + two_wheeled_motor_vehicles + 
                 cars_and_taxis + buses_and_coaches + lgvs + all_hgvs

hgv_percentage = all_hgvs / all_motor_vehicles × 100
```

---

## 3. GOLD TABLES — Which Source Tables & Columns Used

### BATCH GOLD

#### fact_traffic_summary (286 rows)
```
CREATED FROM: Silver counts + Silver regions
JOIN: counts.region_id = regions.id
GROUP BY: region_name, road_type, year
```
| Gold Column | Source Table | Source Column | Aggregation |
|------------|-------------|--------------|-------------|
| region_name | regions | name (renamed) | Group key |
| road_type | counts | road_type | Group key |
| year | counts | year | Group key |
| total_cars | counts | cars_and_taxis | SUM |
| total_buses | counts | buses_and_coaches | SUM |
| total_lgvs | counts | lgvs | SUM |
| total_hgvs | counts | all_hgvs | SUM |
| total_cycles | counts | pedal_cycles | SUM |
| total_motorcycles | counts | two_wheeled_motor_vehicles | SUM |
| total_motor_vehicles | counts | all_motor_vehicles | SUM |
| total_all_vehicles | counts | total_vehicles (derived in Silver) | SUM |
| count_points_observed | counts | count_point_id | COUNT DISTINCT |
| avg_hgv_pct | counts | hgv_percentage (derived in Silver) | AVG |
| freight_vehicles | — | total_lgvs + total_hgvs | Calculated |
| green_transport_index | — | (total_cycles + total_buses) / total_all_vehicles × 100 | Calculated |
| prev_year_vehicles | — | LAG(total_all_vehicles) OVER (partition by region, road_type ORDER BY year) | Window |
| yoy_change_pct | — | (current - prev) / prev × 100 | Calculated |

---

#### fact_co2_emissions (286 rows)
```
CREATED FROM: Silver counts + Silver regions
JOIN: counts.region_id = regions.id
GROUP BY: region_name, road_type, year
```
| Gold Column | Source Columns | Calculation |
|------------|---------------|-------------|
| region_name | regions.name | Group key |
| road_type | counts.road_type | Group key |
| year | counts.year | Group key |
| total_co2_tonnes | All vehicle columns | SUM(each_vehicle × emission_factor × 12.8 / 1000) / 1000 |
| car_co2_tonnes | counts.cars_and_taxis | SUM(cars × 164 × 12.8 / 1000) / 1000 |
| hgv_co2_tonnes | counts.all_hgvs | SUM(hgvs × 586 × 12.8 / 1000) / 1000 |
| total_vehicle_count | counts.all_motor_vehicles | SUM |
| co2_per_vehicle_kg | — | total_co2_tonnes × 1000 / total_vehicle_count |

**CO2 Emission Factors Used (grams per km):**
```
pedal_cycles:                    0 g/km
two_wheeled_motor_vehicles:     83 g/km
cars_and_taxis:                164 g/km
buses_and_coaches:             822 g/km
lgvs:                          209 g/km
all_hgvs:                      586 g/km
Average trip distance:        12.8 km
```

---

#### fact_vehicle_mix (286 rows)
```
CREATED FROM: Silver counts + Silver regions
JOIN: counts.region_id = regions.id
GROUP BY: region_name, year
```
| Gold Column | Source Column | Calculation |
|------------|-------------|-------------|
| region_name | regions.name | Group key |
| year | counts.year | Group key |
| cycles | counts.pedal_cycles | SUM |
| motorcycles | counts.two_wheeled_motor_vehicles | SUM |
| cars | counts.cars_and_taxis | SUM |
| buses | counts.buses_and_coaches | SUM |
| lgvs | counts.lgvs | SUM |
| hgvs | counts.all_hgvs | SUM |
| total | counts.total_vehicles | SUM |
| car_share_pct | — | cars / total × 100 |
| cycle_share_pct | — | cycles / total × 100 |
| hgv_share_pct | — | hgvs / total × 100 |
| bus_share_pct | — | buses / total × 100 |
| green_transport_index | — | (cycles + buses) / total × 100 |
| prev_green_index | — | LAG(green_transport_index) |
| green_index_change | — | current - previous |

---

#### fact_road_analysis (1,704 rows)
```
CREATED FROM: Silver counts + Silver regions
JOIN: counts.region_id = regions.id
GROUP BY: region_name, road_class, road_name, year
```
| Gold Column | Source Column | Calculation |
|------------|-------------|-------------|
| region_name | regions.name | Group key |
| road_class | counts.road_category | TA/TM→"Motorway/Trunk A", PA→"Principal A", M→"Motorway", else→"Minor/B Road" |
| road_name | counts.road_name | Group key |
| year | counts.year | Group key |
| total_motor_vehicles | counts.all_motor_vehicles | SUM |
| total_hgvs | counts.all_hgvs | SUM |
| total_cycles | counts.pedal_cycles | SUM |
| avg_link_length_km | counts.link_length_km | AVG |
| count_points | counts.count_point_id | COUNT DISTINCT |
| vehicles_per_km | — | total_motor_vehicles / avg_link_length_km |

---

#### fact_covid_impact (77 rows)
```
CREATED FROM: Silver counts + Silver regions (year 2019-2025 only)
JOIN 1: counts.region_id = regions.id
JOIN 2: LEFT JOIN baseline (year=2019) ON region_name, road_type
GROUP BY: region_name, road_type, year
```
| Gold Column | Source Column | Calculation |
|------------|-------------|-------------|
| region_name | regions.name | Group key |
| road_type | counts.road_type | Group key |
| year | counts.year | 2019-2025 only |
| total_vehicles | counts.all_motor_vehicles | SUM |
| total_cycles | counts.pedal_cycles | SUM |
| total_hgvs | counts.all_hgvs | SUM |
| baseline_2019 | — | total_vehicles WHERE year=2019 (via JOIN) |
| recovery_pct | — | total_vehicles / baseline_2019 × 100 |
| yoy_change | — | current - LAG(total_vehicles) |

---

#### fact_busiest_roads (95 rows)
```
CREATED FROM: Silver counts + Silver regions (year=2023 only)
JOIN: counts.region_id = regions.id
GROUP BY: region_name, road_name, road_type, latitude, longitude
FILTER: rank <= 500
```
| Gold Column | Source Column | Calculation |
|------------|-------------|-------------|
| region_name | regions.name | Group key |
| road_name | counts.road_name | Group key |
| road_type | counts.road_type | Group key |
| latitude | counts.latitude | Group key |
| longitude | counts.longitude | Group key |
| total_vehicles | counts.all_motor_vehicles | SUM |
| total_hgvs | counts.all_hgvs | SUM |
| total_cycles | counts.pedal_cycles | SUM |
| rank | — | DENSE_RANK ORDER BY total_vehicles DESC |

---

#### dim_date (9,497 rows)
```
CREATED FROM: Generated (not from source data)
Spark SQL sequence function: 2000-01-01 to 2025-12-31
```
| Gold Column | Calculation |
|------------|-------------|
| date | Each day from 2000-01-01 to 2025-12-31 |
| year | YEAR(date) |
| month | MONTH(date) |
| quarter | QUARTER(date) |
| day_name | FORMAT(date, "EEEE") → Monday, Tuesday... |
| month_name | FORMAT(date, "MMMM") → January, February... |
| is_weekend | dayofweek IN (1, 7) → Saturday or Sunday |

---

#### dim_location (123 rows)
```
CREATED FROM: Silver counts + Silver regions + Silver local_authorities
JOIN 1: counts.region_id = regions.id
JOIN 2: counts.local_authority_id = local_authorities.id
SELECT DISTINCT count_point_id
```
| Gold Column | Source Table | Source Column |
|------------|-------------|-------------|
| count_point_id | counts | count_point_id |
| road_name | counts | road_name |
| road_type | counts | road_type |
| road_category | counts | road_category |
| region_name | regions | name |
| local_authority_name | local_authorities | name |
| latitude | counts | latitude |
| longitude | counts | longitude |
| road_class | — | Classified from road_category |

---

### STREAMING GOLD

#### gold_national_intensity
```
CREATED FROM: Silver WHERE event_type = "national_intensity"
SOURCE API: /intensity
dropDuplicates: ["period_from"]
```
| Gold Column | Source (Producer Event) | Calculation |
|------------|----------------------|-------------|
| data_timestamp | timestamp | Direct from producer |
| period_from | from | Direct from API |
| period_to | to | Direct from API |
| forecast | intensity.forecast | Direct from API |
| actual | intensity.actual | Direct from API |
| intensity_index | intensity.index | Direct from API |
| forecast_vs_actual | — | actual - forecast |
| intensity_category | — | ≤50: Very Low, ≤100: Low, ≤200: Moderate, ≤300: High, >300: Very High |

---

#### gold_generation_mix
```
CREATED FROM: Silver WHERE event_type = "generation_mix"
SOURCE API: /generation
dropDuplicates: ["period_from", "fuel_type"]
```
| Gold Column | Source | Calculation |
|------------|--------|-------------|
| data_timestamp | timestamp | Direct |
| period_from | from | Direct |
| period_to | to | Direct |
| fuel_type | fuel | Direct (9 types) |
| fuel_percentage | percentage | Direct from API |
| energy_category | — | wind/solar/hydro→"Renewable", gas/coal→"Fossil Fuel", nuclear→"Nuclear", rest→"Other" |

---

#### gold_regional_intensity
```
CREATED FROM: Silver WHERE event_type = "regional_intensity"
SOURCE API: /regional
dropDuplicates: ["period_from", "region_id"]
```
| Gold Column | Source | Calculation |
|------------|--------|-------------|
| data_timestamp | timestamp | Direct |
| period_from | from | Direct |
| period_to | to | Direct |
| region_id | regionid | Direct (1-17) |
| region_name | shortname | Direct |
| dno_region | dnoregion | Direct |
| forecast | intensity.forecast | Direct |
| intensity_index | intensity.index | Direct |
| intensity_category | — | Same classification as national |

---

#### gold_regional_generation
```
CREATED FROM: Silver WHERE event_type = "regional_generation"
SOURCE API: /regional (generationmix per region)
dropDuplicates: ["period_from", "region_id", "fuel_type"]
```
| Gold Column | Source | Calculation |
|------------|--------|-------------|
| data_timestamp | timestamp | Direct |
| period_from | from | Direct |
| region_id | regionid | Direct |
| region_name | shortname | Direct |
| fuel_type | fuel | Direct (9 types) |
| fuel_percentage | perc | Direct from API |
| energy_category | — | Same classification |

---

#### gold_renewable_summary
```
CREATED FROM: Silver WHERE event_type = "generation_mix"
GROUP BY: period_from, energy_category
dropDuplicates: ["period_from", "energy_category"]
```
| Gold Column | Source | Calculation |
|------------|--------|-------------|
| period_from | from | Group key |
| energy_category | — | Classified from fuel_type |
| total_percentage | percentage | SUM of fuel_percentage per category |

---

## 3. COMPLETE DATA LINEAGE

```
SOURCE → BRONZE → SILVER → GOLD → SYNAPSE → POWER BI

BATCH:
traffic_counts API ──→ counts_clean/ ──→ counts/ ──┬→ fact_traffic_summary ──→ vw_traffic_summary
(602,250 rows)         (strings)        (typed)    ├→ fact_co2_emissions ────→ vw_co2_emissions
                                                    ├→ fact_vehicle_mix ─────→ vw_vehicle_mix
regions API ─────────→ regions_clean/ → regions/ ──┤→ fact_road_analysis ───→ vw_road_analysis
(11 rows)              (strings)       (typed)     ├→ fact_covid_impact ────→ vw_covid_impact
                                                    ├→ fact_busiest_roads ──→ vw_busiest_roads
local_authorities ───→ la_clean/ ────→ la/ ────────┤→ dim_location ─────────→ vw_dim_location
(214 rows)                                          └→ dim_date (generated) → vw_dim_date

STREAMING:
Carbon API ─→ Event Hub ─→ Bronze raw/ ─→ Silver/ ─┬→ gold_national_intensity → vw_stream_national_intensity
(every 30s)    (queue)      (append)     (latest)   ├→ gold_generation_mix ────→ vw_stream_generation_mix
                                                     ├→ gold_regional_intensity → vw_stream_regional_intensity
                                                     ├→ gold_regional_generation→ vw_stream_regional_generation
                                                     └→ gold_renewable_summary ─→ vw_stream_renewable_summary
```

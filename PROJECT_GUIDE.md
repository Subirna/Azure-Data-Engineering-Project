# UK Road Traffic Intelligence Platform — Step-by-Step Project Guide

## Project Overview

An end-to-end Azure Data Engineering project that ingests UK government transport data,
transforms it through a Medallion Architecture (Bronze → Silver → Gold), and serves
insights via Power BI dashboards.

### Architecture

```
UK Gov APIs (DfT Road Traffic)
        │
        ▼
Azure Data Factory (Orchestrator - triggers Databricks)
        │
        ▼
Azure Databricks (Ingestion + Transformation)
        │
        ├──▶ ADLS Gen2 Bronze (raw Parquet)
        ├──▶ ADLS Gen2 Silver (cleansed & typed)
        └──▶ ADLS Gen2 Gold (aggregated KPIs)
                │
                ▼
        Azure Synapse Analytics (SQL serving layer)
                │
                ▼
        Power BI Dashboard (4 pages)
```

### Azure Resources Used

| Resource | Name | Region | Purpose |
|----------|------|--------|---------|
| Resource Group | `rg-dataeng-training-uks` | UK South | Container for all resources |
| ADLS Gen2 Storage | `subiradls2026` | UK South | Data Lake (Bronze/Silver/Gold containers) |
| Azure Data Factory | `SubiADF` | UK South | Pipeline orchestration |
| Azure Databricks | `adb-training-bd` | East US | Spark transformations |
| Azure Synapse | `syn-bd-training-uk` | UK South | SQL serving layer for Power BI |

### Data Sources

| Dataset | API Endpoint | Records | Format |
|---------|-------------|---------|--------|
| Regions | `/api/regions` | 11 | Plain JSON list |
| Local Authorities | `/api/local-authorities` | 214 | Plain JSON list |
| Count Points | `/api/count-points` | 46,754 | Paginated JSON (data key) |
| Traffic Counts (AADF) | `/api/average-annual-daily-flow` | 600,551 | Paginated JSON (data key) |

---

## PHASE 1: Azure Infrastructure Setup (Done)

### Step 1: Resource Group
- Used existing training resource group: `rg-dataeng-training-uks` (UK South)
- This is the container for all project resources

### Step 2: Create ADLS Gen2 Storage Account
- Used existing: `subiradls2026` (UK South)
- Hierarchical Namespace: Enabled (makes it ADLS Gen2)
- Created 3 containers:
  - `bronze` — Raw data from APIs
  - `silver` — Cleansed & standardized data
  - `gold` — Business-ready aggregated tables

### Step 3: Create Azure Data Factory
- Used existing: `SubiADF`
- Git configuration: Configured later
- Identity: System Assigned Managed Identity

### Step 4: Create Azure Databricks Workspace
- Used existing: `adb-training-bd` (East US)
- Cluster: `ADB Cluster` (Standard_D4ds_v4, 16GB, 4 Cores)
- Runtime: 17.3 LTS (Apache Spark 4.0.0, Scala 2.13)
- Cluster ID: `0608-090316-1u4u3q1u`
- Data Access: Unity Catalog enabled

### Step 5: Create Azure Synapse Analytics
- Used existing: `syn-bd-training-uk` (UK South)
- Connected to `subiradls2026` gold container

---

## PHASE 2: ADF Linked Services & Datasets (Done)

### Step 6a: ADLS Gen2 Linked Service
1. ADF Studio → Manage → Linked services → + New
2. Select: Azure Data Lake Storage Gen2
3. Settings:
   - Name: `ls_adls_subiradls2026`
   - Authentication: Account key
   - Subscription: Azure subscription 1 (3a72be92...)
   - Storage account: `subiradls2026`
4. Test connection → Create

### Step 6b: HTTP Linked Service (UK Gov API)
1. ADF Studio → Manage → Linked services → + New
2. Select: HTTP
3. Settings:
   - Name: `ls_http_uk_gov_api`
   - Base URL: `https://roadtraffic.dft.gov.uk`
   - Authentication: Anonymous
4. Test connection → Create

### Step 6c: Databricks Linked Service
1. ADF Studio → Manage → Linked services → + New
2. Select: Azure Databricks (under **Compute** tab, NOT Data store)
3. Settings:
   - Name: `ls_azure_databricks`
   - Account selection: Enter manually
   - Workspace URL: `https://adb-7405604459989675.15.azuredatabricks.net`
   - Authentication: Access token
   - Access token: Generated from Databricks Settings → Developer → Access tokens
     - Token scope: "all APIs" (under Other APIs)
   - Cluster: Existing interactive cluster
   - Cluster ID: `0608-090316-1u4u3q1u`
4. Test connection → Create

> **Note:** When generating access token in Databricks:
> Settings → Developer → Access tokens → Generate new token
> Select Scope: Other APIs → API scope: "all APIs (not recommended)"
> Copy token immediately — it won't be shown again!

### Step 7: Create Datasets

#### Dataset 1: HTTP JSON Source (Traffic API)
1. Author → + → Dataset → HTTP → JSON
2. Settings:
   - Name: `ds_traffic_api_source`
   - Linked service: `ls_http_uk_gov_api`
   - Relative URL: leave blank
   - Import schema: None
3. Add Parameter: `relativeUrl` (String)
4. Connection tab → Relative URL → Add dynamic content → select `relativeUrl`
   - Expression: `@dataset().relativeUrl`

#### Dataset 2: ADLS Parquet Sink
1. Author → + → Dataset → Azure Data Lake Storage Gen2 → Parquet
2. Settings:
   - Name: `ds_adls_sink`
   - Linked service: `ls_adls_subiradls2026`
   - File path: leave blank
   - Import schema: None
   - Compression: snappy
3. Add Parameters:
   - `containerName` (String)
   - `folderPath` (String)
4. Connection tab:
   - File system (1st box) → dynamic content → `@dataset().containerName`
   - Directory (2nd box) → dynamic content → `@dataset().folderPath`
   - File name: leave blank

---

## PHASE 3: ADF Ingestion Pipeline (Done)

### Step 8: Create Pipeline `pl_ingest_traffic_data`

1. Author → + → Pipeline
2. Name: `pl_ingest_traffic_data`
3. Added 4 Copy Data activities:

| Activity Name | Source relativeUrl | Sink containerName | Sink folderPath |
|--------------|-------------------|-------------------|-----------------|
| Fetch Count Points | `/api/count-points` | `bronze` | `traffic/count_points` |
| Fetch Traffic Counts | `/api/average-annual-daily-flow?limit=50000` | `bronze` | `traffic/counts` |
| Fetch Regions | `/api/regions` | `bronze` | `traffic/regions` |
| Fetch Local Authorities | `/api/local-authorities` | `bronze` | `traffic/local_authorities` |

> **Important:** The original `/api/counts` endpoint does NOT exist.
> The correct endpoint is `/api/average-annual-daily-flow`

4. Each activity Source tab: Request method = GET
5. Debug → All 4 activities succeeded
6. Data landed in `bronze/traffic/` as Parquet files

### ADF Limitation Discovered
ADF Copy Activity saved the **API pagination wrapper** (current_page, total, etc.)
instead of the actual data records. The API returns:
```json
{
  "current_page": 1,
  "data": [ ...actual records... ],
  "total": 600551
}
```
ADF saved the outer object, not the `data` array inside.

**Solution:** Use Databricks for direct API ingestion with full pagination control.
ADF pipeline still serves as the **orchestrator** that triggers Databricks notebooks.

---

## PHASE 4: Databricks — Bronze Layer Ingestion (In Progress)

### Step 9: Connect Databricks to ADLS Gen2

#### Notebook: `01_mount_storage`

**Unity Catalog restrictions encountered:**
- `dbutils.fs.mount()` → blocked (not whitelisted)
- `spark._jsc.hadoopConfiguration()` → blocked (shared cluster)
- `spark.conf.set()` with account key → **WORKS on ADB Cluster**

**Working approach — Cell 1:**
```python
storage_account = "subiradls2026"
storage_key = "<YOUR_STORAGE_KEY>"  # Azure Portal → subiradls2026 → Access keys → key1

spark.conf.set(
    f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
    storage_key
)

# Test: List files in bronze container
files = dbutils.fs.ls(f"abfss://bronze@{storage_account}.dfs.core.windows.net/traffic/")
for f in files:
    print(f.name, f.size)
```

> **Important:** Must use `ADB Cluster` (not Serverless) — select cluster
> from the dropdown at top-right of notebook.

> **Important:** Hardcoding storage keys is fine for training.
> In production, use Azure Key Vault + Databricks Secrets.

### Step 10: Fetch Clean Bronze Data from API

**Cell 2 — Ingestion with proper pagination:**
```python
import requests
import pandas as pd

BRONZE_PATH = f"abfss://bronze@{storage_account}.dfs.core.windows.net/traffic"

def safe_dataframe(data):
    pdf = pd.DataFrame(data)
    for col in pdf.columns:
        pdf[col] = pdf[col].astype(str)
    return spark.createDataFrame(pdf)

# 1. Regions — plain list (no pagination)
print("Fetching regions...")
resp = requests.get("https://roadtraffic.dft.gov.uk/api/regions", timeout=60)
df_regions = safe_dataframe(resp.json())
df_regions.write.mode("overwrite").parquet(f"{BRONZE_PATH}/regions_clean/")
print(f"Regions: {df_regions.count()} rows")

# 2. Local Authorities — plain list (no pagination)
print("Fetching local authorities...")
resp = requests.get("https://roadtraffic.dft.gov.uk/api/local-authorities", timeout=60)
df_la = safe_dataframe(resp.json())
df_la.write.mode("overwrite").parquet(f"{BRONZE_PATH}/local_authorities_clean/")
print(f"Local Authorities: {df_la.count()} rows")

# 3. Count Points — paginated (46,754 rows)
print("Fetching count points...")
all_cp = []
page = 1
while True:
    resp = requests.get("https://roadtraffic.dft.gov.uk/api/count-points",
                       params={"limit": 5000, "page": page}, timeout=120)
    result = resp.json()
    all_cp.extend(result["data"])
    print(f"  Page {page}/{result['last_page']}: {len(all_cp)} rows")
    if page >= result["last_page"]:
        break
    page += 1
df_cp = safe_dataframe(all_cp)
df_cp.write.mode("overwrite").parquet(f"{BRONZE_PATH}/count_points_clean/")
print(f"Count Points: {df_cp.count()} rows")

# 4. Traffic Counts AADF — paginated (600,551 rows, takes 5-10 minutes)
print("Fetching traffic counts (5-10 minutes)...")
all_counts = []
page = 1
while True:
    resp = requests.get("https://roadtraffic.dft.gov.uk/api/average-annual-daily-flow",
                       params={"limit": 10000, "page": page}, timeout=300)
    result = resp.json()
    all_counts.extend(result["data"])
    print(f"  Page {page}/{result['last_page']}: {len(all_counts)} rows")
    if page >= result["last_page"]:
        break
    page += 1
df_counts = safe_dataframe(all_counts)
df_counts.write.mode("overwrite").parquet(f"{BRONZE_PATH}/counts_clean/")
print(f"Traffic Counts: {df_counts.count()} rows, {len(df_counts.columns)} columns")

print("\n=== BRONZE LAYER COMPLETE ===")
```

**Expected output:**
```
Regions: 11 rows
Local Authorities: 214 rows
Count Points: 46,754 rows
Traffic Counts: 600,551 rows, 27 columns
=== BRONZE LAYER COMPLETE ===
```

**Data saved to:** `abfss://bronze@subiradls2026.dfs.core.windows.net/traffic/`
- `regions_clean/`
- `local_authorities_clean/`
- `count_points_clean/`
- `counts_clean/`

---

## PHASE 5: Databricks — Silver Layer Transformation (Next)

### Step 11: Silver Transformation Notebook

Create new notebook: `02_silver_transform`

**Purpose:** Cleanse, deduplicate, type-cast, and standardize Bronze data.

**Transformations:**
- Cast string columns to proper types (int, float, date)
- Standardize text (trim, uppercase road names)
- Filter UK coordinates (lat 49-61, lon -8 to 2)
- Remove duplicates
- Add derived columns (time_period, hgv_percentage)
- Add processing timestamp

**Code will be provided in next step.**

---

## PHASE 6: Databricks — Gold Layer Transformation (Pending)

### Step 12: Gold Transformation Notebooks

Three notebooks for business domains:

1. **`03_gold_traffic_analysis`** — Daily traffic summary, hourly peaks, YoY regional comparison
2. **`04_gold_road_safety`** — Accident hotspots, severity analysis, casualty demographics
3. **`05_gold_environmental`** — CO2 emissions estimates, vehicle mix trends, green transport index

---

## PHASE 7: Synapse SQL Serving Layer (Pending)

### Step 13: Create External Tables & Views

1. Open Synapse Studio (`syn-bd-training-uk`)
2. Run `create_schemas.sql` — creates bronze, silver, gold, reporting schemas
3. Run `create_external_tables.sql` — external tables pointing to Gold Parquet files
4. Run reporting views:
   - `vw_traffic_summary.sql`
   - `vw_accident_hotspots.sql`
   - `vw_environmental_metrics.sql`
   - `vw_infrastructure_planning.sql`

---

## PHASE 8: Power BI Dashboard (Pending)

### Step 14: Connect Power BI to Synapse

1. Open Power BI Desktop
2. Get Data → Azure Synapse Analytics
3. Server: `syn-bd-training-uk.sql.azuresynapse.net`
4. Database: `traffic_dwh`
5. Import the `reporting` schema views

### Dashboard Pages:

| Page | View Used | Key Visuals |
|------|----------|-------------|
| 1. Traffic Volume | `vw_traffic_summary` | Traffic by region bar chart, YoY trend line, vehicle type donut, map |
| 2. Road Safety | `vw_accident_hotspots`, `vw_accident_trends` | Hotspot map, severity by weather, KSI trend |
| 3. Environmental | `vw_co2_emissions`, `vw_green_transport` | CO2 by region, green transport index, cycle mode share |
| 4. Infrastructure | `vw_congestion_analysis`, `vw_capacity_utilisation` | Congestion heatmap, peak vs off-peak, capacity gauge |

### Key DAX Measures:
```dax
Total Traffic = SUM('fact_daily_traffic'[total_all_vehicles])
KSI Rate = DIVIDE(SUM([ksi_count]), SUM([total_collisions]), 0) * 100
Green Index = DIVIDE(SUM([cycles]) + SUM([buses]), SUM([total]), 0) * 100
CO2 Per Vehicle = DIVIDE(SUM([total_co2_tonnes]) * 1000, SUM([total_vehicle_count]), 0)
```

---

## Troubleshooting Notes

### ADF Issues
- `/api/counts` returns 404 → Use `/api/average-annual-daily-flow` instead
- ADF saves API wrapper not data → Use Databricks for ingestion
- Base URL must NOT have trailing path when relative URL starts with `/api/`

### Databricks Issues
- `dbutils.fs.mount()` blocked → Unity Catalog restriction, use `abfss://` paths directly
- `spark._jsc` blocked → Shared cluster restriction, use `spark.conf.set()` instead
- `spark.conf.set()` blocked on Serverless → Must use `ADB Cluster` (dedicated)
- Mixed types in JSON → Use `pd.DataFrame().astype(str)` then cast in Silver layer
- Access token scope error → Generate token with "all APIs" scope

### Storage Access
- Always use full ABFSS path: `abfss://<container>@subiradls2026.dfs.core.windows.net/<path>`
- Storage key from: Azure Portal → subiradls2026 → Security + networking → Access keys → key1

---

## Progress Tracker

| Phase | Description | Status |
|-------|------------|--------|
| 1 | Azure Infrastructure | Done |
| 2 | ADF Linked Services & Datasets | Done |
| 3 | ADF Ingestion Pipeline | Done |
| 4 | Databricks Bronze Ingestion | In Progress |
| 5 | Databricks Silver Transformation | Pending |
| 6 | Databricks Gold Transformation | Pending |
| 7 | Synapse SQL Layer | Pending |
| 8 | Power BI Dashboard | Pending |

**Current Step:** Project complete — ADF pipeline orchestration pending

---

## PHASE 5: Databricks — Silver Layer (Done)

### Notebook: `03_silver_transform.py`

**Transformations applied:**
- Cast all string columns to proper types (IntegerType, DoubleType)
- Standardize text (UPPER road names, InitCap region names)
- Filter UK coordinates (lat 49-61, lon -8 to 2)
- Remove duplicates
- Add derived columns: total_vehicles, hgv_percentage
- Add _processed_timestamp

**Output:** `abfss://silver@subiradls2026.dfs.core.windows.net/traffic/`
- counts/ (600,750 rows)
- count_points/ (250 rows)
- regions/ (11 rows)
- local_authorities/ (214 rows)

---

## PHASE 6: Databricks — Gold Layer (Done)

### Notebook: `04_gold_transform.py`

**IMPORTANT:** Gold tables are written WITHOUT `.partitionBy("year")` to preserve
the year column in the Parquet schema. Using partitionBy removes the column from
the data and stores it only in the folder structure, which Synapse/Power BI cannot read.

**8 Gold Tables Created:**

| Table | Rows | Type | Key Columns |
|-------|------|------|-------------|
| fact_traffic_summary | 80 | Fact | year, region_name, road_type, total_all_vehicles, yoy_change_pct |
| fact_co2_emissions | 80 | Fact | year, region_name, total_co2_tonnes, co2_per_vehicle_kg |
| fact_vehicle_mix | 80 | Fact | year, region_name, cars, hgvs, green_transport_index |
| fact_road_analysis | 174 | Fact | year, region_name, road_class, vehicles_per_km |
| fact_covid_impact | 28 | Fact | year, region_name, recovery_pct, baseline_2019 |
| fact_busiest_roads | 12 | Fact | region_name, road_name, total_vehicles, rank |
| dim_location | 12 | Dimension | count_point_id, latitude, longitude, region_name |
| dim_date | 9,497 | Dimension | year, month, quarter, day_name |

**COVID Impact Fix:** The baseline_2019 calculation uses a JOIN approach
(not window function) to correctly populate the 2019 baseline values.

**Output:** `abfss://gold@subiradls2026.dfs.core.windows.net/`

---

## PHASE 7: Synapse SQL Layer (Done)

### File: `synapse/sql_scripts/synapse_complete_setup.sql`

**Setup Steps:**
1. Create database: `uk_traffic_db`
2. Create master key
3. Create SAS credential + external data source
4. Create 8 views on Gold tables
5. Test all views

**Key Fix:** When Gold tables are updated in Databricks, views must be
dropped and recreated in Synapse to pick up schema changes.

**Connection Details for Power BI:**
- Server: `syn-bd-training-uk-ondemand.sql.azuresynapse.net`
- Database: `uk_traffic_db`
- Authentication: Organizational account

---

## PHASE 8: Power BI Dashboard (Done)

### File: `Dash_board.pbix`

**Dashboard: UK Road Traffic Intelligence Dashboard (1 page executive summary)**

**Slicers (2):**
- Year dropdown (from vw_dim_date)
- Region dropdown (from vw_traffic_summary)

**KPI Cards (4):**
| Card | Table | Field | Aggregation |
|------|-------|-------|-------------|
| Total Vehicles | vw_traffic_summary | total_all_vehicles | Sum |
| Total CO2 Tonnes | vw_co2_emissions | total_co2_tonnes | Sum |
| Green Transport Index | vw_vehicle_mix | green_transport_index | Average |
| COVID Recovery % | vw_covid_impact | recovery_pct | Average |

**Charts (4):**
| Chart | Type | Table | X-axis | Y-axis | Legend |
|-------|------|-------|--------|--------|--------|
| Traffic Trend | Line | vw_vehicle_mix | year | total | region_name |
| Vehicle Mix | Donut | vw_vehicle_mix | — | cars, hgvs, lgvs, buses, cycles | — |
| CO2 by Region | Bar | vw_co2_emissions | total_co2_tonnes | region_name | — |
| Green Index | Line | vw_vehicle_mix | year | green_transport_index | region_name |

**Data Model (Star Schema):**
```
              vw_dim_date (year)
                    │
     ┌──────────────┼──────────────────┐──────────────┐
     ▼              ▼                  ▼              ▼
vw_traffic    vw_co2_         vw_vehicle    vw_covid_
_summary      emissions       _mix          impact
```

All relationships: `vw_dim_date (year)` → each fact table `(year)`

**Theme:** Dark theme applied

---

## PHASE 9: ADF Master Pipeline (Pending)

### Pipeline: `pl_master_orchestration`

**Flow:**
```
01_Setup_Config → 03_Silver_Transform → 04_Gold_Transform
```

**Activities (Databricks Notebook type):**
| Activity | Notebook Path | Purpose |
|----------|--------------|---------|
| 01_Setup_Config | /01_setup_config | Configure ADLS storage key |
| 03_Silver_Transform | /03_silver_transform | Cleanse Bronze → Silver |
| 04_Gold_Transform | /04_gold_transform | Aggregate Silver → Gold |

**Note:** 02_bronze_ingestion is NOT in the pipeline because:
- Data is already loaded (600K+ rows)
- It takes 30+ minutes
- Run manually when fresh data is needed

---

## Troubleshooting Notes (Updated)

### Gold Layer Issues
- `.partitionBy("year")` removes year from Parquet schema → DON'T use it
- After updating Gold tables in Databricks, DROP and CREATE views in Synapse
- COVID baseline_2019 uses JOIN approach, not window function

### Power BI Issues
- "Cyclic reference" → Delete all region_name relationships, keep only year
- Year column missing → Recreate Synapse views after Gold table update
- Data not refreshing → Delete table in Power Query Editor → re-add from source
- Slicer dropdown → Use classic Slicer (not new List Slicer)

### Synapse Issues
- "Content of directory cannot be listed" → Create SAS token credential
- "Cannot drop credential" → Drop data source first, then credential
- Schema cache → Drop and recreate views after Gold updates

---

## Progress Tracker

| Phase | Description | Status |
|-------|------------|--------|
| 1 | Azure Infrastructure | Done |
| 2 | ADF Linked Services & Datasets | Done |
| 3 | ADF Ingestion Pipeline | Done |
| 4 | Databricks Bronze Ingestion | Done |
| 5 | Databricks Silver Transformation | Done |
| 6 | Databricks Gold Transformation | Done |
| 7 | Synapse SQL Layer | Done |
| 8 | Power BI Dashboard | Done |
| 9 | ADF Master Pipeline | Pending |

# UK Road Traffic & Carbon Intensity Intelligence Platform
## Azure Data Engineering Project — Presentation Script (20 minutes)

---

## SLIDE 1: Title Slide (30 seconds)

**Title:** UK Road Traffic & Carbon Intensity Intelligence Platform
**Subtitle:** End-to-End Azure Data Engineering with Batch & Streaming Pipelines
**Presented by:** Subirna Muthurasa
**Date:** June 2026

---

## SLIDE 2: Agenda (30 seconds)

1. Project Overview & Business Problem
2. Architecture — Batch & Streaming
3. Data Sources
4. Azure Infrastructure
5. Batch Pipeline — Demo
6. Streaming Pipeline — Live Demo
7. Power BI Dashboards
8. Key Business Insights
9. Challenges & Solutions
10. Q&A

---

## SLIDE 3: Business Problem (1 minute)

**Problem Statement:**

The UK Department for Transport collects massive volumes of road traffic data
across 11 regions and 46,000+ count points. Decision-makers need:

- How has traffic changed over 25 years (2000-2025)?
- What is the environmental impact (CO2 emissions)?
- How did COVID-19 affect UK road traffic?
- Which regions need infrastructure investment?
- What is the UK's current energy carbon intensity?

**Solution:**

Built an end-to-end Azure Data Engineering platform with:
- **Batch pipeline** — Processes 600,000+ historical traffic records
- **Streaming pipeline** — Processes real-time carbon intensity data every 30 seconds

---

## SLIDE 4: Architecture — Batch Pipeline (1 minute)

```
┌──────────────┐     ┌──────────┐     ┌─────────────────────────┐
│ UK Gov DfT   │────▶│   ADF    │────▶│  ADLS Gen2 (Raw)        │
│ Traffic API  │     │ Copy Data│     │  subiradls2026           │
└──────────────┘     └──────────┘     └────────────┬────────────┘
                                                    │
                                                    ▼
                                      ┌─────────────────────────┐
                                      │  Azure Databricks       │
                                      │  ┌───────┐ ┌───────┐   │
                                      │  │Bronze │→│Silver │   │
                                      │  │602K   │ │Cleansed│  │
                                      │  │rows   │ │& typed │  │
                                      │  └───────┘ └───┬───┘   │
                                      │                 │       │
                                      │            ┌────▼────┐  │
                                      │            │  Gold   │  │
                                      │            │8 tables │  │
                                      │            └─────────┘  │
                                      └────────────┬────────────┘
                                                    │
                                      ┌─────────────▼───────────┐
                                      │  Azure Synapse          │
                                      │  8 SQL Views            │
                                      └────────────┬────────────┘
                                                    │
                                      ┌─────────────▼───────────┐
                                      │  Power BI Dashboard     │
                                      │  Traffic Intelligence   │
                                      └─────────────────────────┘
```

**Say:** "Our batch pipeline ingests historical UK road traffic data through ADF, transforms it
in Databricks using the Medallion Architecture, serves it through Synapse SQL views,
and visualizes it in Power BI."

---

## SLIDE 5: Architecture — Streaming Pipeline (1 minute)

```
┌──────────────┐     ┌──────────┐     ┌─────────────────────────┐
│ UK Carbon    │────▶│  Azure   │────▶│  Azure Databricks       │
│ Intensity    │     │ Event Hub│     │  Structured Streaming   │
│ API          │     │          │     │  ┌───────┐ ┌───────┐   │
│ (every 30s)  │     │          │     │  │Bronze │→│Silver │   │
└──────────────┘     └──────────┘     │  └───────┘ └───┬───┘   │
                                      │                 │       │
                                      │            ┌────▼────┐  │
                                      │            │  Gold   │  │
                                      │            │5 tables │  │
                                      │            └─────────┘  │
                                      └────────────┬────────────┘
                                                    │
                                      ┌─────────────▼───────────┐
                                      │  Azure Synapse          │
                                      │  4 SQL Views            │
                                      └────────────┬────────────┘
                                                    │
                                      ┌─────────────▼───────────┐
                                      │  Power BI Dashboard     │
                                      │  Carbon Intensity       │
                                      └─────────────────────────┘
```

**Say:** "Our streaming pipeline captures real-time UK carbon intensity data every 30 seconds
through Azure Event Hub, processes it in Databricks, and displays live insights
in Power BI."

---

## SLIDE 6: Data Sources (1 minute)

### Batch Data — UK DfT Road Traffic API

| Dataset | Records | Description |
|---------|---------|-------------|
| Traffic Counts (AADF) | 602,250 | Annual average daily traffic flow by count point |
| Regions | 11 | UK geographic regions |
| Local Authorities | 214 | Local council areas |
| Count Points | 46,754 | Physical traffic counting locations |

**API:** roadtraffic.dft.gov.uk/api
**Covers:** Years 2000-2025, all 11 UK regions, 13 vehicle types

### Streaming Data — UK Carbon Intensity API

| Dataset | Frequency | Description |
|---------|-----------|-------------|
| National Intensity | Every 30 min | CO2 grams per kWh |
| Generation Mix | Every 30 min | 9 fuel types (wind, solar, gas, nuclear...) |
| Regional Intensity | Every 30 min | 17 UK regions |

**API:** api.carbonintensity.org.uk (free, no auth required)

---

## SLIDE 7: Azure Infrastructure (1 minute)

| Resource | Name | Purpose |
|----------|------|---------|
| Resource Group | rg-dataeng-training-uks | Container for all resources |
| ADLS Gen2 | subiradls2026 | Data Lake (Bronze/Silver/Gold) |
| Azure Data Factory | SubiADF | Pipeline orchestration |
| Azure Databricks | adb-training-bd | Spark transformations |
| Azure Synapse | syn-bd-training-uk | SQL serving layer |
| Azure Event Hub | eh-uk-traffic-subirna | Streaming message broker |
| Power BI | Desktop | Dashboards |

**Say:** "All resources are deployed in UK South region within a single resource group."

---

## SLIDE 8: Medallion Architecture (1 minute)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   BRONZE    │────▶│   SILVER    │────▶│    GOLD     │
│   (Raw)     │     │  (Cleansed) │     │ (Business)  │
├─────────────┤     ├─────────────┤     ├─────────────┤
│ Raw JSON/   │     │ Type-cast   │     │ Aggregated  │
│ Parquet     │     │ Validated   │     │ KPIs        │
│ As-is from  │     │ UK coords   │     │ Star schema │
│ API         │     │ filtered    │     │ Ready for   │
│             │     │ Derived     │     │ Power BI    │
│             │     │ columns     │     │             │
│ 602,250 rows│     │ 602,250 rows│     │ 8 tables    │
└─────────────┘     └─────────────┘     └─────────────┘
```

**Say:** "We follow the Medallion Architecture. Bronze stores raw data as-is.
Silver cleanses and type-casts. Gold creates business-ready aggregated tables."

---

## SLIDE 9: Gold Layer — Star Schema (1 minute)

### Batch Gold Tables (8)

| Table | Rows | Purpose |
|-------|------|---------|
| fact_traffic_summary | 286 | Traffic by region, year, YoY trends |
| fact_co2_emissions | 286 | CO2 estimates by region |
| fact_vehicle_mix | 286 | Vehicle type breakdown |
| fact_road_analysis | 1,704 | Road category comparison |
| fact_covid_impact | 77 | COVID recovery vs 2019 |
| fact_busiest_roads | 95 | Top busiest roads |
| dim_date | 9,497 | Date dimension |
| dim_location | 123 | Count point locations |

### Streaming Gold Tables (5)

| Table | Purpose |
|-------|---------|
| gold_national_intensity | Real-time CO2 intensity |
| gold_generation_mix | Energy source breakdown |
| gold_regional_intensity | Regional comparison |
| gold_regional_generation | Regional energy mix |
| gold_renewable_summary | Renewable vs Fossil |

---

## SLIDE 10: ADF Pipelines (1 minute)

### Batch Pipelines:

```
Pipeline 1: pl_ingest_traffic_data
├── Fetch Count Points    ✅
├── Fetch Traffic Counts  ✅
├── Fetch Regions         ✅
└── Fetch Local Auth      ✅

Pipeline 2: pl_batch_traffic_orchestration
├── Bronze_Ingestion      (Databricks)
├── Silver_Transform      (Databricks)
└── Gold_Transform        (Databricks)
```

### Streaming Pipeline:

```
Pipeline 3: pl_streaming_carbon_intensity
├── Produce_Events        (Databricks → Event Hub)
├── Stream_Bronze_Silver  (Event Hub → ADLS)
└── Stream_Gold           (Aggregations)
```

**Say:** "We have three ADF pipelines. Two for batch processing and one for
real-time streaming. Each pipeline orchestrates Databricks notebooks."

---

## SLIDE 11: Demo — Batch Pipeline (3 minutes)

### LIVE DEMO STEPS:

1. **Azure Portal** — Show resource group with all resources
2. **ADF Studio** — Show pl_ingest_traffic_data (4 Copy activities, all Succeeded)
3. **ADF Studio** — Show pl_batch_traffic_orchestration (3 Databricks notebooks)
4. **ADLS Gen2** — Browse Bronze/Silver/Gold containers
5. **Databricks** — Show notebook code (Bronze ingestion with 11 regions)
6. **Synapse Studio** — Run: SELECT * FROM vw_traffic_summary
7. **Power BI** — Open batch dashboard, filter by year, filter by region

### Key Points to Highlight:
- "We fetch data for all 11 UK regions using API pagination"
- "Bronze has 602,250 raw records across 25 years"
- "Gold layer creates 8 business-ready tables"
- "Year dropdown filters all visuals simultaneously"

---

## SLIDE 12: Demo — Streaming Pipeline (3 minutes)

### LIVE DEMO STEPS:

1. **Start producer** — Open CMD, run producer script
   → Show events being sent every 30 seconds
2. **Event Hub** — Show Azure Portal, messages flowing in
3. **ADF Pipeline** — Debug pl_streaming_carbon_intensity
   → Show 3 activities running: Producer → Bronze/Silver → Gold
4. **Power BI** — Refresh streaming dashboard
   → Numbers update with latest data!

### Demo Script:
"Let me show the streaming pipeline live. Our producer fetches
carbon intensity data every 30 seconds and sends it to Azure Event Hub.

[Show CMD with events flowing]

Databricks consumes these events, transforms through Bronze and Silver,
and creates Gold aggregation tables.

[Refresh Power BI]

The dashboard now shows 160 gCO2/kWh with moderate intensity.
Gas provides 39%, wind 18%, solar 14%. The forecast variance is -18,
meaning actual CO2 is lower than predicted — a positive environmental sign."

---

## SLIDE 13: Dashboard — Batch (1 minute)

[SCREENSHOT OF BATCH DASHBOARD]

### Key Business Insights:

1. **33 billion vehicles** counted across UK roads (2000-2025)
2. **89.84M tonnes CO2** estimated from road transport
3. **Cars dominate** at 75% of all vehicles
4. **COVID Impact** — Traffic dropped ~24% in 2020, recovered to 90.68% by 2023
5. **South East** has highest CO2 emissions — densest population
6. **Green Transport Index** increasing since 2010 — more cycling

---

## SLIDE 14: Dashboard — Streaming (1 minute)

[SCREENSHOT OF STREAMING DASHBOARD]

### Key Business Insights:

1. **Carbon Intensity: 160 gCO2/kWh** — moderate level currently
2. **Gas leads** at 39% of energy generation
3. **Renewables** (wind + solar + hydro) = ~32% of total energy
4. **South Wales** has highest regional intensity (fossil fuel dependent)
5. **Scotland** has very low intensity (wind energy dominant)
6. **Forecast Variance: -18** — UK producing less CO2 than predicted (positive)

---

## SLIDE 15: Challenges & Solutions (1 minute)

| Challenge | Solution |
|-----------|----------|
| API returns paginated JSON, ADF Copy couldn't extract nested data | Used Databricks for ingestion with full pagination control |
| API default pagination only returned 4 of 11 regions | Fetched region-by-region using filter[region_id] parameter |
| partitionBy("year") removed year column from Parquet | Removed partitionBy — year stays as normal column |
| COVID baseline calculation returned nulls | Changed from window function to JOIN-based approach |
| Databricks Unity Catalog blocked mount/config methods | Used spark.conf.set with storage account key |
| Synapse couldn't access ADLS without IAM permissions | Used SAS token credential instead |
| Power BI cyclic reference errors | Removed auto-detected relationships, kept only year-based |

**Say:** "These are real challenges we faced and solved during the project.
Each one taught us important lessons about Azure data engineering."

---

## SLIDE 16: Technology Stack (30 seconds)

| Category | Technology |
|----------|-----------|
| Cloud | Microsoft Azure |
| Storage | Azure Data Lake Storage Gen2 |
| Orchestration | Azure Data Factory |
| Processing | Azure Databricks (PySpark) |
| Streaming | Azure Event Hub |
| SQL Layer | Azure Synapse Analytics (Serverless) |
| Visualization | Power BI Desktop |
| Version Control | Git / GitHub |
| Infrastructure | Terraform (IaC) |
| Language | Python, SQL, PySpark |

---

## SLIDE 17: Data Model (30 seconds)

```
                    vw_dim_date (year)
                         │
          ┌──────────────┼──────────────┬──────────────┐
          │ 1:M          │ 1:M          │ 1:M          │ 1:M
          ▼              ▼              ▼              ▼
   vw_traffic      vw_co2_        vw_vehicle     vw_covid_
   _summary        emissions      _mix           impact

   Streaming tables: No relationships (standalone)
```

---

## SLIDE 18: Future Enhancements (30 seconds)

1. **Add accident data** — STATS19 road casualty statistics for road safety analysis
2. **Delta Lake** — Replace Parquet with Delta format for ACID transactions
3. **Real-time dashboard** — Power BI streaming dataset for auto-refresh
4. **CI/CD** — Azure DevOps pipeline for automated deployment
5. **Machine Learning** — Predict traffic congestion and accident risk
6. **Data Quality** — Great Expectations framework for automated validation

---

## SLIDE 19: Summary (30 seconds)

### What We Built:

| | Batch | Streaming |
|---|---|---|
| **Source** | UK DfT Traffic API | UK Carbon Intensity API |
| **Records** | 602,250 | Real-time (every 30s) |
| **Pipeline** | ADF → Databricks → Synapse | Event Hub → Databricks → Synapse |
| **Gold Tables** | 8 | 5 |
| **Dashboard** | Traffic Intelligence | Carbon Intensity |
| **Regions** | 11 UK regions | 17 UK regions |
| **Years** | 2000-2025 | Live |

### Key Achievement:
End-to-end Azure Data Engineering platform handling both
**historical batch processing** and **real-time streaming** with
professional Power BI dashboards.

---

## SLIDE 20: Q&A (remaining time)

**Thank You!**

**GitHub:** github.com/Subirna/Azure-Data-Engineering-Project

### Common Questions & Answers:

**Q: Why Views instead of External Tables?**
A: Views with OPENROWSET auto-adapt to schema changes. External tables
require manual DDL updates. Same data, same performance.

**Q: Why Databricks instead of ADF for ingestion?**
A: ADF Copy Activity saved the API pagination wrapper instead of actual data.
Databricks gave full control over JSON parsing and pagination.

**Q: How often does streaming run?**
A: Producer sends data every 30 seconds. ADF pipeline can be scheduled
every 5 minutes for automated processing.

**Q: What happens if the cluster is down?**
A: Event Hub retains messages for up to 24 hours. When the cluster starts,
it processes all pending events.

**Q: How do you handle data quality?**
A: Silver layer validates UK coordinates (lat 49-61, lon -8 to 2),
type-casts all columns, and removes nulls.

# UK Road Traffic & Safety Intelligence Platform

An end-to-end Azure Data Engineering project that ingests UK government transport data, transforms it through a Medallion Architecture (Bronze → Silver → Gold), and serves insights via Power BI dashboards.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────────┐
│  UK Gov APIs     │────▶│  Azure Data      │────▶│  Azure Data Lake     │
│  & CSV Datasets  │     │  Factory (ADF)   │     │  Gen2 (Bronze)       │
└─────────────────┘     └──────────────────┘     └──────────┬───────────┘
                                                            │
                                                            ▼
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────────┐
│  Power BI       │◀────│  Azure Synapse   │◀────│  Azure Databricks    │
│  Dashboard      │     │  Analytics       │     │  (Silver & Gold)     │
└─────────────────┘     └──────────────────┘     └──────────────────────┘
```

## Data Sources

| Dataset | Source | Format | Frequency |
|---------|--------|--------|-----------|
| UK Road Traffic Counts | roadtraffic.dft.gov.uk/api | JSON/CSV | Annual |
| UK Road Accidents (STATS19) | data.gov.uk | CSV | Monthly |
| UK Air Quality (DEFRA) | uk-air.defra.gov.uk | JSON | Hourly |
| UK Carbon Intensity | api.carbonintensity.org.uk | JSON | Real-time |

## Project Structure

```
├── infrastructure/          # Terraform IaC for Azure resources
│   └── terraform/
├── data_factory/            # ADF pipeline & linked service definitions
│   ├── pipelines/
│   ├── linked_services/
│   └── datasets/
├── databricks/              # Spark notebooks (Bronze → Silver → Gold)
│   ├── notebooks/
│   └── config/
├── synapse/                 # SQL serving layer
│   └── sql_scripts/
├── scripts/                 # Python ingestion & utility scripts
├── powerbi/                 # Power BI data model documentation
├── tests/                   # Data quality & transformation tests
└── config/                  # Pipeline & environment configuration
```

## Medallion Architecture

### Bronze Layer (Raw)
- Raw data ingested as-is from APIs and CSV files
- Stored in Parquet format in ADLS Gen2
- Partitioned by ingestion date

### Silver Layer (Cleansed)
- Data cleansed, deduplicated, and standardized
- Schema enforcement and type casting
- Null handling and data quality checks

### Gold Layer (Business-Ready)
- Aggregated dimension and fact tables
- Pre-computed KPIs and metrics
- Optimized for Power BI consumption

## Dashboard KPIs

1. **Traffic Volume Analysis** — Peak hours, YoY growth, COVID recovery trends
2. **Road Safety Intelligence** — Accident hotspots, severity correlations, weather impact
3. **Environmental Impact** — CO2 estimates by vehicle type, regional emissions
4. **Infrastructure Planning** — Congestion prediction, capacity utilization scores

## Setup

### Prerequisites
- Azure subscription
- Terraform >= 1.5
- Python >= 3.10
- Azure CLI
- Databricks CLI

### Deploy Infrastructure
```bash
cd infrastructure/terraform
terraform init
terraform plan -var-file="../../config/environment.yaml"
terraform apply
```

### Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Run Data Ingestion
```bash
python scripts/fetch_traffic_data.py
python scripts/fetch_accident_data.py
python scripts/upload_to_adls.py
```

## License
MIT

# UK Carbon Intensity — Streaming Pipeline Guide

## Architecture

```
UK Carbon Intensity API (api.carbonintensity.org.uk)
        │ (every 30 seconds)
        ▼
Python Producer Script (01_producer)
        │ (sends JSON events)
        ▼
Azure Event Hub (carbon-intensity-stream)
        │
        ▼
Databricks Structured Streaming (02_streaming)
        │
        ├──▶ ADLS Bronze (raw JSON → Parquet)
        ├──▶ ADLS Silver (parsed, cleansed)
        │
        ▼
Databricks Batch (03_gold_streaming)
        │
        ├──▶ gold_national_intensity
        ├──▶ gold_generation_mix
        ├──▶ gold_regional_intensity
        ├──▶ gold_regional_generation
        └──▶ gold_renewable_summary
                │
                ▼
        Synapse SQL Views (04_synapse)
                │
                ▼
        Power BI Streaming Dashboard
```

## Azure Resources

| Resource | Name | Purpose |
|----------|------|---------|
| Event Hub Namespace | `eh-uk-traffic-subira` | Message broker |
| Event Hub | `carbon-intensity-stream` | Receives carbon data events |
| ADLS Gen2 | `subiradls2026` | Bronze/Silver/Gold storage |
| Databricks | `adb-training-bd` | Stream processing |
| Synapse | `syn-bd-training-uk` | SQL views for Power BI |

## Data Source

**UK Carbon Intensity API** — Free, no auth required

| Endpoint | Data | Events per cycle |
|----------|------|-----------------|
| `/intensity` | National carbon intensity (gCO2/kWh) | 1 |
| `/generation` | Energy mix (9 fuel types) | 9 |
| `/regional` | 17 UK regions intensity | 17 |
| `/regional` | 17 regions × 9 fuel types | 153 |
| **Total** | | **~180 events every 30 seconds** |

## Setup Steps

### Step 1: Create Event Hub
1. Azure Portal → Event Hubs → Create
2. Namespace: `eh-uk-traffic-subira`, UK South, Basic tier
3. Create Event Hub: `carbon-intensity-stream`, 2 partitions
4. Copy connection string from Shared access policies

### Step 2: Run Producer
```bash
pip install azure-eventhub requests
python streaming/01_producer_carbon_intensity.py
```

### Step 3: Run Databricks Streaming
1. Upload `02_databricks_streaming_bronze_silver.py` to Databricks
2. Paste storage key and Event Hub connection string
3. Run all cells — streams will start automatically
4. Let it run for 5-10 minutes to accumulate data

### Step 4: Run Gold Aggregations
1. Upload `03_gold_streaming_aggregations.py` to Databricks
2. Run all cells to create 5 Gold tables

### Step 5: Create Synapse Views
1. Open Synapse Studio → SQL script
2. Run `04_synapse_streaming_views.sql`

### Step 6: Power BI Dashboard
1. Connect to Synapse → uk_traffic_db
2. Import the 5 streaming views
3. Create streaming dashboard page

## Streaming Gold Tables

| Table | Rows | Description |
|-------|------|-------------|
| gold_national_intensity | Growing | National CO2 intensity timeline |
| gold_generation_mix | Growing | Energy source breakdown (wind, solar, gas, etc.) |
| gold_regional_intensity | Growing | 17 UK regions intensity comparison |
| gold_regional_generation | Growing | Regional energy mix per region |
| gold_renewable_summary | Growing | Renewable vs Fossil vs Nuclear summary |

## Power BI Streaming Dashboard

### Visuals:
1. **Card** — Current Carbon Intensity (gCO2/kWh)
2. **Line Chart** — Intensity over time (forecast vs actual)
3. **Donut Chart** — Energy generation mix (wind, solar, gas, nuclear)
4. **Bar Chart** — Regional intensity comparison (17 regions)
5. **Stacked Area** — Renewable vs Fossil Fuel trend
6. **Table** — Regional details with intensity index

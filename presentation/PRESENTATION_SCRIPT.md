# Presentation Script — 20 Minutes
## Speak naturally, don't read word-by-word. Use this as a guide.

---

## SLIDE 1: Title (30 seconds)

"Good morning/afternoon everyone. My name is Subirna and today I'm going to present my Azure Data Engineering project. I've built an end-to-end data platform that processes UK road traffic data using a batch pipeline and UK carbon intensity data using a real-time streaming pipeline. Let me take you through it."

---

## SLIDE 2: Agenda (30 seconds)

"Here's what I'll cover today. I'll start with the business problem, then walk through both architectures, show you the data sources and infrastructure, explain the Medallion Architecture, and then do two live demos — one for batch and one for streaming. Finally I'll cover the challenges I faced and take your questions."

---

## SLIDE 3: Business Problem & Solution (1 minute)

"So what's the problem? The UK Department for Transport collects massive volumes of road traffic data — over 46,000 counting points across 11 regions, going back 25 years. But there was no unified platform to analyse this data. Decision-makers couldn't easily answer questions like: How has traffic changed over time? What's the environmental impact? How did COVID affect UK roads?

On top of that, the UK is pushing towards net zero, so understanding real-time carbon intensity is critical.

Our solution is a complete Azure platform with two pipelines. The batch pipeline processes 602,000 historical traffic records. The streaming pipeline captures real-time carbon intensity data every 30 seconds. Both feed into professional Power BI dashboards."

---

## SLIDE 4: Batch Architecture (1 minute)

"Let me walk you through the batch architecture. 

Starting from the left — we have the UK Government's DfT Traffic API as our source. Azure Data Factory copies the raw data into ADLS Gen2. Then Databricks takes over with our Medallion Architecture — Bronze stores the raw data, Silver cleanses and type-casts it, and Gold creates 8 aggregated business tables.

These Gold tables are then exposed through Azure Synapse SQL views, which Power BI connects to for the dashboard.

The key numbers here — 602,000 records, 11 UK regions, 25 years of data, and 8 Gold tables."

---

## SLIDE 5: Streaming Architecture (1 minute)

"The streaming architecture follows a similar pattern but with real-time data.

We have the UK Carbon Intensity API as our source, which provides live energy data. A Python producer fetches this data every 30 seconds and sends it to Azure Event Hub — our message broker.

Databricks then consumes these events from Event Hub, processes them through Bronze and Silver, and creates 5 Gold aggregation tables.

These are served through Synapse views to a separate Power BI streaming dashboard. Around 190 events flow through the pipeline every cycle."

---

## SLIDE 6: Data Sources & Infrastructure (1 minute)

"Let me quickly cover our data sources. For batch, we use the DfT Road Traffic API — it gives us annual average daily flow data with 13 vehicle types across all UK regions. Completely free, no authentication needed.

For streaming, we use the Carbon Intensity API — also free — which gives us national and regional intensity in grams of CO2 per kilowatt hour, plus the energy generation mix across 9 fuel types.

At the bottom you can see our Azure infrastructure — ADLS Gen2 for storage, Data Factory for orchestration, Databricks for processing, Synapse for the SQL layer, Event Hub for streaming, and Power BI for visualisation."

---

## SLIDE 7: Medallion Architecture (1 minute)

"We follow the Medallion Architecture with three layers.

Bronze is our raw layer — data comes in as-is from the API, all columns stored as strings in Parquet format. One important thing here — we had to fetch data region by region because the API's default pagination only returned 4 of the 11 UK regions.

Silver is our cleansed layer — we type-cast strings to integers and doubles, validate UK coordinates to filter out any bad data, standardise road names to uppercase, and create derived columns like total vehicles and HGV percentage.

Gold is our business layer — 8 aggregated tables in a star schema, ready for Power BI. One critical lesson here — we do NOT use partitionBy when writing Gold tables, because that removes the year column from the Parquet schema, which breaks the dashboard filtering."

---

## SLIDE 8: Gold Tables & Data Model (1 minute)

"Here are our Gold tables. On the left, batch has 8 tables — traffic summary, CO2 emissions, vehicle mix, road analysis, COVID impact, busiest roads, and two dimension tables for date and location.

On the right, streaming has 5 tables — national intensity, generation mix, regional intensity, regional generation, and a renewable vs fossil summary.

For the data model, we use a star schema where dim_date connects to all fact tables through the year column with one-to-many relationships. The streaming tables are standalone — they don't need relationships.

In total, Synapse has 12 SQL views — 8 for batch, 4 for streaming."

---

## SLIDE 9: ADF Pipelines (1 minute)

"We have three ADF pipelines. 

Pipeline 1 is our batch ingestion — 4 Copy Data activities that pull raw data from the UK Government API into ADLS.

Pipeline 2 is our batch transformation — 3 Databricks notebooks running in sequence: Bronze ingestion, Silver transformation, Gold aggregation.

Pipeline 3 is our streaming pipeline — also 3 Databricks notebooks: the producer sends data to Event Hub, the consumer processes it through Bronze and Silver, and the Gold notebook creates the aggregations. One click on Debug runs the entire streaming pipeline automatically.

Let me now show you the batch pipeline in action."

---

## SLIDE 10: Batch Demo (30 seconds intro, then switch to live)

"For the batch demo, I'm going to walk you through the complete pipeline — starting from Azure Portal showing all our resources, then ADF where you can see our pipelines succeeded, ADLS where the data sits in Bronze, Silver, and Gold containers, Databricks where the transformation notebooks live, Synapse where we query the Gold layer with SQL, and finally the Power BI dashboard.

Let me switch to Azure now..."

### BATCH DEMO — What to show (3 minutes):

1. **Azure Portal** → Open `rg-dataeng-training-uks` → show all resources
2. **ADF** → Show `pl_ingest_traffic_data` (4 green checkmarks)
3. **ADF** → Show `pl_batch_traffic_orchestration` (3 notebooks)
4. **ADLS** → Click `subiradls2026` → Storage browser → show bronze/silver/gold containers → click into gold → show 8 folders
5. **Databricks** → Open a notebook briefly → show the code
6. **Synapse** → Run `SELECT TOP 5 * FROM vw_traffic_summary`
7. **Power BI** → Open batch dashboard

---

## BATCH DASHBOARD SCRIPT (speak while showing the dashboard)

"This is our UK Road Traffic Intelligence Dashboard. Let me walk you through it.

### KPI Cards (point to each one):
Starting at the top — we have 5 KPI cards.

**33 billion total vehicles** — that's the cumulative count of all vehicles recorded across UK roads from 2000 to 2025. This includes cars, trucks, buses, cycles — everything.

**89.84 million tonnes of CO2** — this is our estimated carbon emissions from road transport. We calculated this using the UK Government's BEIS emission factors — for example, an average car emits 164 grams of CO2 per kilometre, a heavy goods vehicle emits 586 grams.

**Green Transport Index at 0.70** — this measures the proportion of sustainable transport, calculated as cycling plus public buses divided by total vehicles. A higher number means more green transport.

**3K Count Points Observed** — these are the physical locations on UK roads where traffic is counted.

**COVID Recovery at 90.68%** — this tells us that UK traffic has recovered to about 91% of pre-COVID 2019 levels. So we're almost back to normal but not quite.

### Line Chart (Traffic Trend):
Looking at the traffic trend by region — you can see all 11 UK regions over 25 years. Notice the sharp dip around 2020 — that's COVID. South East and North West consistently have the highest traffic volumes. What's interesting is you can see regions like Scotland and East Midlands jumping after 2012 — that's when the DfT expanded their counting network.

### Donut Chart (Vehicle Mix):
The vehicle type breakdown shows cars dominate at 75% of all traffic. LGVs — light goods vehicles like delivery vans — make up about 14%. HGVs are about 10%. Buses and cycles are less than 1% combined. This tells us there's a huge opportunity for electric vehicle transition since cars are such a large share.

### Bar Chart (CO2 by Region):
CO2 emissions by region — South East is the highest by far, followed by North West. This correlates directly with population density and traffic volume. Scotland and South West have much lower emissions.

### Table (Regional Ranking):
The table shows each region ranked by total vehicles with year-over-year change. Scotland has the highest YoY growth at 23.65%, which is interesting — could be economic growth or expanded road network. London has the lowest growth at 0.39%, possibly because more people are using public transport.

### Green Transport Trend:
Finally, the green transport index trend shows how sustainable transport has evolved. You can see it's generally been increasing since 2010, which is encouraging — more cycling infrastructure and better bus services.

### Filtering Demo:
Let me show the interactivity — if I select year 2020 from the dropdown, watch how all the numbers change... you can see the COVID impact clearly. And if I select just Scotland from the region filter... now we see Scotland-specific data only."

---

## SLIDE 11: Streaming Demo (30 seconds intro, then switch to live)

"Now let me show you the real-time streaming pipeline. This is completely live — I'm going to trigger the pipeline right now and you'll see actual UK carbon intensity data flowing through the system.

The ADF pipeline runs 3 notebooks automatically — first the producer fetches data from the Carbon Intensity API and sends it to Event Hub, then Databricks consumes and processes it, and finally the Gold tables are created. Let me switch to ADF and click Debug..."

### STREAMING DEMO — What to do (4 minutes):

1. **ADF** → Open `pl_streaming_carbon_intensity` → Click **Debug**
2. **While waiting** → Show Event Hub in Azure Portal → messages flowing
3. **Wait for success** → All 3 activities green (~4 minutes)
4. **Power BI** → Open streaming dashboard → Click **Refresh**
5. Walk through the dashboard

---

## STREAMING DASHBOARD SCRIPT (speak while showing the dashboard)

"This is our UK Real-Time Energy & Carbon Intensity Dashboard. This data was just captured moments ago from the live API.

### KPI Cards:
At the top — **Carbon Intensity is currently around 160 gCO2 per kilowatt hour** — that's moderate level. This means for every kilowatt hour of electricity generated right now in the UK, about 160 grams of CO2 is being produced.

**The intensity level is moderate** — the UK Carbon Intensity API classifies this into five levels: very low, low, moderate, high, and very high. Moderate means it's an average day.

**Forecast Variance is -18** — this is really interesting. It means the actual carbon intensity is 18 units LOWER than what was predicted. That's a positive sign — the UK is generating cleaner energy than expected, probably because wind or solar output is higher than forecasted today.

### Donut Chart (Energy Source Split):
The energy source split shows four categories. Renewables at about 42% — that's wind, solar, and hydro combined. Fossil fuels at 32% — mainly natural gas. Nuclear provides about 9% of baseload power. And other sources like biomass and imports make up the rest.

### Donut Chart (UK Energy Generation Mix):
Breaking it down further — gas is the single largest fuel at 39%. Wind is second at about 18%, then solar at 14%. Nuclear contributes 9.7%. What's notable is that renewables combined actually exceed gas — that's a significant milestone for UK energy.

### Bar Chart (Regional Intensity):
Looking at regional carbon intensity — South Wales has the highest intensity because it relies heavily on gas-fired power stations. Wales is second. Compare that to Scotland which has very low intensity — almost zero — because Scotland generates most of its electricity from wind farms.

This regional variation is really important for policy makers — it shows exactly where the UK needs to invest in clean energy infrastructure.

### Stacked Bar (Fuel Breakdown by Category):
The fuel breakdown shows what makes up each energy category. In the renewable bar, you can see wind and solar are roughly equal contributors. Fossil fuel is almost entirely gas — coal is essentially zero in the UK now. The other category includes biomass and imports.

### Table (Regional Details):
The table gives the detailed view — each region with its intensity value, level, and category. You can see the clear divide — Scottish regions are all 'very low', while Welsh and English regions are 'moderate' to 'high'. This is directly related to the energy infrastructure in each region.

### Real-time aspect:
The beauty of this dashboard is that it updates with live data. Every time we run the streaming pipeline and refresh Power BI, these numbers change based on what's actually happening in the UK energy grid right now."

---

## SLIDE 12: Challenges & Solutions (1 minute)

"Let me quickly cover some real challenges we faced.

The biggest one was the API only returning 4 out of 11 UK regions. We solved this by fetching region by region using a filter parameter.

ADF Copy Activity couldn't handle the nested JSON from the API — it saved the pagination wrapper instead of the actual data. So we moved ingestion to Databricks where we have full control.

We also discovered that using partitionBy on year removed the year column from the Parquet schema — which completely broke our Power BI filtering. The fix was simple — just remove partitionBy.

And for the COVID baseline calculation, the window function was returning nulls. We changed to a JOIN-based approach which worked perfectly.

Each of these challenges taught us important lessons about Azure data engineering."

---

## SLIDE 13: Future Enhancements (30 seconds)

"For future enhancements — we could add UK road accident data for safety analysis, migrate to Delta Lake for ACID transactions, set up a CI/CD pipeline with Azure DevOps, and potentially add machine learning to predict traffic congestion."

---

## SLIDE 14: Summary (30 seconds)

"To summarise — we've built a complete end-to-end Azure Data Engineering platform. Over 600,000 historical records processed through a batch pipeline, real-time carbon intensity data flowing through a streaming pipeline, 13 Gold tables served through Synapse, and two professional Power BI dashboards delivering actionable business insights.

Thank you."

---

## SLIDE 15: Q&A

### Common Questions & Answers:

**Q: Why did you use Views instead of External Tables in Synapse?**
"Views with OPENROWSET automatically adapt to schema changes in the Gold layer. If we add a new column in Databricks, the view picks it up without any DDL changes. External tables would require us to manually update the column definitions every time. Both read the same Parquet files — the end result is identical."

**Q: Why Databricks for ingestion instead of just ADF?**
"We initially tried ADF Copy Activity but it saved the API's pagination metadata instead of the actual data records. The API returns nested JSON with a 'data' array inside a wrapper object. ADF couldn't extract that nested array. Databricks gave us full Python control over JSON parsing, pagination, and region-by-region fetching."

**Q: How often does the streaming pipeline run?**
"The producer fetches data every 30 seconds. The ADF pipeline can be scheduled to run every 5 minutes using a tumbling window trigger. For the demo, we trigger it manually."

**Q: What happens if Event Hub goes down or the cluster is terminated?**
"Event Hub retains messages for up to 24 hours on the Basic tier. When the Databricks cluster restarts and the pipeline runs again, it processes all pending events from where it left off. No data is lost."

**Q: How do you ensure data quality?**
"In the Silver layer, we validate UK coordinates — latitude must be between 49 and 61, longitude between -8 and 2. We type-cast all columns from strings to proper types. We filter out nulls. And we use dropDuplicates on key columns. For the COVID baseline, we use a JOIN approach instead of a window function to avoid null values."

**Q: Why two separate dashboards instead of one?**
"They serve different business purposes. The batch dashboard is for historical trend analysis — traffic patterns, CO2 emissions over 25 years. The streaming dashboard is for real-time monitoring — what's happening right now with UK energy. Different audiences, different use cases. Also, they use different data sources and different Power BI themes to make them visually distinct."

**Q: What's the Green Transport Index?**
"It's calculated as cycles plus buses divided by total vehicles, multiplied by 100. It measures the proportion of sustainable transport modes. A higher value means more green transport in that region."

**Q: What does the COVID Recovery percentage mean?**
"It compares current traffic levels to the 2019 pre-COVID baseline. 90.68% means UK traffic is at about 91% of 2019 levels. It hasn't fully recovered — possibly because more people continue to work from home."

**Q: Why does the forecast variance matter?**
"A negative variance means actual CO2 is lower than predicted — the UK is generating cleaner energy than expected. A positive variance means more CO2 than predicted — dirtier energy. It's a real-time indicator of how well the UK is performing against its energy forecasts."

**Q: How would you scale this for production?**
"We would use Delta Lake instead of Parquet for ACID transactions, set up CI/CD with Azure DevOps, add data quality framework like Great Expectations, implement row-level security in Power BI, and schedule the pipelines with proper monitoring and alerting."

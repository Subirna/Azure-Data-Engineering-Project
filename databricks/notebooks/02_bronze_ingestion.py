# Databricks notebook source
# MAGIC %md
# MAGIC # 02 - Bronze Layer Ingestion
# MAGIC Fetches UK road traffic data from DfT API and saves to Bronze container.
# MAGIC
# MAGIC **IMPORTANT:** Fetches ALL 11 UK regions one by one to ensure complete data.
# MAGIC Takes 30-40 minutes due to API pagination (250 rows per page).
# MAGIC
# MAGIC **Run 01_setup_config FIRST** (or run Cell 1 below for storage key).

# COMMAND ----------

# Storage config (in case 01_setup_config was not run)
storage_account = "subiradls2026"
storage_key = "<PASTE_YOUR_KEY_IN_DATABRICKS>"

spark.conf.set(
    f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
    storage_key
)

# COMMAND ----------

import requests
import pandas as pd

BRONZE_PATH = f"abfss://bronze@{storage_account}.dfs.core.windows.net/traffic"

def safe_dataframe(data):
    pdf = pd.DataFrame(data)
    for col in pdf.columns:
        pdf[col] = pdf[col].astype(str)
    return spark.createDataFrame(pdf)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Fetch Regions (11 rows) — Plain list, no pagination

# COMMAND ----------

print("Fetching regions...")
resp = requests.get("https://roadtraffic.dft.gov.uk/api/regions", timeout=60)
df_regions = safe_dataframe(resp.json())
df_regions.write.mode("overwrite").parquet(f"{BRONZE_PATH}/regions_clean/")
print(f"Regions: {df_regions.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Fetch Local Authorities (214 rows) — Plain list, no pagination

# COMMAND ----------

print("Fetching local authorities...")
resp = requests.get("https://roadtraffic.dft.gov.uk/api/local-authorities", timeout=60)
df_la = safe_dataframe(resp.json())
df_la.write.mode("overwrite").parquet(f"{BRONZE_PATH}/local_authorities_clean/")
print(f"Local Authorities: {df_la.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Fetch Count Points — Paginated (46,754 rows)

# COMMAND ----------

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

# COMMAND ----------

# MAGIC %md
# MAGIC ## Fetch Traffic Counts (AADF) — ALL 11 Regions (602,250+ rows)
# MAGIC
# MAGIC Fetches region by region to ensure all 11 UK regions are included.
# MAGIC The default API pagination only returns ~4 regions worth of data.
# MAGIC Takes 30-40 minutes.

# COMMAND ----------

print("Fetching traffic counts for ALL 11 regions...")
all_data = []
for region_id in range(1, 12):
    page = 1
    while True:
        resp = requests.get(
            "https://roadtraffic.dft.gov.uk/api/average-annual-daily-flow",
            params={"limit": 10000, "page": page, "filter[region_id]": region_id},
            timeout=300
        )
        result = resp.json()
        if not result.get("data"):
            break
        all_data.extend(result["data"])
        print(f"  Region {region_id} - Page {page}/{result['last_page']}: {len(all_data)} total rows")
        if page >= result["last_page"]:
            break
        page += 1

df_counts = safe_dataframe(all_data)
df_counts.write.mode("overwrite").parquet(f"{BRONZE_PATH}/counts_clean/")
print(f"\nTotal rows: {df_counts.count()}")
print(f"Unique regions: {df_counts.select('region_id').distinct().count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Bronze Layer

# COMMAND ----------

print("=== BRONZE LAYER COMPLETE ===\n")
for folder in ["regions_clean", "local_authorities_clean", "count_points_clean", "counts_clean"]:
    df = spark.read.parquet(f"{BRONZE_PATH}/{folder}/")
    print(f"  {folder}: {df.count()} rows, {len(df.columns)} columns")

print(f"\nUnique regions in counts: {spark.read.parquet(f'{BRONZE_PATH}/counts_clean/').select('region_id').distinct().count()}")

# Databricks notebook source
# MAGIC %md
# MAGIC # 02 - Bronze Layer Ingestion
# MAGIC Fetches UK road traffic data from DfT API and saves to Bronze container.
# MAGIC Takes 30-40 minutes due to 600K+ rows pagination.
# MAGIC Run 01_setup_config FIRST.

# COMMAND ----------

import requests
import pandas as pd

storage_account = "subiradls2026"
BRONZE_PATH = f"abfss://bronze@{storage_account}.dfs.core.windows.net/traffic"

def safe_dataframe(data):
    pdf = pd.DataFrame(data)
    for col in pdf.columns:
        pdf[col] = pdf[col].astype(str)
    return spark.createDataFrame(pdf)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Fetch Regions (11 rows)

# COMMAND ----------

print("Fetching regions...")
resp = requests.get("https://roadtraffic.dft.gov.uk/api/regions", timeout=60)
df_regions = safe_dataframe(resp.json())
df_regions.write.mode("overwrite").parquet(f"{BRONZE_PATH}/regions_clean/")
print(f"Regions: {df_regions.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Fetch Local Authorities (214 rows)

# COMMAND ----------

print("Fetching local authorities...")
resp = requests.get("https://roadtraffic.dft.gov.uk/api/local-authorities", timeout=60)
df_la = safe_dataframe(resp.json())
df_la.write.mode("overwrite").parquet(f"{BRONZE_PATH}/local_authorities_clean/")
print(f"Local Authorities: {df_la.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Fetch Count Points - Paginated (46,754 rows)

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
# MAGIC ## Fetch Traffic Counts AADF - Paginated (600,551 rows) — Takes 30+ minutes

# COMMAND ----------

print("Fetching traffic counts (this takes 30+ minutes)...")
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

# COMMAND ----------

print("\n=== BRONZE LAYER COMPLETE ===")
for folder in ["regions_clean", "local_authorities_clean", "count_points_clean", "counts_clean"]:
    files = dbutils.fs.ls(f"{BRONZE_PATH}/{folder}/")
    print(f"  {folder}: {len(files)} files")

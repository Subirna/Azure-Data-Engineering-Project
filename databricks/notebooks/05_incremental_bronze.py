# Databricks notebook source
# MAGIC %md
# MAGIC # 05 - Incremental Bronze Ingestion
# MAGIC Checks Gold layer for latest year, fetches only NEW data from API.
# MAGIC Much faster than full load — only processes missing years.

# COMMAND ----------

import requests
import pandas as pd
from pyspark.sql import functions as F

storage_account = "subiradls2026"
storage_key = dbutils.secrets.get(scope="uk-traffic-vault", key="subiadls-account-key")

spark.conf.set(
    f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
    storage_key
)

BRONZE_PATH = f"abfss://bronze@{storage_account}.dfs.core.windows.net/traffic"
GOLD_PATH = f"abfss://gold@{storage_account}.dfs.core.windows.net"

def safe_dataframe(data):
    pdf = pd.DataFrame(data)
    for col in pdf.columns:
        pdf[col] = pdf[col].astype(str)
    return spark.createDataFrame(pdf)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Check Gold — What year do we already have?

# COMMAND ----------

try:
    df_gold = spark.read.parquet(f"{GOLD_PATH}/fact_traffic_summary/")
    latest_gold_year = df_gold.agg(F.max("year")).collect()[0][0]
    print(f"Gold layer has data up to year: {latest_gold_year}")
except:
    latest_gold_year = 1999
    print("Gold layer is empty — will do full load")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Check API — What years are available?

# COMMAND ----------

resp = requests.get(
    "https://roadtraffic.dft.gov.uk/api/average-annual-daily-flow",
    params={"limit": 1, "page": 1},
    timeout=60
)
api_data = resp.json()

sample_record = api_data["data"][0] if api_data.get("data") else None
if sample_record:
    print(f"API has data — sample year: {sample_record.get('year')}")
    print(f"Total records in API: {api_data.get('total')}")

# Check latest year available in API
resp_latest = requests.get(
    "https://roadtraffic.dft.gov.uk/api/average-annual-daily-flow",
    params={"limit": 1, "page": 1, "sort": "-year"},
    timeout=60
)
latest_api_data = resp_latest.json()
if latest_api_data.get("data"):
    latest_api_year = int(latest_api_data["data"][0]["year"])
    print(f"Latest year in API: {latest_api_year}")
else:
    latest_api_year = latest_gold_year
    print("Could not determine latest API year")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Compare — What's missing?

# COMMAND ----------

missing_years = list(range(latest_gold_year + 1, latest_api_year + 1))

if not missing_years:
    print(f"✅ Gold is up to date! Latest year: {latest_gold_year}")
    print("No new data to fetch — pipeline will skip ingestion.")
    dbutils.notebook.exit("NO_NEW_DATA")
else:
    print(f"📥 Missing years: {missing_years}")
    print(f"Gold has: up to {latest_gold_year}")
    print(f"API has: up to {latest_api_year}")
    print(f"Will fetch: {len(missing_years)} year(s)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Fetch ONLY missing years from API

# COMMAND ----------

all_new_data = []
for year in missing_years:
    print(f"\nFetching year {year}...")
    for region_id in range(1, 12):
        page = 1
        while True:
            resp = requests.get(
                "https://roadtraffic.dft.gov.uk/api/average-annual-daily-flow",
                params={
                    "limit": 10000,
                    "page": page,
                    "filter[region_id]": region_id,
                    "filter[year]": year
                },
                timeout=300
            )
            result = resp.json()
            if not result.get("data"):
                break
            all_new_data.extend(result["data"])
            print(f"  Region {region_id} - Page {page}/{result.get('last_page', '?')}: {len(all_new_data)} total")
            if page >= result.get("last_page", 0):
                break
            page += 1

if all_new_data:
    print(f"\n📥 Fetched {len(all_new_data)} new records for years {missing_years}")
else:
    print("No new data found in API")
    dbutils.notebook.exit("NO_NEW_DATA")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Append new data to Bronze

# COMMAND ----------

df_new = safe_dataframe(all_new_data)
df_new.write.mode("append").parquet(f"{BRONZE_PATH}/counts_clean/")
print(f"✅ Appended {df_new.count()} new records to Bronze")
print(f"Years added: {missing_years}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6: Also refresh reference data (Regions, Local Authorities)

# COMMAND ----------

print("Refreshing reference data...")

resp = requests.get("https://roadtraffic.dft.gov.uk/api/regions", timeout=60)
df_regions = safe_dataframe(resp.json())
df_regions.write.mode("overwrite").parquet(f"{BRONZE_PATH}/regions_clean/")
print(f"Regions: {df_regions.count()} rows")

resp = requests.get("https://roadtraffic.dft.gov.uk/api/local-authorities", timeout=60)
df_la = safe_dataframe(resp.json())
df_la.write.mode("overwrite").parquet(f"{BRONZE_PATH}/local_authorities_clean/")
print(f"Local Authorities: {df_la.count()} rows")

print("\n=== INCREMENTAL BRONZE COMPLETE ===")

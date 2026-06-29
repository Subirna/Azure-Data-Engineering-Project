# Databricks notebook source
# MAGIC %md
# MAGIC # 08 - Register Batch Tables in Unity Catalog
# MAGIC Registers Bronze, Silver, and Gold batch tables in Unity Catalog.
# MAGIC Run AFTER Gold transformation completes.

# COMMAND ----------

storage_account = "subiradls2026"
storage_key = dbutils.secrets.get(scope="uk-traffic-vault", key="subiadls-account-key")

spark.conf.set(
    f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
    storage_key
)

BRONZE_PATH = f"abfss://bronze@{storage_account}.dfs.core.windows.net/traffic"
SILVER_PATH = f"abfss://silver@{storage_account}.dfs.core.windows.net/traffic"
GOLD_PATH = f"abfss://gold@{storage_account}.dfs.core.windows.net"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Schemas

# COMMAND ----------

spark.sql("CREATE SCHEMA IF NOT EXISTS subirna_bronze")
spark.sql("CREATE SCHEMA IF NOT EXISTS subirna_silver")
spark.sql("CREATE SCHEMA IF NOT EXISTS subirna_gold")
print("Schemas created: subirna_bronze, subirna_silver, subirna_gold")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Register Bronze Tables (Raw Data)

# COMMAND ----------

bronze_tables = {
    "counts_clean": f"{BRONZE_PATH}/counts_clean/",
    "regions_clean": f"{BRONZE_PATH}/regions_clean/",
    "local_authorities_clean": f"{BRONZE_PATH}/local_authorities_clean/",
    "count_points_clean": f"{BRONZE_PATH}/count_points_clean/"
}

print("=== BRONZE LAYER ===")
for table_name, path in bronze_tables.items():
    df = spark.read.parquet(path)
    df.write.mode("overwrite").saveAsTable(f"subirna_bronze.{table_name}")
    print(f"✅ subirna_bronze.{table_name} ({df.count()} rows)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Register Silver Tables (Cleansed Data)

# COMMAND ----------

silver_tables = {
    "counts": f"{SILVER_PATH}/counts/",
    "regions": f"{SILVER_PATH}/regions/",
    "local_authorities": f"{SILVER_PATH}/local_authorities/",
    "count_points": f"{SILVER_PATH}/count_points/"
}

print("=== SILVER LAYER ===")
for table_name, path in silver_tables.items():
    df = spark.read.parquet(path)
    df.write.mode("overwrite").saveAsTable(f"subirna_silver.{table_name}")
    print(f"✅ subirna_silver.{table_name} ({df.count()} rows)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Register Gold Tables (Business Ready)

# COMMAND ----------

gold_tables = {
    "fact_traffic_summary": f"{GOLD_PATH}/fact_traffic_summary/",
    "fact_co2_emissions": f"{GOLD_PATH}/fact_co2_emissions/",
    "fact_vehicle_mix": f"{GOLD_PATH}/fact_vehicle_mix/",
    "fact_road_analysis": f"{GOLD_PATH}/fact_road_analysis/",
    "fact_covid_impact": f"{GOLD_PATH}/fact_covid_impact/",
    "fact_busiest_roads": f"{GOLD_PATH}/fact_busiest_roads/",
    "dim_location": f"{GOLD_PATH}/dim_location/",
    "dim_date": f"{GOLD_PATH}/dim_date/"
}

print("=== GOLD LAYER ===")
for table_name, path in gold_tables.items():
    df = spark.read.parquet(path)
    df.write.mode("overwrite").saveAsTable(f"subirna_gold.{table_name}")
    print(f"✅ subirna_gold.{table_name} ({df.count()} rows)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify All Batch Tables

# COMMAND ----------

print("=" * 60)
print("BATCH UNITY CATALOG — COMPLETE")
print("=" * 60)

for schema in ["subirna_bronze", "subirna_silver", "subirna_gold"]:
    tables = spark.sql(f"SHOW TABLES IN {schema}").collect()
    print(f"\n📁 {schema} ({len(tables)} tables):")
    for table in tables:
        count = spark.table(f"{schema}.{table.tableName}").count()
        print(f"   📄 {table.tableName}: {count} rows")

print("\n=== TEST QUERIES ===")

print("\nBronze → Silver → Gold progression:")
bronze_count = spark.table("subirna_bronze.counts_clean").count()
silver_count = spark.table("subirna_silver.counts").count()
gold_count = spark.table("subirna_gold.fact_traffic_summary").count()
print(f"  Bronze: {bronze_count} rows (raw)")
print(f"  Silver: {silver_count} rows (cleansed)")
print(f"  Gold:   {gold_count} rows (aggregated)")

print("\nGold sample:")
spark.sql("""
    SELECT region_name, year, total_all_vehicles, yoy_change_pct
    FROM subirna_gold.fact_traffic_summary
    WHERE year = 2023
    ORDER BY total_all_vehicles DESC
    LIMIT 5
""").show()

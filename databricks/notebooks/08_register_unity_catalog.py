# Databricks notebook source
# MAGIC %md
# MAGIC # 08 - Register Tables in Unity Catalog
# MAGIC Creates External Tables in Unity Catalog pointing to ADLS Gold Parquet files.
# MAGIC Run AFTER Gold transformation to register/update catalog entries.

# COMMAND ----------

storage_account = "subiradls2026"
storage_key = dbutils.secrets.get(scope="uk-traffic-vault", key="subiadls-account-key")

spark.conf.set(
    f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
    storage_key
)

GOLD_PATH = f"abfss://gold@{storage_account}.dfs.core.windows.net"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Schemas

# COMMAND ----------

spark.sql("CREATE SCHEMA IF NOT EXISTS gold")
spark.sql("CREATE SCHEMA IF NOT EXISTS streaming")
print("Schemas created: gold, streaming")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Register Batch Gold Tables (External)

# COMMAND ----------

batch_tables = [
    "fact_traffic_summary",
    "fact_co2_emissions",
    "fact_vehicle_mix",
    "fact_road_analysis",
    "fact_covid_impact",
    "fact_busiest_roads",
    "dim_location",
    "dim_date"
]

for table_name in batch_tables:
    spark.sql(f"DROP TABLE IF EXISTS gold.{table_name}")
    spark.sql(f"""
        CREATE TABLE gold.{table_name}
        USING PARQUET
        LOCATION '{GOLD_PATH}/{table_name}/'
    """)
    count = spark.table(f"gold.{table_name}").count()
    print(f"Registered: gold.{table_name} ({count} rows)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Register Streaming Gold Tables (External)

# COMMAND ----------

streaming_tables = [
    "gold_national_intensity",
    "gold_generation_mix",
    "gold_regional_intensity",
    "gold_regional_generation",
    "gold_renewable_summary"
]

for table_name in streaming_tables:
    spark.sql(f"DROP TABLE IF EXISTS streaming.{table_name}")
    spark.sql(f"""
        CREATE TABLE streaming.{table_name}
        USING PARQUET
        LOCATION '{GOLD_PATH}/streaming/{table_name}/'
    """)
    count = spark.table(f"streaming.{table_name}").count()
    print(f"Registered: streaming.{table_name} ({count} rows)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify All Catalog Tables

# COMMAND ----------

print("=== BATCH GOLD TABLES ===")
spark.sql("SHOW TABLES IN gold").show(truncate=False)

print("=== STREAMING GOLD TABLES ===")
spark.sql("SHOW TABLES IN streaming").show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test Queries Using Catalog Names

# COMMAND ----------

print("=== Test: Batch Traffic Summary ===")
spark.sql("SELECT region_name, year, total_all_vehicles FROM gold.fact_traffic_summary WHERE year = 2023 ORDER BY total_all_vehicles DESC LIMIT 5").show()

print("=== Test: Streaming Generation Mix ===")
spark.sql("SELECT fuel_type, fuel_percentage FROM streaming.gold_generation_mix ORDER BY fuel_percentage DESC").show()

print("\n=== UNITY CATALOG REGISTRATION COMPLETE ===")

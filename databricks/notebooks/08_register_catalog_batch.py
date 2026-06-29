# Databricks notebook source
# MAGIC %md
# MAGIC # 08 - Register Batch External Tables in Unity Catalog
# MAGIC Creates External Tables pointing to ADLS Parquet files for all layers.
# MAGIC Data stays in ADLS — catalog only has pointers.
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
# MAGIC ## Register Bronze External Tables (Raw Data)

# COMMAND ----------

bronze_tables = {
    "counts_clean": f"{BRONZE_PATH}/counts_clean/",
    "regions_clean": f"{BRONZE_PATH}/regions_clean/",
    "local_authorities_clean": f"{BRONZE_PATH}/local_authorities_clean/",
    "count_points_clean": f"{BRONZE_PATH}/count_points_clean/"
}

print("=== BRONZE LAYER (External Tables) ===")
for table_name, path in bronze_tables.items():
    spark.sql(f"DROP TABLE IF EXISTS subirna_bronze.{table_name}")
    spark.sql(f"""
        CREATE TABLE subirna_bronze.{table_name}
        USING PARQUET
        LOCATION '{path}'
    """)
    count = spark.table(f"subirna_bronze.{table_name}").count()
    print(f"✅ subirna_bronze.{table_name} ({count} rows) → {path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Register Silver External Tables (Cleansed Data)

# COMMAND ----------

silver_tables = {
    "counts": f"{SILVER_PATH}/counts/",
    "regions": f"{SILVER_PATH}/regions/",
    "local_authorities": f"{SILVER_PATH}/local_authorities/",
    "count_points": f"{SILVER_PATH}/count_points/"
}

print("=== SILVER LAYER (External Tables) ===")
for table_name, path in silver_tables.items():
    spark.sql(f"DROP TABLE IF EXISTS subirna_silver.{table_name}")
    spark.sql(f"""
        CREATE TABLE subirna_silver.{table_name}
        USING PARQUET
        LOCATION '{path}'
    """)
    count = spark.table(f"subirna_silver.{table_name}").count()
    print(f"✅ subirna_silver.{table_name} ({count} rows) → {path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Register Gold External Tables (Business Ready)

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

print("=== GOLD LAYER (External Tables) ===")
for table_name, path in gold_tables.items():
    spark.sql(f"DROP TABLE IF EXISTS subirna_gold.{table_name}")
    spark.sql(f"""
        CREATE TABLE subirna_gold.{table_name}
        USING PARQUET
        LOCATION '{path}'
    """)
    count = spark.table(f"subirna_gold.{table_name}").count()
    print(f"✅ subirna_gold.{table_name} ({count} rows) → {path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify All Batch External Tables

# COMMAND ----------

print("=" * 60)
print("BATCH EXTERNAL TABLES — COMPLETE")
print("=" * 60)

for schema in ["subirna_bronze", "subirna_silver", "subirna_gold"]:
    tables = spark.sql(f"SHOW TABLES IN {schema}").collect()
    print(f"\n📁 {schema} ({len(tables)} tables):")
    for table in tables:
        count = spark.table(f"{schema}.{table.tableName}").count()
        tbl_type = spark.sql(f"DESCRIBE EXTENDED {schema}.{table.tableName}").filter("col_name = 'Type'").collect()
        type_str = tbl_type[0][1] if tbl_type else "unknown"
        print(f"   📄 {table.tableName}: {count} rows | Type: {type_str}")

print("\n=== DATA LINEAGE ===")
bronze_count = spark.table("subirna_bronze.counts_clean").count()
silver_count = spark.table("subirna_silver.counts").count()
gold_count = spark.table("subirna_gold.fact_traffic_summary").count()
print(f"  Bronze: {bronze_count} rows (raw strings from API)")
print(f"  Silver: {silver_count} rows (typed, validated, derived columns)")
print(f"  Gold:   {gold_count} rows (aggregated by region, year)")

print("\n=== SAMPLE QUERY ===")
spark.sql("""
    SELECT region_name, year, total_all_vehicles, yoy_change_pct
    FROM subirna_gold.fact_traffic_summary
    WHERE year = 2023
    ORDER BY total_all_vehicles DESC
    LIMIT 5
""").show()

# Databricks notebook source
# MAGIC %md
# MAGIC # 09 - Register Streaming Tables in Unity Catalog
# MAGIC Registers streaming Gold tables in Unity Catalog.
# MAGIC Run AFTER streaming Gold transformation completes.

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
# MAGIC ## Create Schema

# COMMAND ----------

spark.sql("CREATE SCHEMA IF NOT EXISTS subirna_streaming")
print("Schema created: subirna_streaming")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Register Streaming Gold Tables

# COMMAND ----------

streaming_tables = {
    "gold_national_intensity": f"{GOLD_PATH}/streaming/gold_national_intensity/",
    "gold_generation_mix": f"{GOLD_PATH}/streaming/gold_generation_mix/",
    "gold_regional_intensity": f"{GOLD_PATH}/streaming/gold_regional_intensity/",
    "gold_regional_generation": f"{GOLD_PATH}/streaming/gold_regional_generation/",
    "gold_renewable_summary": f"{GOLD_PATH}/streaming/gold_renewable_summary/"
}

print("=== STREAMING LAYER ===")
for table_name, path in streaming_tables.items():
    df = spark.read.parquet(path)
    df.write.mode("overwrite").saveAsTable(f"subirna_streaming.{table_name}")
    print(f"✅ subirna_streaming.{table_name} ({df.count()} rows)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Streaming Tables

# COMMAND ----------

print("=" * 60)
print("STREAMING UNITY CATALOG — COMPLETE")
print("=" * 60)

tables = spark.sql("SHOW TABLES IN subirna_streaming").collect()
print(f"\n📁 subirna_streaming ({len(tables)} tables):")
for table in tables:
    count = spark.table(f"subirna_streaming.{table.tableName}").count()
    print(f"   📄 {table.tableName}: {count} rows")

print("\n=== TEST QUERIES ===")

print("\nGeneration Mix:")
spark.sql("""
    SELECT fuel_type, fuel_percentage, energy_category
    FROM subirna_streaming.gold_generation_mix
    ORDER BY fuel_percentage DESC
""").show()

print("\nRegional Intensity:")
spark.sql("""
    SELECT region_name, forecast, intensity_index
    FROM subirna_streaming.gold_regional_intensity
    ORDER BY forecast DESC
    LIMIT 5
""").show()

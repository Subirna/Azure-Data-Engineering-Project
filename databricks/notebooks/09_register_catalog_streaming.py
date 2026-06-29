# Databricks notebook source
# MAGIC %md
# MAGIC # 09 - Register Streaming External Tables in Unity Catalog
# MAGIC Creates External Tables pointing to ADLS streaming Gold Parquet files.
# MAGIC Data stays in ADLS — catalog only has pointers.
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
# MAGIC ## Register Streaming External Tables

# COMMAND ----------

streaming_tables = {
    "gold_national_intensity": f"{GOLD_PATH}/streaming/gold_national_intensity/",
    "gold_generation_mix": f"{GOLD_PATH}/streaming/gold_generation_mix/",
    "gold_regional_intensity": f"{GOLD_PATH}/streaming/gold_regional_intensity/",
    "gold_regional_generation": f"{GOLD_PATH}/streaming/gold_regional_generation/",
    "gold_renewable_summary": f"{GOLD_PATH}/streaming/gold_renewable_summary/"
}

print("=== STREAMING LAYER (External Tables) ===")
for table_name, path in streaming_tables.items():
    spark.sql(f"DROP TABLE IF EXISTS subirna_streaming.{table_name}")
    spark.sql(f"""
        CREATE TABLE subirna_streaming.{table_name}
        USING PARQUET
        LOCATION '{path}'
    """)
    count = spark.table(f"subirna_streaming.{table_name}").count()
    print(f"✅ subirna_streaming.{table_name} ({count} rows) → {path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Streaming External Tables

# COMMAND ----------

print("=" * 60)
print("STREAMING EXTERNAL TABLES — COMPLETE")
print("=" * 60)

tables = spark.sql("SHOW TABLES IN subirna_streaming").collect()
print(f"\n📁 subirna_streaming ({len(tables)} tables):")
for table in tables:
    count = spark.table(f"subirna_streaming.{table.tableName}").count()
    tbl_type = spark.sql(f"DESCRIBE EXTENDED subirna_streaming.{table.tableName}").filter("col_name = 'Type'").collect()
    type_str = tbl_type[0][1] if tbl_type else "unknown"
    print(f"   📄 {table.tableName}: {count} rows | Type: {type_str}")

print("\n=== SAMPLE QUERIES ===")

print("\nGeneration Mix:")
spark.sql("""
    SELECT fuel_type, fuel_percentage, energy_category
    FROM subirna_streaming.gold_generation_mix
    ORDER BY fuel_percentage DESC
""").show()

print("\nRegional Intensity (Top 5 highest):")
spark.sql("""
    SELECT region_name, forecast, intensity_index
    FROM subirna_streaming.gold_regional_intensity
    ORDER BY forecast DESC
    LIMIT 5
""").show()

print("\nRenewable Summary:")
spark.sql("""
    SELECT energy_category, total_percentage
    FROM subirna_streaming.gold_renewable_summary
    ORDER BY total_percentage DESC
""").show()

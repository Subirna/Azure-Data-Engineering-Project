# Databricks notebook source
# MAGIC %md
# MAGIC # 03 - Silver Layer Transformation
# MAGIC Cleanses, type-casts, and standardizes Bronze data into Silver layer.
# MAGIC
# MAGIC **Run 01_setup_config FIRST** (or run Cell 1 below for storage key).

# COMMAND ----------

# Storage config (in case 01_setup_config was not run)
storage_account = "subiradls2026"
storage_key = "<PASTE_KEY_FROM_AZURE_PORTAL: subiradls2026 > Security + networking > Access keys > key1>"

spark.conf.set(
    f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
    storage_key
)

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, DoubleType

BRONZE_PATH = f"abfss://bronze@{storage_account}.dfs.core.windows.net/traffic"
SILVER_PATH = f"abfss://silver@{storage_account}.dfs.core.windows.net/traffic"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver: Traffic Counts (602,250+ rows)
# MAGIC Type-cast strings to proper types, add derived columns, filter UK coordinates.

# COMMAND ----------

df_counts = spark.read.parquet(f"{BRONZE_PATH}/counts_clean/")

df_counts_silver = df_counts \
    .withColumn("count_point_id", F.col("count_point_id").cast(IntegerType())) \
    .withColumn("year", F.col("year").cast(IntegerType())) \
    .withColumn("region_id", F.col("region_id").cast(IntegerType())) \
    .withColumn("local_authority_id", F.col("local_authority_id").cast(IntegerType())) \
    .withColumn("latitude", F.col("latitude").cast(DoubleType())) \
    .withColumn("longitude", F.col("longitude").cast(DoubleType())) \
    .withColumn("pedal_cycles", F.col("pedal_cycles").cast(IntegerType())) \
    .withColumn("two_wheeled_motor_vehicles", F.col("two_wheeled_motor_vehicles").cast(IntegerType())) \
    .withColumn("cars_and_taxis", F.col("cars_and_taxis").cast(IntegerType())) \
    .withColumn("buses_and_coaches", F.col("buses_and_coaches").cast(IntegerType())) \
    .withColumn("lgvs", F.col("lgvs").cast(IntegerType())) \
    .withColumn("all_hgvs", F.col("all_hgvs").cast(IntegerType())) \
    .withColumn("all_motor_vehicles", F.col("all_motor_vehicles").cast(IntegerType())) \
    .withColumn("link_length_km", F.col("link_length_km").cast(DoubleType())) \
    .withColumn("road_name", F.upper(F.trim(F.col("road_name")))) \
    .withColumn("road_type", F.trim(F.col("road_type"))) \
    .withColumn("total_vehicles",
        F.col("pedal_cycles") + F.col("two_wheeled_motor_vehicles") +
        F.col("cars_and_taxis") + F.col("buses_and_coaches") +
        F.col("lgvs") + F.col("all_hgvs")
    ) \
    .withColumn("hgv_percentage",
        F.round(F.col("all_hgvs") / F.col("all_motor_vehicles") * 100, 2)
    ) \
    .filter(F.col("year").isNotNull()) \
    .filter(F.col("latitude").between(49.0, 61.0)) \
    .filter(F.col("longitude").between(-8.0, 2.0)) \
    .withColumn("_processed_timestamp", F.current_timestamp())

df_counts_silver.write.mode("overwrite").parquet(f"{SILVER_PATH}/counts/")
print(f"Silver Counts: {df_counts_silver.count()} rows")
print(f"Unique regions: {df_counts_silver.select('region_id').distinct().count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver: Count Points

# COMMAND ----------

df_cp = spark.read.parquet(f"{BRONZE_PATH}/count_points_clean/")

df_cp_silver = df_cp \
    .withColumn("count_point_id", F.col("count_point_id").cast(IntegerType())) \
    .withColumn("latitude", F.col("latitude").cast(DoubleType())) \
    .withColumn("longitude", F.col("longitude").cast(DoubleType())) \
    .withColumn("road_name", F.upper(F.trim(F.col("road_name")))) \
    .filter(F.col("latitude").between(49.0, 61.0)) \
    .filter(F.col("longitude").between(-8.0, 2.0)) \
    .dropDuplicates(["count_point_id"]) \
    .withColumn("_processed_timestamp", F.current_timestamp())

df_cp_silver.write.mode("overwrite").parquet(f"{SILVER_PATH}/count_points/")
print(f"Silver Count Points: {df_cp_silver.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver: Regions

# COMMAND ----------

df_regions = spark.read.parquet(f"{BRONZE_PATH}/regions_clean/")

df_regions_silver = df_regions \
    .withColumn("id", F.col("id").cast(IntegerType())) \
    .withColumn("name", F.initcap(F.trim(F.col("name")))) \
    .dropDuplicates(["id"]) \
    .withColumn("_processed_timestamp", F.current_timestamp())

df_regions_silver.write.mode("overwrite").parquet(f"{SILVER_PATH}/regions/")
print(f"Silver Regions: {df_regions_silver.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver: Local Authorities

# COMMAND ----------

df_la = spark.read.parquet(f"{BRONZE_PATH}/local_authorities_clean/")

df_la_silver = df_la \
    .withColumn("id", F.col("id").cast(IntegerType())) \
    .withColumn("name", F.initcap(F.trim(F.col("name")))) \
    .dropDuplicates(["id"]) \
    .withColumn("_processed_timestamp", F.current_timestamp())

df_la_silver.write.mode("overwrite").parquet(f"{SILVER_PATH}/local_authorities/")
print(f"Silver Local Authorities: {df_la_silver.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Silver Layer

# COMMAND ----------

print("=== SILVER LAYER COMPLETE ===\n")
for folder in ["counts", "count_points", "regions", "local_authorities"]:
    df = spark.read.parquet(f"{SILVER_PATH}/{folder}/")
    print(f"  {folder}: {df.count()} rows, {len(df.columns)} columns")

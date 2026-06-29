# Databricks notebook source
# MAGIC %md
# MAGIC # 06 - Incremental Silver Transformation
# MAGIC Processes ALL Bronze data (including new records) into Silver.
# MAGIC Overwrites Silver to ensure consistency.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, DoubleType

storage_account = "subiradls2026"
storage_key = dbutils.secrets.get(scope="uk-traffic-vault", key="subiadls-account-key")

spark.conf.set(
    f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
    storage_key
)

BRONZE_PATH = f"abfss://bronze@{storage_account}.dfs.core.windows.net/traffic"
SILVER_PATH = f"abfss://silver@{storage_account}.dfs.core.windows.net/traffic"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver: Traffic Counts (all data including new)

# COMMAND ----------

df_counts = spark.read.parquet(f"{BRONZE_PATH}/counts_clean/")
print(f"Bronze total records: {df_counts.count()}")
print(f"Years in Bronze: {df_counts.select('year').distinct().orderBy('year').rdd.flatMap(lambda x: x).collect()}")

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
print(f"Year range: {df_counts_silver.agg(F.min('year'), F.max('year')).collect()[0]}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver: Reference data (Regions, Local Authorities)

# COMMAND ----------

df_regions = spark.read.parquet(f"{BRONZE_PATH}/regions_clean/")
df_regions_silver = df_regions \
    .withColumn("id", F.col("id").cast(IntegerType())) \
    .withColumn("name", F.initcap(F.trim(F.col("name")))) \
    .dropDuplicates(["id"]) \
    .withColumn("_processed_timestamp", F.current_timestamp())
df_regions_silver.write.mode("overwrite").parquet(f"{SILVER_PATH}/regions/")
print(f"Silver Regions: {df_regions_silver.count()} rows")

df_la = spark.read.parquet(f"{BRONZE_PATH}/local_authorities_clean/")
df_la_silver = df_la \
    .withColumn("id", F.col("id").cast(IntegerType())) \
    .withColumn("name", F.initcap(F.trim(F.col("name")))) \
    .dropDuplicates(["id"]) \
    .withColumn("_processed_timestamp", F.current_timestamp())
df_la_silver.write.mode("overwrite").parquet(f"{SILVER_PATH}/local_authorities/")
print(f"Silver Local Authorities: {df_la_silver.count()} rows")

# COMMAND ----------

print("\n=== INCREMENTAL SILVER COMPLETE ===")

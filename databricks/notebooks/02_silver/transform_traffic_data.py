# Databricks notebook source
# MAGIC %md
# MAGIC # Silver Layer — Transform Traffic Data
# MAGIC Cleanses, deduplicates, and standardizes Bronze traffic data into Silver layer Delta tables.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, DoubleType, TimestampType

# COMMAND ----------

BRONZE_PATH = "/mnt/bronze/traffic"
SILVER_PATH = "/mnt/silver/traffic"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Transform Count Points

# COMMAND ----------

df_count_points = spark.read.format("delta").load(f"{BRONZE_PATH}/count_points")

df_count_points_silver = df_count_points \
    .withColumnRenamed("id", "count_point_id") \
    .withColumn("count_point_id", F.col("count_point_id").cast(IntegerType())) \
    .withColumn("latitude", F.col("latitude").cast(DoubleType())) \
    .withColumn("longitude", F.col("longitude").cast(DoubleType())) \
    .withColumn("road_name", F.upper(F.trim(F.col("road_name")))) \
    .withColumn("road_type", F.trim(F.col("road_type"))) \
    .withColumn("region_name", F.initcap(F.trim(F.col("region_name")))) \
    .withColumn("local_authority_name", F.initcap(F.trim(F.col("local_authority_name")))) \
    .filter(F.col("latitude").isNotNull() & F.col("longitude").isNotNull()) \
    .filter(
        (F.col("latitude").between(49.0, 61.0)) &
        (F.col("longitude").between(-8.0, 2.0))
    ) \
    .dropDuplicates(["count_point_id"]) \
    .withColumn("_processed_timestamp", F.current_timestamp())

df_count_points_silver.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(f"{SILVER_PATH}/count_points")

print(f"Silver count_points: {df_count_points_silver.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Transform Traffic Counts

# COMMAND ----------

df_counts = spark.read.format("delta").load(f"{BRONZE_PATH}/counts")

VEHICLE_COLUMNS = [
    "pedal_cycles", "two_wheeled_motor_vehicles", "cars_and_taxis",
    "buses_and_coaches", "lgvs", "all_hgvs", "all_motor_vehicles"
]

df_counts_silver = df_counts \
    .withColumn("count_point_id", F.col("count_point_id").cast(IntegerType())) \
    .withColumn("year", F.col("year").cast(IntegerType())) \
    .withColumn("count_date", F.to_date(F.col("count_date"), "yyyy-MM-dd")) \
    .withColumn("hour", F.col("hour").cast(IntegerType())) \
    .withColumn("direction_of_travel", F.upper(F.trim(F.col("direction_of_travel"))))

for col_name in VEHICLE_COLUMNS:
    df_counts_silver = df_counts_silver.withColumn(col_name, F.col(col_name).cast(IntegerType()))

df_counts_silver = df_counts_silver \
    .filter(F.col("year").isNotNull() & F.col("count_point_id").isNotNull()) \
    .filter(F.col("year").between(2000, 2025)) \
    .withColumn("total_vehicles",
        F.col("pedal_cycles") + F.col("two_wheeled_motor_vehicles") +
        F.col("cars_and_taxis") + F.col("buses_and_coaches") +
        F.col("lgvs") + F.col("all_hgvs")
    ) \
    .withColumn("hgv_percentage",
        F.round(F.col("all_hgvs") / F.col("total_vehicles") * 100, 2)
    ) \
    .withColumn("time_period",
        F.when(F.col("hour").between(7, 9), "morning_peak")
        .when(F.col("hour").between(10, 15), "inter_peak")
        .when(F.col("hour").between(16, 18), "evening_peak")
        .when(F.col("hour").between(19, 22), "evening")
        .otherwise("night")
    ) \
    .dropDuplicates(["count_point_id", "year", "count_date", "hour", "direction_of_travel"]) \
    .withColumn("_processed_timestamp", F.current_timestamp())

df_counts_silver.write.format("delta") \
    .mode("overwrite") \
    .partitionBy("year") \
    .option("overwriteSchema", "true") \
    .save(f"{SILVER_PATH}/counts")

print(f"Silver counts: {df_counts_silver.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Transform Regions & Local Authorities

# COMMAND ----------

for table_name in ["regions", "local_authorities"]:
    df = spark.read.format("delta").load(f"{BRONZE_PATH}/{table_name}")

    df_silver = df \
        .withColumn("name", F.initcap(F.trim(F.col("name")))) \
        .dropDuplicates(["id"]) \
        .withColumn("_processed_timestamp", F.current_timestamp())

    df_silver.write.format("delta") \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .save(f"{SILVER_PATH}/{table_name}")

    print(f"Silver {table_name}: {df_silver.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Quality Summary

# COMMAND ----------

for table in ["count_points", "counts", "regions", "local_authorities"]:
    df = spark.read.format("delta").load(f"{SILVER_PATH}/{table}")
    null_counts = {c: df.filter(F.col(c).isNull()).count() for c in df.columns[:5]}
    print(f"\n{table} ({df.count()} rows):")
    for col_name, nulls in null_counts.items():
        print(f"  {col_name}: {nulls} nulls")

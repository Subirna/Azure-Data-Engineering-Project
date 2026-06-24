# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer — Traffic Volume Analysis
# MAGIC Creates aggregated fact and dimension tables for traffic volume analysis in Power BI.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

# COMMAND ----------

SILVER_PATH = "/mnt/silver/traffic"
GOLD_PATH = "/mnt/gold/traffic_analysis"

# COMMAND ----------

df_counts = spark.read.format("delta").load(f"{SILVER_PATH}/counts")
df_count_points = spark.read.format("delta").load(f"{SILVER_PATH}/count_points")
df_regions = spark.read.format("delta").load(f"{SILVER_PATH}/regions")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Fact: Daily Traffic Summary

# COMMAND ----------

fact_daily_traffic = df_counts \
    .groupBy("count_point_id", "year", "count_date", "direction_of_travel") \
    .agg(
        F.sum("pedal_cycles").alias("total_pedal_cycles"),
        F.sum("two_wheeled_motor_vehicles").alias("total_motorcycles"),
        F.sum("cars_and_taxis").alias("total_cars"),
        F.sum("buses_and_coaches").alias("total_buses"),
        F.sum("lgvs").alias("total_lgvs"),
        F.sum("all_hgvs").alias("total_hgvs"),
        F.sum("total_vehicles").alias("total_all_vehicles"),
        F.avg("hgv_percentage").alias("avg_hgv_percentage"),
        F.count("*").alias("hours_counted")
    ) \
    .withColumn("motorised_vehicles",
        F.col("total_cars") + F.col("total_buses") + F.col("total_lgvs") +
        F.col("total_hgvs") + F.col("total_motorcycles")
    ) \
    .withColumn("active_travel_vehicles",
        F.col("total_pedal_cycles")
    ) \
    .withColumn("freight_vehicles",
        F.col("total_lgvs") + F.col("total_hgvs")
    )

fact_daily_traffic.write.format("delta") \
    .mode("overwrite") \
    .partitionBy("year") \
    .option("overwriteSchema", "true") \
    .save(f"{GOLD_PATH}/fact_daily_traffic")

print(f"fact_daily_traffic: {fact_daily_traffic.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Fact: Hourly Peak Analysis

# COMMAND ----------

fact_hourly_peaks = df_counts \
    .groupBy("count_point_id", "year", "hour", "time_period") \
    .agg(
        F.avg("total_vehicles").alias("avg_vehicles"),
        F.max("total_vehicles").alias("max_vehicles"),
        F.min("total_vehicles").alias("min_vehicles"),
        F.avg("cars_and_taxis").alias("avg_cars"),
        F.avg("all_hgvs").alias("avg_hgvs"),
        F.count("*").alias("observation_count")
    ) \
    .withColumn("congestion_index",
        F.round(F.col("avg_vehicles") / F.col("max_vehicles"), 3)
    )

fact_hourly_peaks.write.format("delta") \
    .mode("overwrite") \
    .partitionBy("year") \
    .option("overwriteSchema", "true") \
    .save(f"{GOLD_PATH}/fact_hourly_peaks")

print(f"fact_hourly_peaks: {fact_hourly_peaks.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Fact: Year-over-Year Regional Comparison

# COMMAND ----------

fact_yoy_regional = df_counts \
    .join(df_count_points.select("count_point_id", "region_name", "road_type"), "count_point_id") \
    .groupBy("region_name", "road_type", "year") \
    .agg(
        F.sum("total_vehicles").alias("total_vehicles"),
        F.sum("cars_and_taxis").alias("total_cars"),
        F.sum("all_hgvs").alias("total_hgvs"),
        F.sum("pedal_cycles").alias("total_cycles"),
        F.countDistinct("count_point_id").alias("count_points_observed")
    )

window_yoy = Window.partitionBy("region_name", "road_type").orderBy("year")

fact_yoy_regional = fact_yoy_regional \
    .withColumn("prev_year_vehicles", F.lag("total_vehicles").over(window_yoy)) \
    .withColumn("yoy_change_pct",
        F.round(
            (F.col("total_vehicles") - F.col("prev_year_vehicles")) /
            F.col("prev_year_vehicles") * 100, 2
        )
    )

fact_yoy_regional.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(f"{GOLD_PATH}/fact_yoy_regional")

print(f"fact_yoy_regional: {fact_yoy_regional.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Dimension: Count Point Location

# COMMAND ----------

dim_count_point = df_count_points \
    .select(
        "count_point_id", "road_name", "road_type",
        "region_name", "local_authority_name",
        "latitude", "longitude"
    ) \
    .withColumn("road_category",
        F.when(F.col("road_type") == "Major", "A Road / Motorway")
        .when(F.col("road_type") == "Minor", "B Road / Minor")
        .otherwise("Unclassified")
    )

dim_count_point.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(f"{GOLD_PATH}/dim_count_point")

print(f"dim_count_point: {dim_count_point.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Dimension: Date

# COMMAND ----------

date_range = spark.sql("""
    SELECT explode(sequence(to_date('2000-01-01'), to_date('2025-12-31'), interval 1 day)) AS date
""")

dim_date = date_range \
    .withColumn("year", F.year("date")) \
    .withColumn("month", F.month("date")) \
    .withColumn("day", F.dayofmonth("date")) \
    .withColumn("quarter", F.quarter("date")) \
    .withColumn("day_of_week", F.dayofweek("date")) \
    .withColumn("day_name", F.date_format("date", "EEEE")) \
    .withColumn("month_name", F.date_format("date", "MMMM")) \
    .withColumn("is_weekend", F.col("day_of_week").isin(1, 7)) \
    .withColumn("fiscal_year",
        F.when(F.col("month") >= 4, F.col("year"))
        .otherwise(F.col("year") - 1)
    ) \
    .withColumn("fiscal_quarter",
        F.when(F.col("month").isin(4, 5, 6), 1)
        .when(F.col("month").isin(7, 8, 9), 2)
        .when(F.col("month").isin(10, 11, 12), 3)
        .otherwise(4)
    )

dim_date.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(f"{GOLD_PATH}/dim_date")

print(f"dim_date: {dim_date.count()} rows")

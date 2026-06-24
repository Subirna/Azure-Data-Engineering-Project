# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer — Road Safety Intelligence
# MAGIC Creates aggregated tables for accident hotspots, severity analysis, and road safety KPIs.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

# COMMAND ----------

SILVER_ACCIDENTS = "/mnt/silver/accidents"
SILVER_TRAFFIC = "/mnt/silver/traffic"
GOLD_PATH = "/mnt/gold/road_safety"

# COMMAND ----------

df_collisions = spark.read.format("delta").load(f"{SILVER_ACCIDENTS}/collisions")
df_vehicles = spark.read.format("delta").load(f"{SILVER_ACCIDENTS}/vehicles")
df_casualties = spark.read.format("delta").load(f"{SILVER_ACCIDENTS}/casualties")
df_count_points = spark.read.format("delta").load(f"{SILVER_TRAFFIC}/count_points")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Fact: Accident Summary

# COMMAND ----------

fact_accidents = df_collisions \
    .groupBy(
        "collision_year", "collision_month",
        "severity_label", "weather_label", "light_condition_label",
        "is_urban", "speed_limit"
    ) \
    .agg(
        F.count("collision_id").alias("total_collisions"),
        F.sum("number_of_casualties").alias("total_casualties"),
        F.sum("number_of_vehicles").alias("total_vehicles_involved"),
        F.avg("number_of_casualties").alias("avg_casualties_per_collision"),
        F.sum(F.when(F.col("severity_label") == "Fatal", 1).otherwise(0)).alias("fatal_count"),
        F.sum(F.when(F.col("severity_label") == "Serious", 1).otherwise(0)).alias("serious_count"),
        F.sum(F.when(F.col("severity_label") == "Slight", 1).otherwise(0)).alias("slight_count")
    ) \
    .withColumn("ksi_count", F.col("fatal_count") + F.col("serious_count")) \
    .withColumn("ksi_rate",
        F.round(F.col("ksi_count") / F.col("total_collisions") * 100, 2)
    )

fact_accidents.write.format("delta") \
    .mode("overwrite") \
    .partitionBy("collision_year") \
    .option("overwriteSchema", "true") \
    .save(f"{GOLD_PATH}/fact_accident_summary")

print(f"fact_accident_summary: {fact_accidents.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Fact: Accident Hotspots (Geospatial Grid)

# COMMAND ----------

fact_hotspots = df_collisions \
    .withColumn("lat_grid", F.round(F.col("latitude"), 2)) \
    .withColumn("lon_grid", F.round(F.col("longitude"), 2)) \
    .groupBy("lat_grid", "lon_grid", "collision_year") \
    .agg(
        F.count("collision_id").alias("total_incidents"),
        F.sum(F.when(F.col("severity_label") == "Fatal", 1).otherwise(0)).alias("fatal_incidents"),
        F.sum(F.when(F.col("severity_label") == "Serious", 1).otherwise(0)).alias("serious_incidents"),
        F.sum("number_of_casualties").alias("total_casualties"),
        F.avg("speed_limit").alias("avg_speed_limit"),
        F.first("is_urban").alias("is_urban")
    ) \
    .withColumn("severity_score",
        F.col("fatal_incidents") * 10 + F.col("serious_incidents") * 5 +
        (F.col("total_incidents") - F.col("fatal_incidents") - F.col("serious_incidents")) * 1
    ) \
    .withColumn("hotspot_rank",
        F.dense_rank().over(
            Window.partitionBy("collision_year").orderBy(F.desc("severity_score"))
        )
    )

fact_hotspots.write.format("delta") \
    .mode("overwrite") \
    .partitionBy("collision_year") \
    .option("overwriteSchema", "true") \
    .save(f"{GOLD_PATH}/fact_accident_hotspots")

print(f"fact_accident_hotspots: {fact_hotspots.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Fact: Casualty Demographics

# COMMAND ----------

fact_casualty_demographics = df_casualties \
    .join(df_collisions.select("collision_id", "collision_year", "is_urban"), "collision_id") \
    .groupBy(
        "collision_year", "casualty_severity_label", "casualty_type_label",
        "casualty_age_band", "sex_label", "is_urban"
    ) \
    .agg(
        F.count("*").alias("casualty_count")
    )

fact_casualty_demographics.write.format("delta") \
    .mode("overwrite") \
    .partitionBy("collision_year") \
    .option("overwriteSchema", "true") \
    .save(f"{GOLD_PATH}/fact_casualty_demographics")

print(f"fact_casualty_demographics: {fact_casualty_demographics.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Fact: Vehicle Involvement Analysis

# COMMAND ----------

fact_vehicle_analysis = df_vehicles \
    .join(df_collisions.select("collision_id", "collision_year", "severity_label"), "collision_id") \
    .groupBy("collision_year", "vehicle_type_label", "driver_age_band", "severity_label") \
    .agg(
        F.count("*").alias("vehicle_count"),
        F.avg("age_of_vehicle").alias("avg_vehicle_age"),
        F.avg("engine_capacity_cc").alias("avg_engine_cc")
    )

fact_vehicle_analysis.write.format("delta") \
    .mode("overwrite") \
    .partitionBy("collision_year") \
    .option("overwriteSchema", "true") \
    .save(f"{GOLD_PATH}/fact_vehicle_analysis")

print(f"fact_vehicle_analysis: {fact_vehicle_analysis.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Fact: Day/Time Collision Pattern

# COMMAND ----------

fact_time_patterns = df_collisions \
    .withColumn("hour", F.hour(F.col("time"))) \
    .withColumn("time_period",
        F.when(F.col("hour").between(7, 9), "Morning Rush")
        .when(F.col("hour").between(10, 15), "Midday")
        .when(F.col("hour").between(16, 18), "Evening Rush")
        .when(F.col("hour").between(19, 22), "Evening")
        .otherwise("Night")
    ) \
    .groupBy("collision_year", "day_of_week", "hour", "time_period", "severity_label") \
    .agg(
        F.count("collision_id").alias("collision_count"),
        F.sum("number_of_casualties").alias("casualty_count")
    )

fact_time_patterns.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(f"{GOLD_PATH}/fact_time_patterns")

print(f"fact_time_patterns: {fact_time_patterns.count()} rows")

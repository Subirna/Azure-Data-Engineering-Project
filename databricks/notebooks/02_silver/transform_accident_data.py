# Databricks notebook source
# MAGIC %md
# MAGIC # Silver Layer — Transform UK Road Accident Data
# MAGIC Cleanses and standardizes STATS19 collision, vehicle, and casualty data.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, DoubleType

# COMMAND ----------

BRONZE_PATH = "/mnt/bronze/accidents"
SILVER_PATH = "/mnt/silver/accidents"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Transform Collisions

# COMMAND ----------

df_collisions = spark.read.format("delta").load(f"{BRONZE_PATH}/collisions")

SEVERITY_MAP = {1: "Fatal", 2: "Serious", 3: "Slight"}

df_collisions_silver = df_collisions \
    .withColumnRenamed("accident_index", "collision_id") \
    .withColumn("collision_date", F.to_date(F.col("date"), "dd/MM/yyyy")) \
    .withColumn("collision_year", F.year(F.col("collision_date"))) \
    .withColumn("collision_month", F.month(F.col("collision_date"))) \
    .withColumn("day_of_week", F.dayofweek(F.col("collision_date"))) \
    .withColumn("latitude", F.col("latitude").cast(DoubleType())) \
    .withColumn("longitude", F.col("longitude").cast(DoubleType())) \
    .withColumn("number_of_vehicles", F.col("number_of_vehicles").cast(IntegerType())) \
    .withColumn("number_of_casualties", F.col("number_of_casualties").cast(IntegerType())) \
    .withColumn("speed_limit", F.col("speed_limit").cast(IntegerType())) \
    .withColumn("severity_label",
        F.when(F.col("accident_severity") == 1, "Fatal")
        .when(F.col("accident_severity") == 2, "Serious")
        .when(F.col("accident_severity") == 3, "Slight")
        .otherwise("Unknown")
    ) \
    .withColumn("is_urban",
        F.when(F.col("urban_or_rural_area") == 1, True)
        .otherwise(False)
    ) \
    .withColumn("light_condition_label",
        F.when(F.col("light_conditions") == 1, "Daylight")
        .when(F.col("light_conditions") == 4, "Darkness - lights lit")
        .when(F.col("light_conditions") == 5, "Darkness - lights unlit")
        .when(F.col("light_conditions") == 6, "Darkness - no lighting")
        .when(F.col("light_conditions") == 7, "Darkness - lighting unknown")
        .otherwise("Unknown")
    ) \
    .withColumn("weather_label",
        F.when(F.col("weather_conditions") == 1, "Fine no high winds")
        .when(F.col("weather_conditions") == 2, "Raining no high winds")
        .when(F.col("weather_conditions") == 3, "Snowing no high winds")
        .when(F.col("weather_conditions") == 4, "Fine + high winds")
        .when(F.col("weather_conditions") == 5, "Raining + high winds")
        .when(F.col("weather_conditions") == 6, "Snowing + high winds")
        .when(F.col("weather_conditions") == 7, "Fog or mist")
        .otherwise("Other/Unknown")
    ) \
    .filter(
        F.col("latitude").isNotNull() &
        F.col("longitude").isNotNull() &
        F.col("latitude").between(49.0, 61.0) &
        F.col("longitude").between(-8.0, 2.0)
    ) \
    .dropDuplicates(["collision_id"]) \
    .withColumn("_processed_timestamp", F.current_timestamp())

df_collisions_silver.write.format("delta") \
    .mode("overwrite") \
    .partitionBy("collision_year") \
    .option("overwriteSchema", "true") \
    .save(f"{SILVER_PATH}/collisions")

print(f"Silver collisions: {df_collisions_silver.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Transform Vehicles

# COMMAND ----------

df_vehicles = spark.read.format("delta").load(f"{BRONZE_PATH}/vehicles")

df_vehicles_silver = df_vehicles \
    .withColumnRenamed("accident_index", "collision_id") \
    .withColumn("vehicle_type_label",
        F.when(F.col("vehicle_type") == 1, "Pedal cycle")
        .when(F.col("vehicle_type") == 2, "Motorcycle 50cc and under")
        .when(F.col("vehicle_type") == 3, "Motorcycle 125cc and under")
        .when(F.col("vehicle_type") == 4, "Motorcycle over 125cc and up to 500cc")
        .when(F.col("vehicle_type") == 5, "Motorcycle over 500cc")
        .when(F.col("vehicle_type") == 8, "Taxi/Private hire car")
        .when(F.col("vehicle_type") == 9, "Car")
        .when(F.col("vehicle_type") == 10, "Minibus")
        .when(F.col("vehicle_type") == 11, "Bus or coach")
        .when(F.col("vehicle_type").isin(19, 20, 21), "Goods vehicle")
        .when(F.col("vehicle_type") == 90, "Other vehicle")
        .otherwise("Unknown")
    ) \
    .withColumn("age_of_driver", F.col("age_of_driver").cast(IntegerType())) \
    .withColumn("age_of_vehicle", F.col("age_of_vehicle").cast(IntegerType())) \
    .withColumn("engine_capacity_cc", F.col("engine_capacity_cc").cast(IntegerType())) \
    .withColumn("driver_age_band",
        F.when(F.col("age_of_driver").between(17, 25), "17-25")
        .when(F.col("age_of_driver").between(26, 35), "26-35")
        .when(F.col("age_of_driver").between(36, 45), "36-45")
        .when(F.col("age_of_driver").between(46, 55), "46-55")
        .when(F.col("age_of_driver").between(56, 65), "56-65")
        .when(F.col("age_of_driver") > 65, "65+")
        .otherwise("Unknown")
    ) \
    .dropDuplicates(["collision_id", "vehicle_reference"]) \
    .withColumn("_processed_timestamp", F.current_timestamp())

df_vehicles_silver.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(f"{SILVER_PATH}/vehicles")

print(f"Silver vehicles: {df_vehicles_silver.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Transform Casualties

# COMMAND ----------

df_casualties = spark.read.format("delta").load(f"{BRONZE_PATH}/casualties")

df_casualties_silver = df_casualties \
    .withColumnRenamed("accident_index", "collision_id") \
    .withColumn("casualty_severity_label",
        F.when(F.col("casualty_severity") == 1, "Fatal")
        .when(F.col("casualty_severity") == 2, "Serious")
        .when(F.col("casualty_severity") == 3, "Slight")
        .otherwise("Unknown")
    ) \
    .withColumn("age_of_casualty", F.col("age_of_casualty").cast(IntegerType())) \
    .withColumn("casualty_age_band",
        F.when(F.col("age_of_casualty").between(0, 15), "0-15")
        .when(F.col("age_of_casualty").between(16, 25), "16-25")
        .when(F.col("age_of_casualty").between(26, 35), "26-35")
        .when(F.col("age_of_casualty").between(36, 45), "36-45")
        .when(F.col("age_of_casualty").between(46, 55), "46-55")
        .when(F.col("age_of_casualty").between(56, 65), "56-65")
        .when(F.col("age_of_casualty") > 65, "65+")
        .otherwise("Unknown")
    ) \
    .withColumn("casualty_type_label",
        F.when(F.col("casualty_type") == 0, "Pedestrian")
        .when(F.col("casualty_type") == 1, "Cyclist")
        .when(F.col("casualty_type").isin(2, 3, 4, 5, 23), "Motorcyclist")
        .when(F.col("casualty_type").isin(8, 9), "Car occupant")
        .when(F.col("casualty_type") == 11, "Bus/coach occupant")
        .when(F.col("casualty_type").isin(19, 20, 21), "Goods vehicle occupant")
        .otherwise("Other")
    ) \
    .withColumn("sex_label",
        F.when(F.col("sex_of_casualty") == 1, "Male")
        .when(F.col("sex_of_casualty") == 2, "Female")
        .otherwise("Unknown")
    ) \
    .dropDuplicates(["collision_id", "casualty_reference"]) \
    .withColumn("_processed_timestamp", F.current_timestamp())

df_casualties_silver.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(f"{SILVER_PATH}/casualties")

print(f"Silver casualties: {df_casualties_silver.count()} rows")

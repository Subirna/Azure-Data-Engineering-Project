# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer — Environmental Impact Analysis
# MAGIC Estimates CO2 emissions and tracks vehicle composition trends for sustainability reporting.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

# COMMAND ----------

SILVER_PATH = "/mnt/silver/traffic"
GOLD_PATH = "/mnt/gold/environmental"

# COMMAND ----------

df_counts = spark.read.format("delta").load(f"{SILVER_PATH}/counts")
df_count_points = spark.read.format("delta").load(f"{SILVER_PATH}/count_points")

# COMMAND ----------

# MAGIC %md
# MAGIC ## CO2 Emission Factors (grams per km, UK Gov BEIS 2023 averages)

# COMMAND ----------

# Average UK emission factors by vehicle type (g CO2/km)
EMISSION_FACTORS = {
    "pedal_cycles": 0,
    "two_wheeled_motor_vehicles": 83,
    "cars_and_taxis": 164,
    "buses_and_coaches": 822,
    "lgvs": 209,
    "all_hgvs": 586,
}

AVG_TRIP_DISTANCE_KM = 12.8  # UK NTS average trip length

# COMMAND ----------

# MAGIC %md
# MAGIC ## Fact: Estimated CO2 Emissions by Region

# COMMAND ----------

df_enriched = df_counts.join(
    df_count_points.select("count_point_id", "region_name", "local_authority_name", "road_type"),
    "count_point_id"
)

for vehicle_type, factor in EMISSION_FACTORS.items():
    df_enriched = df_enriched.withColumn(
        f"co2_{vehicle_type}_kg",
        F.round(F.col(vehicle_type) * factor * AVG_TRIP_DISTANCE_KM / 1000, 2)
    )

co2_columns = [f"co2_{vt}_kg" for vt in EMISSION_FACTORS]

fact_co2_emissions = df_enriched \
    .withColumn("total_co2_kg", sum(F.col(c) for c in co2_columns)) \
    .groupBy("region_name", "local_authority_name", "road_type", "year") \
    .agg(
        F.sum("total_co2_kg").alias("total_co2_tonnes"),
        F.sum("co2_cars_and_taxis_kg").alias("car_co2_tonnes"),
        F.sum("co2_all_hgvs_kg").alias("hgv_co2_tonnes"),
        F.sum("co2_buses_and_coaches_kg").alias("bus_co2_tonnes"),
        F.sum("co2_lgvs_kg").alias("lgv_co2_tonnes"),
        F.sum("total_vehicles").alias("total_vehicle_count"),
        F.sum("pedal_cycles").alias("total_cycle_count"),
        F.countDistinct("count_point_id").alias("observation_points")
    ) \
    .withColumn("total_co2_tonnes", F.round(F.col("total_co2_tonnes") / 1000, 2)) \
    .withColumn("car_co2_tonnes", F.round(F.col("car_co2_tonnes") / 1000, 2)) \
    .withColumn("hgv_co2_tonnes", F.round(F.col("hgv_co2_tonnes") / 1000, 2)) \
    .withColumn("co2_per_vehicle_kg",
        F.round(F.col("total_co2_tonnes") * 1000 / F.col("total_vehicle_count"), 2)
    )

fact_co2_emissions.write.format("delta") \
    .mode("overwrite") \
    .partitionBy("year") \
    .option("overwriteSchema", "true") \
    .save(f"{GOLD_PATH}/fact_co2_emissions")

print(f"fact_co2_emissions: {fact_co2_emissions.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Fact: Vehicle Composition Trends (Green Transport Index)

# COMMAND ----------

fact_vehicle_mix = df_enriched \
    .groupBy("region_name", "year") \
    .agg(
        F.sum("pedal_cycles").alias("cycles"),
        F.sum("two_wheeled_motor_vehicles").alias("motorcycles"),
        F.sum("cars_and_taxis").alias("cars"),
        F.sum("buses_and_coaches").alias("buses"),
        F.sum("lgvs").alias("lgvs"),
        F.sum("all_hgvs").alias("hgvs"),
        F.sum("total_vehicles").alias("total")
    ) \
    .withColumn("car_share_pct", F.round(F.col("cars") / F.col("total") * 100, 2)) \
    .withColumn("cycle_share_pct", F.round(F.col("cycles") / F.col("total") * 100, 2)) \
    .withColumn("hgv_share_pct", F.round(F.col("hgvs") / F.col("total") * 100, 2)) \
    .withColumn("bus_share_pct", F.round(F.col("buses") / F.col("total") * 100, 2)) \
    .withColumn("green_transport_index",
        F.round((F.col("cycles") + F.col("buses")) / F.col("total") * 100, 2)
    )

window_yoy = Window.partitionBy("region_name").orderBy("year")

fact_vehicle_mix = fact_vehicle_mix \
    .withColumn("prev_green_index", F.lag("green_transport_index").over(window_yoy)) \
    .withColumn("green_index_change",
        F.round(F.col("green_transport_index") - F.col("prev_green_index"), 2)
    )

fact_vehicle_mix.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(f"{GOLD_PATH}/fact_vehicle_mix")

print(f"fact_vehicle_mix: {fact_vehicle_mix.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Fact: Active Travel Adoption

# COMMAND ----------

fact_active_travel = df_enriched \
    .groupBy("region_name", "local_authority_name", "year") \
    .agg(
        F.sum("pedal_cycles").alias("total_cycles"),
        F.sum("total_vehicles").alias("total_all_vehicles"),
        F.countDistinct("count_point_id").alias("observation_points")
    ) \
    .withColumn("cycle_mode_share",
        F.round(F.col("total_cycles") / F.col("total_all_vehicles") * 100, 2)
    ) \
    .withColumn("cycles_per_observation_point",
        F.round(F.col("total_cycles") / F.col("observation_points"), 0)
    )

window_yoy_la = Window.partitionBy("region_name", "local_authority_name").orderBy("year")

fact_active_travel = fact_active_travel \
    .withColumn("prev_cycle_share", F.lag("cycle_mode_share").over(window_yoy_la)) \
    .withColumn("cycle_share_change",
        F.round(F.col("cycle_mode_share") - F.col("prev_cycle_share"), 2)
    )

fact_active_travel.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(f"{GOLD_PATH}/fact_active_travel")

print(f"fact_active_travel: {fact_active_travel.count()} rows")

# Databricks notebook source
# MAGIC %md
# MAGIC # 04 - Gold Layer Transformation
# MAGIC Creates business-ready aggregated tables for Power BI dashboard.
# MAGIC Run 01_setup_config FIRST.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

storage_account = "subiradls2026"
SILVER_PATH = f"abfss://silver@{storage_account}.dfs.core.windows.net/traffic"
GOLD_PATH = f"abfss://gold@{storage_account}.dfs.core.windows.net"

df_counts_silver = spark.read.parquet(f"{SILVER_PATH}/counts/")
df_regions = spark.read.parquet(f"{SILVER_PATH}/regions/")
df_la = spark.read.parquet(f"{SILVER_PATH}/local_authorities/")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold 1: Traffic Summary by Region & Year

# COMMAND ----------

fact_traffic = df_counts_silver \
    .join(df_regions.withColumnRenamed("id", "region_id").withColumnRenamed("name", "region_name"), "region_id") \
    .groupBy("region_name", "road_type", "year") \
    .agg(
        F.sum("cars_and_taxis").alias("total_cars"),
        F.sum("buses_and_coaches").alias("total_buses"),
        F.sum("lgvs").alias("total_lgvs"),
        F.sum("all_hgvs").alias("total_hgvs"),
        F.sum("pedal_cycles").alias("total_cycles"),
        F.sum("two_wheeled_motor_vehicles").alias("total_motorcycles"),
        F.sum("all_motor_vehicles").alias("total_motor_vehicles"),
        F.sum("total_vehicles").alias("total_all_vehicles"),
        F.countDistinct("count_point_id").alias("count_points_observed"),
        F.avg("hgv_percentage").alias("avg_hgv_pct")
    ) \
    .withColumn("freight_vehicles", F.col("total_lgvs") + F.col("total_hgvs")) \
    .withColumn("green_transport_index",
        F.round((F.col("total_cycles") + F.col("total_buses")) / F.col("total_all_vehicles") * 100, 2)
    )

window_yoy = Window.partitionBy("region_name", "road_type").orderBy("year")
fact_traffic = fact_traffic \
    .withColumn("prev_year_vehicles", F.lag("total_all_vehicles").over(window_yoy)) \
    .withColumn("yoy_change_pct",
        F.round((F.col("total_all_vehicles") - F.col("prev_year_vehicles")) / F.col("prev_year_vehicles") * 100, 2)
    )

fact_traffic.write.mode("overwrite").parquet(f"{GOLD_PATH}/fact_traffic_summary/")
print(f"Gold fact_traffic_summary: {fact_traffic.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold 2: CO2 Emissions Estimate

# COMMAND ----------

CO2_FACTORS = {"pedal_cycles": 0, "two_wheeled_motor_vehicles": 83, "cars_and_taxis": 164,
               "buses_and_coaches": 822, "lgvs": 209, "all_hgvs": 586}
AVG_TRIP_KM = 12.8

fact_co2 = df_counts_silver \
    .join(df_regions.withColumnRenamed("id", "region_id").withColumnRenamed("name", "region_name"), "region_id")

for vtype, factor in CO2_FACTORS.items():
    fact_co2 = fact_co2.withColumn(f"co2_{vtype}_kg", F.round(F.col(vtype) * factor * AVG_TRIP_KM / 1000, 2))

co2_cols = [f"co2_{vt}_kg" for vt in CO2_FACTORS]
fact_co2 = fact_co2 \
    .withColumn("total_co2_kg", sum(F.col(c) for c in co2_cols)) \
    .groupBy("region_name", "road_type", "year") \
    .agg(
        F.round(F.sum("total_co2_kg") / 1000, 2).alias("total_co2_tonnes"),
        F.round(F.sum("co2_cars_and_taxis_kg") / 1000, 2).alias("car_co2_tonnes"),
        F.round(F.sum("co2_all_hgvs_kg") / 1000, 2).alias("hgv_co2_tonnes"),
        F.sum("all_motor_vehicles").alias("total_vehicle_count")
    ) \
    .withColumn("co2_per_vehicle_kg", F.round(F.col("total_co2_tonnes") * 1000 / F.col("total_vehicle_count"), 2))

fact_co2.write.mode("overwrite").parquet(f"{GOLD_PATH}/fact_co2_emissions/")
print(f"Gold fact_co2_emissions: {fact_co2.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold 3: Vehicle Mix & Green Transport Index

# COMMAND ----------

fact_vehicle_mix = df_counts_silver \
    .join(df_regions.withColumnRenamed("id", "region_id").withColumnRenamed("name", "region_name"), "region_id") \
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

fact_vehicle_mix.write.mode("overwrite").parquet(f"{GOLD_PATH}/fact_vehicle_mix/")
print(f"Gold fact_vehicle_mix: {fact_vehicle_mix.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold 4: Road Category Analysis

# COMMAND ----------

fact_road = df_counts_silver \
    .join(df_regions.withColumnRenamed("id", "region_id").withColumnRenamed("name", "region_name"), "region_id") \
    .withColumn("road_class",
        F.when(F.col("road_category").isin("TA", "TM"), "Motorway/Trunk A")
        .when(F.col("road_category") == "PA", "Principal A")
        .when(F.col("road_category") == "M", "Motorway")
        .otherwise("Minor/B Road")
    ) \
    .groupBy("region_name", "road_class", "road_name", "year") \
    .agg(
        F.sum("all_motor_vehicles").alias("total_motor_vehicles"),
        F.sum("all_hgvs").alias("total_hgvs"),
        F.sum("pedal_cycles").alias("total_cycles"),
        F.avg("link_length_km").alias("avg_link_length_km"),
        F.countDistinct("count_point_id").alias("count_points")
    ) \
    .withColumn("vehicles_per_km",
        F.round(F.col("total_motor_vehicles") / F.col("avg_link_length_km"), 0)
    )

fact_road.write.mode("overwrite").parquet(f"{GOLD_PATH}/fact_road_analysis/")
print(f"Gold fact_road_analysis: {fact_road.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold 5: COVID Impact Analysis

# COMMAND ----------

covid_data = df_counts_silver \
    .join(df_regions.withColumnRenamed("id", "region_id").withColumnRenamed("name", "region_name"), "region_id") \
    .filter(F.col("year").between(2019, 2025)) \
    .groupBy("region_name", "road_type", "year") \
    .agg(
        F.sum("all_motor_vehicles").alias("total_vehicles"),
        F.sum("pedal_cycles").alias("total_cycles"),
        F.sum("all_hgvs").alias("total_hgvs")
    )

# Get 2019 baseline as separate dataframe and join (avoids window function null issue)
baseline = covid_data \
    .filter(F.col("year") == 2019) \
    .select("region_name", "road_type", F.col("total_vehicles").alias("baseline_2019"))

window_covid = Window.partitionBy("region_name", "road_type").orderBy("year")

fact_covid = covid_data \
    .join(baseline, ["region_name", "road_type"], "left") \
    .withColumn("recovery_pct",
        F.round(F.col("total_vehicles") / F.col("baseline_2019") * 100, 2)
    ) \
    .withColumn("yoy_change",
        F.round(F.col("total_vehicles") - F.lag("total_vehicles").over(window_covid), 0)
    )

fact_covid.write.mode("overwrite").parquet(f"{GOLD_PATH}/fact_covid_impact/")
print(f"Gold fact_covid_impact: {fact_covid.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold 6: Top Busiest Roads

# COMMAND ----------

fact_busiest = df_counts_silver \
    .join(df_regions.withColumnRenamed("id", "region_id").withColumnRenamed("name", "region_name"), "region_id") \
    .filter(F.col("year") == 2023) \
    .groupBy("region_name", "road_name", "road_type", "latitude", "longitude") \
    .agg(
        F.sum("all_motor_vehicles").alias("total_vehicles"),
        F.sum("all_hgvs").alias("total_hgvs"),
        F.sum("pedal_cycles").alias("total_cycles")
    ) \
    .withColumn("rank",
        F.dense_rank().over(Window.orderBy(F.desc("total_vehicles")))
    ) \
    .filter(F.col("rank") <= 500)

fact_busiest.write.mode("overwrite").parquet(f"{GOLD_PATH}/fact_busiest_roads/")
print(f"Gold fact_busiest_roads: {fact_busiest.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold 7: Dimension - Location

# COMMAND ----------

dim_location = df_counts_silver \
    .join(df_regions.withColumnRenamed("id", "region_id").withColumnRenamed("name", "region_name"), "region_id") \
    .join(df_la.withColumnRenamed("id", "local_authority_id").withColumnRenamed("name", "local_authority_name"), "local_authority_id") \
    .select("count_point_id", "road_name", "road_type", "road_category",
            "region_name", "local_authority_name", "latitude", "longitude") \
    .dropDuplicates(["count_point_id"]) \
    .withColumn("road_class",
        F.when(F.col("road_category").isin("TA", "TM"), "Motorway/Trunk A")
        .when(F.col("road_category") == "PA", "Principal A")
        .when(F.col("road_category") == "M", "Motorway")
        .otherwise("Minor/B Road")
    )

dim_location.write.mode("overwrite").parquet(f"{GOLD_PATH}/dim_location/")
print(f"Gold dim_location: {dim_location.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold 8: Dimension - Date

# COMMAND ----------

dim_date = spark.sql("""
    SELECT explode(sequence(to_date('2000-01-01'), to_date('2025-12-31'), interval 1 day)) AS date
""") \
    .withColumn("year", F.year("date")) \
    .withColumn("month", F.month("date")) \
    .withColumn("quarter", F.quarter("date")) \
    .withColumn("day_name", F.date_format("date", "EEEE")) \
    .withColumn("month_name", F.date_format("date", "MMMM")) \
    .withColumn("is_weekend", F.dayofweek("date").isin(1, 7))

dim_date.write.mode("overwrite").parquet(f"{GOLD_PATH}/dim_date/")
print(f"Gold dim_date: {dim_date.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify All Gold Tables

# COMMAND ----------

print("=== GOLD LAYER COMPLETE ===\n")
for table in ["fact_traffic_summary", "fact_co2_emissions", "fact_vehicle_mix",
              "fact_road_analysis", "fact_covid_impact", "fact_busiest_roads",
              "dim_location", "dim_date"]:
    df = spark.read.parquet(f"{GOLD_PATH}/{table}/")
    has_year = "year" in df.columns
    print(f"  {table}: {df.count()} rows, {len(df.columns)} cols, year_column: {has_year}")

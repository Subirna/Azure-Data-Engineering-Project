# Databricks notebook source
# MAGIC %md
# MAGIC # Streaming — Gold Layer Aggregations
# MAGIC Creates 5 aggregated Gold tables from Silver streaming data for Power BI.
# MAGIC Run this AFTER 02_databricks_streaming_bronze_silver has processed events.

# COMMAND ----------

# Storage config
storage_account = "subiradls2026"
storage_key = dbutils.secrets.get(scope="uk-traffic-vault", key="subiadls-account-key")

spark.conf.set(
    f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
    storage_key
)

# COMMAND ----------

from pyspark.sql import functions as F

SILVER_PATH = f"abfss://silver@{storage_account}.dfs.core.windows.net/streaming/carbon_intensity"
GOLD_PATH = f"abfss://gold@{storage_account}.dfs.core.windows.net/streaming"

df_silver = spark.read.parquet(f"{SILVER_PATH}/")
# Use only latest cycle data for dashboard (no time-window dependency)
latest_ts = df_silver.agg(F.max("data_timestamp")).collect()[0][0]
df_silver = df_silver.filter(F.col("data_timestamp") == latest_ts)
print(f"Silver streaming records (latest cycle from {latest_ts}): {df_silver.count()}")
df_silver.groupBy("event_type").count().show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold 1: National Intensity Timeline

# COMMAND ----------

gold_national = df_silver \
    .filter(F.col("event_type") == "national_intensity") \
    .select("data_timestamp", "period_from", "period_to", "forecast", "actual", "intensity_index") \
    .withColumn("forecast_vs_actual", F.round(F.col("actual") - F.col("forecast"), 2)) \
    .withColumn("intensity_category",
        F.when(F.col("actual") <= 50, "Very Low")
        .when(F.col("actual") <= 100, "Low")
        .when(F.col("actual") <= 200, "Moderate")
        .when(F.col("actual") <= 300, "High")
        .otherwise("Very High")) \
    .dropDuplicates(["period_from"])

gold_national.write.mode("overwrite").parquet(f"{GOLD_PATH}/gold_national_intensity/")
print(f"gold_national_intensity: {gold_national.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold 2: Generation Mix (Energy Sources)

# COMMAND ----------

gold_generation = df_silver \
    .filter(F.col("event_type") == "generation_mix") \
    .select("data_timestamp", "period_from", "period_to", "fuel_type", "fuel_percentage") \
    .withColumn("energy_category",
        F.when(F.col("fuel_type").isin("wind", "solar", "hydro"), "Renewable")
        .when(F.col("fuel_type") == "nuclear", "Nuclear")
        .when(F.col("fuel_type").isin("gas", "coal"), "Fossil Fuel")
        .otherwise("Other")) \
    .dropDuplicates(["period_from", "fuel_type"])

gold_generation.write.mode("overwrite").parquet(f"{GOLD_PATH}/gold_generation_mix/")
print(f"gold_generation_mix: {gold_generation.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold 3: Regional Intensity Comparison

# COMMAND ----------

gold_regional = df_silver \
    .filter(F.col("event_type") == "regional_intensity") \
    .select("data_timestamp", "period_from", "period_to", "region_id", "region_name", "dno_region", "forecast", "intensity_index") \
    .withColumn("intensity_category",
        F.when(F.col("forecast") <= 50, "Very Low")
        .when(F.col("forecast") <= 100, "Low")
        .when(F.col("forecast") <= 200, "Moderate")
        .when(F.col("forecast") <= 300, "High")
        .otherwise("Very High")) \
    .dropDuplicates(["period_from", "region_id"])

gold_regional.write.mode("overwrite").parquet(f"{GOLD_PATH}/gold_regional_intensity/")
print(f"gold_regional_intensity: {gold_regional.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold 4: Regional Energy Mix

# COMMAND ----------

gold_regional_gen = df_silver \
    .filter(F.col("event_type") == "regional_generation") \
    .select("data_timestamp", "period_from", "region_id", "region_name", "fuel_type", "fuel_percentage") \
    .withColumn("energy_category",
        F.when(F.col("fuel_type").isin("wind", "solar", "hydro"), "Renewable")
        .when(F.col("fuel_type") == "nuclear", "Nuclear")
        .when(F.col("fuel_type").isin("gas", "coal"), "Fossil Fuel")
        .otherwise("Other")) \
    .dropDuplicates(["period_from", "region_id", "fuel_type"])

gold_regional_gen.write.mode("overwrite").parquet(f"{GOLD_PATH}/gold_regional_generation/")
print(f"gold_regional_generation: {gold_regional_gen.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold 5: Renewable vs Fossil Summary

# COMMAND ----------

gold_renewable = df_silver \
    .filter(F.col("event_type") == "generation_mix") \
    .withColumn("energy_category",
        F.when(F.col("fuel_type").isin("wind", "solar", "hydro"), "Renewable")
        .when(F.col("fuel_type") == "nuclear", "Nuclear")
        .when(F.col("fuel_type").isin("gas", "coal"), "Fossil Fuel")
        .otherwise("Other")) \
    .groupBy("period_from", "energy_category") \
    .agg(F.sum("fuel_percentage").alias("total_percentage")) \
    .dropDuplicates(["period_from", "energy_category"])

gold_renewable.write.mode("overwrite").parquet(f"{GOLD_PATH}/gold_renewable_summary/")
print(f"gold_renewable_summary: {gold_renewable.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify All Streaming Gold Tables

# COMMAND ----------

print("=== STREAMING GOLD COMPLETE ===\n")
for t in ["gold_national_intensity", "gold_generation_mix", "gold_regional_intensity",
          "gold_regional_generation", "gold_renewable_summary"]:
    df = spark.read.parquet(f"{GOLD_PATH}/{t}/")
    print(f"  {t}: {df.count()} rows, {len(df.columns)} columns")

# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze Layer — Ingest UK Traffic Count Data
# MAGIC Reads raw traffic count data from UK DfT API and stores as Delta tables in the Bronze layer.

# COMMAND ----------

import requests
import json
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, LongType
from datetime import datetime

# COMMAND ----------

BASE_URL = "https://roadtraffic.dft.gov.uk/api"
BRONZE_PATH = "/mnt/bronze/traffic"
INGESTION_DATE = datetime.now().strftime("%Y-%m-%d")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Ingest Count Points (Reference Data)

# COMMAND ----------

response = requests.get(f"{BASE_URL}/count-points", params={"limit": 50000}, timeout=120)
count_points_data = response.json()

count_points_rdd = spark.sparkContext.parallelize([json.dumps(record) for record in count_points_data["rows"]])
df_count_points_raw = spark.read.json(count_points_rdd)

df_count_points = df_count_points_raw.withColumn("_ingestion_timestamp", F.current_timestamp()) \
    .withColumn("_ingestion_date", F.lit(INGESTION_DATE)) \
    .withColumn("_source", F.lit("dft_api_count_points"))

df_count_points.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(f"{BRONZE_PATH}/count_points")

print(f"Ingested {df_count_points.count()} count points")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Ingest Traffic Counts

# COMMAND ----------

response = requests.get(f"{BASE_URL}/counts", params={"limit": 100000}, timeout=300)
counts_data = response.json()

counts_rdd = spark.sparkContext.parallelize([json.dumps(record) for record in counts_data["rows"]])
df_counts_raw = spark.read.json(counts_rdd)

df_counts = df_counts_raw.withColumn("_ingestion_timestamp", F.current_timestamp()) \
    .withColumn("_ingestion_date", F.lit(INGESTION_DATE)) \
    .withColumn("_source", F.lit("dft_api_counts"))

df_counts.write.format("delta") \
    .mode("overwrite") \
    .partitionBy("year") \
    .option("overwriteSchema", "true") \
    .save(f"{BRONZE_PATH}/counts")

print(f"Ingested {df_counts.count()} traffic count records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Ingest Regions & Local Authorities (Reference Data)

# COMMAND ----------

for endpoint, name in [("/regions", "regions"), ("/local-authorities", "local_authorities")]:
    response = requests.get(f"{BASE_URL}{endpoint}", timeout=60)
    data = response.json()

    rdd = spark.sparkContext.parallelize([json.dumps(record) for record in data["rows"]])
    df = spark.read.json(rdd) \
        .withColumn("_ingestion_timestamp", F.current_timestamp()) \
        .withColumn("_ingestion_date", F.lit(INGESTION_DATE)) \
        .withColumn("_source", F.lit(f"dft_api_{name}"))

    df.write.format("delta") \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .save(f"{BRONZE_PATH}/{name}")

    print(f"Ingested {df.count()} {name} records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Bronze Layer

# COMMAND ----------

for table in ["count_points", "counts", "regions", "local_authorities"]:
    df = spark.read.format("delta").load(f"{BRONZE_PATH}/{table}")
    print(f"{table}: {df.count()} rows, {len(df.columns)} columns")

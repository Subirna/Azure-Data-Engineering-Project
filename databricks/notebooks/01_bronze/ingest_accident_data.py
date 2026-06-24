# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze Layer — Ingest UK Road Accident Data (STATS19)
# MAGIC Downloads STATS19 collision, vehicle, and casualty CSV files and stores as Delta tables.

# COMMAND ----------

from pyspark.sql import functions as F
from datetime import datetime

# COMMAND ----------

BRONZE_PATH = "/mnt/bronze/accidents"
INGESTION_DATE = datetime.now().strftime("%Y-%m-%d")

ACCIDENT_FILES = {
    "collisions": "https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-collision-2023.csv",
    "vehicles": "https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-vehicle-2023.csv",
    "casualties": "https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-casualty-2023.csv",
}

# COMMAND ----------

# MAGIC %md
# MAGIC ## Download & Ingest Accident Files

# COMMAND ----------

for table_name, url in ACCIDENT_FILES.items():
    print(f"Ingesting {table_name} from {url}...")

    df_raw = spark.read.format("csv") \
        .option("header", "true") \
        .option("inferSchema", "true") \
        .option("multiLine", "true") \
        .option("escape", '"') \
        .load(url)

    df = df_raw.withColumn("_ingestion_timestamp", F.current_timestamp()) \
        .withColumn("_ingestion_date", F.lit(INGESTION_DATE)) \
        .withColumn("_source", F.lit(f"stats19_{table_name}"))

    df.write.format("delta") \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .save(f"{BRONZE_PATH}/{table_name}")

    print(f"  {table_name}: {df.count()} rows ingested")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Bronze Accident Tables

# COMMAND ----------

for table_name in ACCIDENT_FILES:
    df = spark.read.format("delta").load(f"{BRONZE_PATH}/{table_name}")
    print(f"{table_name}: {df.count()} rows, {len(df.columns)} columns")
    df.printSchema()

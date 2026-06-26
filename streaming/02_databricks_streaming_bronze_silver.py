# Databricks notebook source
# MAGIC %md
# MAGIC # Streaming — Bronze & Silver Layer
# MAGIC Reads real-time carbon intensity data from Azure Event Hub using Python consumer.
# MAGIC Writes to Bronze (raw) and Silver (cleansed) layers in ADLS Gen2.
# MAGIC
# MAGIC **Prerequisites:**
# MAGIC - Event Hub namespace: eh-uk-traffic-subirna
# MAGIC - Event Hub name: carbon-intensity-stream
# MAGIC - Producer script running (01_producer_carbon_intensity.py)
# MAGIC - Library installed: azure-eventhub (PyPI)

# COMMAND ----------

# Storage config
storage_account = "subiradls2026"
storage_key = "<PASTE_KEY_FROM_AZURE_PORTAL: subiradls2026 > Security + networking > Access keys > key1>"

spark.conf.set(
    f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
    storage_key
)

# Event Hub config
EVENT_HUB_CONNECTION_STRING = "<PASTE_EVENT_HUB_CONNECTION_STRING>"
EVENT_HUB_NAME = "carbon-intensity-stream"

BRONZE_PATH = f"abfss://bronze@{storage_account}.dfs.core.windows.net/streaming/carbon_intensity"
SILVER_PATH = f"abfss://silver@{storage_account}.dfs.core.windows.net/streaming/carbon_intensity"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Consume Events from Event Hub → Save to Bronze

# COMMAND ----------

import json
from azure.eventhub import EventHubConsumerClient
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType
from datetime import datetime

# Collect events from Event Hub
all_events = []

def on_event(partition_context, event):
    body = event.body_as_str()
    all_events.append({
        "raw_json": body,
        "partition_id": partition_context.partition_id,
        "enqueued_time": str(event.enqueued_time),
        "sequence_number": event.sequence_number
    })
    partition_context.update_checkpoint(event)

# Consumer reads from Event Hub
consumer = EventHubConsumerClient.from_connection_string(
    conn_str=EVENT_HUB_CONNECTION_STRING,
    consumer_group="$Default",
    eventhub_name=EVENT_HUB_NAME
)

print("Reading events from Event Hub (60 seconds)...")
print("Make sure the producer script is running!")

import threading

def receive_events():
    with consumer:
        consumer.receive(
            on_event=on_event,
            starting_position="-1",
            max_wait_time=60
        )

# Run consumer in background thread with timeout
thread = threading.Thread(target=receive_events)
thread.start()
thread.join(timeout=65)

print(f"\nReceived {len(all_events)} events from Event Hub")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Save Raw Events to Bronze Layer

# COMMAND ----------

if len(all_events) > 0:
    import pandas as pd

    pdf_bronze = pd.DataFrame(all_events)
    df_bronze = spark.createDataFrame(pdf_bronze)

    df_bronze.write.mode("append").parquet(f"{BRONZE_PATH}/raw/")
    print(f"Bronze: Saved {df_bronze.count()} raw events to ADLS")
    df_bronze.show(5, truncate=False)
else:
    print("No events received! Make sure producer is running.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Parse JSON → Create Silver Layer

# COMMAND ----------

# Read ONLY the latest Bronze data (last 10 minutes)
df_bronze_all = spark.read.parquet(f"{BRONZE_PATH}/raw/")
df_bronze_all = df_bronze_all \
    .withColumn("enqueued_ts", F.col("enqueued_time").cast("timestamp")) \
    .filter(F.col("enqueued_ts") >= F.current_timestamp() - F.expr("INTERVAL 10 MINUTES"))
print(f"Latest Bronze records (last 10 min): {df_bronze_all.count()}")

# Define schema for parsing
carbon_schema = StructType([
    StructField("event_type", StringType()),
    StructField("timestamp", StringType()),
    StructField("from", StringType()),
    StructField("to", StringType()),
    StructField("forecast", DoubleType()),
    StructField("actual", DoubleType()),
    StructField("index", StringType()),
    StructField("fuel", StringType()),
    StructField("percentage", DoubleType()),
    StructField("region_id", IntegerType()),
    StructField("region_name", StringType()),
    StructField("dno_region", StringType()),
])

# Parse JSON and create Silver
df_silver = df_bronze_all \
    .withColumn("parsed", F.from_json(F.col("raw_json"), carbon_schema)) \
    .select(
        F.col("enqueued_time").cast("timestamp").alias("event_time"),
        F.col("parsed.event_type").alias("event_type"),
        F.col("parsed.timestamp").cast("timestamp").alias("data_timestamp"),
        F.col("parsed.from").alias("period_from"),
        F.col("parsed.to").alias("period_to"),
        F.col("parsed.forecast").alias("forecast"),
        F.col("parsed.actual").alias("actual"),
        F.col("parsed.index").alias("intensity_index"),
        F.col("parsed.fuel").alias("fuel_type"),
        F.col("parsed.percentage").alias("fuel_percentage"),
        F.col("parsed.region_id").alias("region_id"),
        F.col("parsed.region_name").alias("region_name"),
        F.col("parsed.dno_region").alias("dno_region"),
    ) \
    .withColumn("_processed_timestamp", F.current_timestamp())

df_silver.write.mode("overwrite").partitionBy("event_type").parquet(f"{SILVER_PATH}/")
print(f"Silver: Saved {df_silver.count()} parsed records")

# Show summary by event type
df_silver.groupBy("event_type").count().show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Preview Silver Data

# COMMAND ----------

print("=== National Intensity ===")
df_silver.filter(F.col("event_type") == "national_intensity").show(5, truncate=False)

print("=== Generation Mix ===")
df_silver.filter(F.col("event_type") == "generation_mix").show(5, truncate=False)

print("=== Regional Intensity ===")
df_silver.filter(F.col("event_type") == "regional_intensity").show(5, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Run Again to Accumulate More Data
# MAGIC Re-run cells 3-4 (Event Hub consumer) every few minutes to pull new events.
# MAGIC Each run appends to Bronze and overwrites Silver with all accumulated data.
# MAGIC
# MAGIC For continuous streaming, schedule this notebook to run every 5 minutes using ADF or Databricks Jobs.

# COMMAND ----------

print("=== STREAMING BRONZE & SILVER COMPLETE ===")
print(f"Bronze path: {BRONZE_PATH}/raw/")
print(f"Silver path: {SILVER_PATH}/")
print(f"Total events processed: {df_silver.count()}")

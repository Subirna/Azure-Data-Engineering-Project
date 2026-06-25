# Databricks notebook source
# MAGIC %md
# MAGIC # Streaming — Bronze & Silver Layer
# MAGIC Reads real-time carbon intensity data from Azure Event Hub using Structured Streaming.
# MAGIC Writes to Bronze (raw) and Silver (cleansed) layers in ADLS Gen2.
# MAGIC
# MAGIC **Prerequisites:**
# MAGIC - Event Hub namespace: eh-uk-traffic-subira
# MAGIC - Event Hub name: carbon-intensity-stream
# MAGIC - Producer script running (01_producer_carbon_intensity.py)

# COMMAND ----------

# Storage config
storage_account = "subiradls2026"
storage_key = "<PASTE_KEY_FROM_AZURE_PORTAL: subiradls2026 > Security + networking > Access keys > key1>"

spark.conf.set(
    f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
    storage_key
)

# Event Hub config
EVENT_HUB_CONNECTION_STRING = "<PASTE_YOUR_EVENT_HUB_CONNECTION_STRING>"
EVENT_HUB_NAME = "carbon-intensity-stream"

BRONZE_PATH = f"abfss://bronze@{storage_account}.dfs.core.windows.net/streaming/carbon_intensity"
SILVER_PATH = f"abfss://silver@{storage_account}.dfs.core.windows.net/streaming/carbon_intensity"
CHECKPOINT_PATH = f"abfss://bronze@{storage_account}.dfs.core.windows.net/streaming/_checkpoints"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Event Hub Connection Config

# COMMAND ----------

ehConf = {
    "eventhubs.connectionString": sc._jvm.org.apache.spark.eventhubs.EventHubsUtils.encrypt(
        f"{EVENT_HUB_CONNECTION_STRING};EntityPath={EVENT_HUB_NAME}"
    ),
    "eventhubs.consumerGroup": "$Default",
    "eventhubs.startingPosition": '{"offset": "-1", "seqNo": -1, "enqueuedTime": null, "isInclusive": true}'
}

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze: Read Raw Stream from Event Hub

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType

# Read from Event Hub
raw_stream = spark \
    .readStream \
    .format("eventhubs") \
    .options(**ehConf) \
    .load()

# Parse the body (Event Hub sends bytes)
bronze_stream = raw_stream \
    .withColumn("body_str", F.col("body").cast(StringType())) \
    .withColumn("enqueuedTime", F.col("enqueuedTime").cast("timestamp")) \
    .select(
        F.col("enqueuedTime").alias("event_time"),
        F.col("body_str").alias("raw_json"),
        F.col("partitionId").alias("partition_id"),
        F.col("sequenceNumber").alias("sequence_number")
    )

# Write Bronze (raw JSON) to ADLS
bronze_query = bronze_stream \
    .writeStream \
    .format("parquet") \
    .option("path", f"{BRONZE_PATH}/raw/") \
    .option("checkpointLocation", f"{CHECKPOINT_PATH}/bronze/") \
    .outputMode("append") \
    .trigger(processingTime="30 seconds") \
    .start()

print("Bronze streaming started...")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver: Parse JSON and Cleanse

# COMMAND ----------

# Define schema for the carbon intensity JSON
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

# Read Bronze stream and parse JSON
silver_stream = spark \
    .readStream \
    .format("parquet") \
    .schema(bronze_stream.schema) \
    .load(f"{BRONZE_PATH}/raw/") \
    .withColumn("parsed", F.from_json(F.col("raw_json"), carbon_schema)) \
    .select(
        F.col("event_time"),
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

# Write Silver to ADLS
silver_query = silver_stream \
    .writeStream \
    .format("parquet") \
    .option("path", f"{SILVER_PATH}/") \
    .option("checkpointLocation", f"{CHECKPOINT_PATH}/silver/") \
    .outputMode("append") \
    .trigger(processingTime="30 seconds") \
    .partitionBy("event_type") \
    .start()

print("Silver streaming started...")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Monitor Streams

# COMMAND ----------

# Check active streams
for stream in spark.streams.active:
    print(f"Stream: {stream.name}, Status: {stream.status}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Stop Streams (run when done)

# COMMAND ----------

# # Uncomment to stop all streams
# for stream in spark.streams.active:
#     stream.stop()
# print("All streams stopped.")

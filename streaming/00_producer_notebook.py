# Databricks notebook source
# MAGIC %md
# MAGIC # Streaming Producer — Runs in Databricks
# MAGIC Fetches UK Carbon Intensity data and sends to Event Hub.
# MAGIC Runs for 2 minutes (4 cycles × 30 seconds) then stops.
# MAGIC
# MAGIC This notebook is called by ADF as the first step in the streaming pipeline.

# COMMAND ----------

# MAGIC %pip install azure-eventhub

# COMMAND ----------

import json
import time
import requests
from azure.eventhub import EventHubProducerClient, EventData
from datetime import datetime

EVENT_HUB_CONNECTION_STRING = "<PASTE_EVENT_HUB_CONNECTION_STRING>"
EVENT_HUB_NAME = "carbon-intensity-stream"

NATIONAL_URL = "https://api.carbonintensity.org.uk/intensity"
REGIONAL_URL = "https://api.carbonintensity.org.uk/regional"
GENERATION_URL = "https://api.carbonintensity.org.uk/generation"

# COMMAND ----------

def fetch_carbon_data():
    messages = []
    timestamp = datetime.utcnow().isoformat()

    try:
        resp = requests.get(NATIONAL_URL, timeout=30)
        data = resp.json()["data"][0]
        messages.append({
            "event_type": "national_intensity",
            "timestamp": timestamp,
            "from": data["from"],
            "to": data["to"],
            "forecast": data["intensity"]["forecast"],
            "actual": data["intensity"]["actual"],
            "index": data["intensity"]["index"]
        })
    except Exception as e:
        print(f"Error fetching national: {e}")

    try:
        resp = requests.get(GENERATION_URL, timeout=30)
        data = resp.json()["data"]
        for fuel in data["generationmix"]:
            messages.append({
                "event_type": "generation_mix",
                "timestamp": timestamp,
                "from": data["from"],
                "to": data["to"],
                "fuel": fuel["fuel"],
                "percentage": fuel["perc"]
            })
    except Exception as e:
        print(f"Error fetching generation: {e}")

    try:
        resp = requests.get(REGIONAL_URL, timeout=30)
        data = resp.json()["data"][0]
        for region in data["regions"]:
            messages.append({
                "event_type": "regional_intensity",
                "timestamp": timestamp,
                "from": data["from"],
                "to": data["to"],
                "region_id": region["regionid"],
                "region_name": region["shortname"],
                "dno_region": region["dnoregion"],
                "forecast": region["intensity"]["forecast"],
                "index": region["intensity"]["index"]
            })
            for fuel in region["generationmix"]:
                messages.append({
                    "event_type": "regional_generation",
                    "timestamp": timestamp,
                    "region_id": region["regionid"],
                    "region_name": region["shortname"],
                    "fuel": fuel["fuel"],
                    "percentage": fuel["perc"]
                })
    except Exception as e:
        print(f"Error fetching regional: {e}")

    return messages

def send_to_event_hub(messages):
    producer = EventHubProducerClient.from_connection_string(
        conn_str=EVENT_HUB_CONNECTION_STRING,
        eventhub_name=EVENT_HUB_NAME
    )
    with producer:
        batch = producer.create_batch()
        for msg in messages:
            batch.add(EventData(json.dumps(msg)))
        producer.send_batch(batch)
    print(f"Sent {len(messages)} events to Event Hub")

# COMMAND ----------

# Run for 4 cycles (2 minutes) then stop
CYCLES = 4
INTERVAL = 30

print(f"Starting producer: {CYCLES} cycles, {INTERVAL}s interval")
for i in range(CYCLES):
    messages = fetch_carbon_data()
    send_to_event_hub(messages)
    print(f"Cycle {i+1}/{CYCLES} complete — {len(messages)} events")
    if i < CYCLES - 1:
        time.sleep(INTERVAL)

print(f"\n=== PRODUCER COMPLETE — {CYCLES} cycles finished ===")

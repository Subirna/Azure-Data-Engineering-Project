"""
Streaming Producer — UK Carbon Intensity Data
Fetches real-time carbon intensity data from carbonintensity.org.uk API
and sends it to Azure Event Hub every 30 seconds.

Run this locally or in Azure Function to simulate streaming.

Setup:
  pip install azure-eventhub requests

  Set environment variables:
    EVENT_HUB_CONNECTION_STRING=Endpoint=sb://eh-uk-traffic-subira.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=xxx
    EVENT_HUB_NAME=carbon-intensity-stream
"""

import json
import time
import logging
from datetime import datetime

import requests
from azure.eventhub import EventHubProducerClient, EventData

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Configuration
EVENT_HUB_CONNECTION_STRING = "<PASTE_YOUR_EVENT_HUB_CONNECTION_STRING>"
EVENT_HUB_NAME = "carbon-intensity-stream"

# API Endpoints
NATIONAL_URL = "https://api.carbonintensity.org.uk/intensity"
REGIONAL_URL = "https://api.carbonintensity.org.uk/regional"
GENERATION_URL = "https://api.carbonintensity.org.uk/generation"


def fetch_carbon_data():
    """Fetch national intensity, regional data, and generation mix."""
    messages = []
    timestamp = datetime.utcnow().isoformat()

    # National intensity
    try:
        resp = requests.get(NATIONAL_URL, timeout=30)
        data = resp.json()["data"][0]
        msg = {
            "event_type": "national_intensity",
            "timestamp": timestamp,
            "from": data["from"],
            "to": data["to"],
            "forecast": data["intensity"]["forecast"],
            "actual": data["intensity"]["actual"],
            "index": data["intensity"]["index"]
        }
        messages.append(msg)
    except Exception as e:
        logger.error(f"Failed to fetch national intensity: {e}")

    # Generation mix
    try:
        resp = requests.get(GENERATION_URL, timeout=30)
        data = resp.json()["data"]
        for fuel in data["generationmix"]:
            msg = {
                "event_type": "generation_mix",
                "timestamp": timestamp,
                "from": data["from"],
                "to": data["to"],
                "fuel": fuel["fuel"],
                "percentage": fuel["perc"]
            }
            messages.append(msg)
    except Exception as e:
        logger.error(f"Failed to fetch generation mix: {e}")

    # Regional intensity
    try:
        resp = requests.get(REGIONAL_URL, timeout=30)
        data = resp.json()["data"][0]
        for region in data["regions"]:
            msg = {
                "event_type": "regional_intensity",
                "timestamp": timestamp,
                "from": data["from"],
                "to": data["to"],
                "region_id": region["regionid"],
                "region_name": region["shortname"],
                "dno_region": region["dnoregion"],
                "forecast": region["intensity"]["forecast"],
                "index": region["intensity"]["index"]
            }
            messages.append(msg)

            # Also send generation mix per region
            for fuel in region["generationmix"]:
                fuel_msg = {
                    "event_type": "regional_generation",
                    "timestamp": timestamp,
                    "region_id": region["regionid"],
                    "region_name": region["shortname"],
                    "fuel": fuel["fuel"],
                    "percentage": fuel["perc"]
                }
                messages.append(fuel_msg)
    except Exception as e:
        logger.error(f"Failed to fetch regional data: {e}")

    return messages


def send_to_event_hub(messages):
    """Send messages to Azure Event Hub."""
    producer = EventHubProducerClient.from_connection_string(
        conn_str=EVENT_HUB_CONNECTION_STRING,
        eventhub_name=EVENT_HUB_NAME
    )

    with producer:
        event_data_batch = producer.create_batch()
        for msg in messages:
            event_data_batch.add(EventData(json.dumps(msg)))
        producer.send_batch(event_data_batch)

    logger.info(f"Sent {len(messages)} events to Event Hub")


def main():
    """Main loop — fetch and send data every 30 seconds."""
    logger.info("=" * 60)
    logger.info("UK Carbon Intensity Streaming Producer Started")
    logger.info(f"Event Hub: {EVENT_HUB_NAME}")
    logger.info("=" * 60)

    while True:
        try:
            messages = fetch_carbon_data()
            send_to_event_hub(messages)
            logger.info(f"Cycle complete — {len(messages)} events sent. Sleeping 30s...")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")

        time.sleep(30)


if __name__ == "__main__":
    main()

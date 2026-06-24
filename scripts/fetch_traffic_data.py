"""
Fetch UK Road Traffic Count data from the DfT API.
Saves raw JSON responses locally for upload to ADLS Gen2 Bronze layer.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path

import requests
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://roadtraffic.dft.gov.uk/api"
OUTPUT_DIR = Path("Data/raw/traffic")

ENDPOINTS = {
    "count_points": {"path": "/count-points", "params": {"limit": 50000}},
    "counts": {"path": "/counts", "params": {"limit": 100000}},
    "regions": {"path": "/regions", "params": {}},
    "local_authorities": {"path": "/local-authorities", "params": {}},
}


def fetch_endpoint(name: str, config: dict) -> dict:
    url = f"{BASE_URL}{config['path']}"
    logger.info(f"Fetching {name} from {url}")

    response = requests.get(url, params=config["params"], timeout=300)
    response.raise_for_status()

    data = response.json()
    row_count = len(data.get("rows", []))
    logger.info(f"  Received {row_count} rows for {name}")
    return data


def save_json(data: dict, name: str) -> Path:
    date_str = datetime.now().strftime("%Y%m%d")
    output_path = OUTPUT_DIR / name / date_str
    output_path.mkdir(parents=True, exist_ok=True)

    file_path = output_path / f"{name}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    logger.info(f"  Saved to {file_path}")
    return file_path


def save_csv(data: dict, name: str) -> Path:
    date_str = datetime.now().strftime("%Y%m%d")
    output_path = OUTPUT_DIR / name / date_str
    output_path.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(data.get("rows", []))
    file_path = output_path / f"{name}.csv"
    df.to_csv(file_path, index=False)

    logger.info(f"  Saved CSV to {file_path} ({len(df)} rows)")
    return file_path


def main():
    logger.info("=" * 60)
    logger.info("UK Road Traffic Data Ingestion")
    logger.info("=" * 60)

    for name, config in ENDPOINTS.items():
        try:
            data = fetch_endpoint(name, config)
            save_json(data, name)
            save_csv(data, name)
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {name}: {e}")
        except Exception as e:
            logger.error(f"Error processing {name}: {e}")

    logger.info("Traffic data ingestion complete.")


if __name__ == "__main__":
    main()

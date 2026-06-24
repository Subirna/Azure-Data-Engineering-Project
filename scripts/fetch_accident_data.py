"""
Fetch UK STATS19 Road Accident data from data.dft.gov.uk.
Downloads collision, vehicle, and casualty CSV files.
"""

import logging
from datetime import datetime
from pathlib import Path

import requests
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("Data/raw/accidents")

ACCIDENT_FILES = {
    "collisions": "https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-collision-2023.csv",
    "vehicles": "https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-vehicle-2023.csv",
    "casualties": "https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-casualty-2023.csv",
}


def download_csv(name: str, url: str) -> Path:
    logger.info(f"Downloading {name} from {url}")

    response = requests.get(url, timeout=120, stream=True)
    response.raise_for_status()

    date_str = datetime.now().strftime("%Y%m%d")
    output_path = OUTPUT_DIR / name / date_str
    output_path.mkdir(parents=True, exist_ok=True)

    file_path = output_path / f"{name}.csv"
    with open(file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    df = pd.read_csv(file_path)
    logger.info(f"  Saved {file_path} ({len(df)} rows, {len(df.columns)} columns)")

    return file_path


def main():
    logger.info("=" * 60)
    logger.info("UK Road Accident Data (STATS19) Ingestion")
    logger.info("=" * 60)

    for name, url in ACCIDENT_FILES.items():
        try:
            download_csv(name, url)
        except requests.RequestException as e:
            logger.error(f"Failed to download {name}: {e}")
        except Exception as e:
            logger.error(f"Error processing {name}: {e}")

    logger.info("Accident data ingestion complete.")


if __name__ == "__main__":
    main()

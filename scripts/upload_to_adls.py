"""
Upload local raw data files to Azure Data Lake Storage Gen2 Bronze layer.
"""

import os
import logging
from pathlib import Path

from azure.identity import DefaultAzureCredential
from azure.storage.filedatalake import DataLakeServiceClient
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

STORAGE_ACCOUNT = os.getenv("ADLS_STORAGE_ACCOUNT", "uktrafficdldev")
CONTAINER_NAME = "bronze"
LOCAL_DATA_DIR = Path("Data/raw")


def get_datalake_client() -> DataLakeServiceClient:
    credential = DefaultAzureCredential()
    account_url = f"https://{STORAGE_ACCOUNT}.dfs.core.windows.net"
    return DataLakeServiceClient(account_url=account_url, credential=credential)


def upload_file(service_client: DataLakeServiceClient, local_path: Path, remote_path: str):
    file_system_client = service_client.get_file_system_client(CONTAINER_NAME)
    file_client = file_system_client.get_file_client(remote_path)

    with open(local_path, "rb") as f:
        file_client.upload_data(f, overwrite=True)

    logger.info(f"  Uploaded {local_path} -> {CONTAINER_NAME}/{remote_path}")


def upload_directory(service_client: DataLakeServiceClient, local_dir: Path, remote_prefix: str):
    if not local_dir.exists():
        logger.warning(f"  Directory {local_dir} does not exist, skipping.")
        return

    for file_path in local_dir.rglob("*"):
        if file_path.is_file():
            relative = file_path.relative_to(local_dir)
            remote_path = f"{remote_prefix}/{relative.as_posix()}"
            upload_file(service_client, file_path, remote_path)


def main():
    logger.info("=" * 60)
    logger.info("Upload Raw Data to ADLS Gen2 Bronze Layer")
    logger.info("=" * 60)

    service_client = get_datalake_client()

    datasets = [
        ("traffic", "traffic"),
        ("accidents", "accidents"),
    ]

    for local_name, remote_name in datasets:
        local_dir = LOCAL_DATA_DIR / local_name
        logger.info(f"Uploading {local_name} -> {CONTAINER_NAME}/{remote_name}/")
        upload_directory(service_client, local_dir, remote_name)

    logger.info("Upload complete.")


if __name__ == "__main__":
    main()

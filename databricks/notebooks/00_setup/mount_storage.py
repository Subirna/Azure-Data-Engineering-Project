# Databricks notebook source
# MAGIC %md
# MAGIC # Mount ADLS Gen2 Storage
# MAGIC Mounts Bronze, Silver, and Gold containers from Azure Data Lake Storage Gen2.

# COMMAND ----------

configs = {
    "fs.azure.account.auth.type": "OAuth",
    "fs.azure.account.oauth.provider.type": "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider",
    "fs.azure.account.oauth2.client.id": dbutils.secrets.get(scope="uk-traffic-scope", key="sp-client-id"),
    "fs.azure.account.oauth2.client.secret": dbutils.secrets.get(scope="uk-traffic-scope", key="sp-client-secret"),
    "fs.azure.account.oauth2.client.endpoint": dbutils.secrets.get(scope="uk-traffic-scope", key="sp-token-endpoint"),
}

STORAGE_ACCOUNT = "uktrafficdldev"

# COMMAND ----------

def mount_container(container_name):
    mount_point = f"/mnt/{container_name}"
    source = f"abfss://{container_name}@{STORAGE_ACCOUNT}.dfs.core.windows.net/"

    if any(mount.mountPoint == mount_point for mount in dbutils.fs.mounts()):
        print(f"  {mount_point} already mounted, skipping.")
        return

    dbutils.fs.mount(source=source, mount_point=mount_point, extra_configs=configs)
    print(f"  {mount_point} mounted successfully.")


for container in ["bronze", "silver", "gold"]:
    mount_container(container)

# COMMAND ----------

dbutils.fs.ls("/mnt/bronze")

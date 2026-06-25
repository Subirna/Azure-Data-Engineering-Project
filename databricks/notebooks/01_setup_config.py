# Databricks notebook source
# MAGIC %md
# MAGIC # 01 - Setup Storage Configuration
# MAGIC Configures access to Azure Data Lake Storage Gen2.
# MAGIC Run this FIRST before any other notebook.

# COMMAND ----------

storage_account = "subiradls2026"
storage_key = dbutils.widgets.get("storage_key") if "storage_key" in [w.name for w in dbutils.widgets.getAll()] else "<PASTE_YOUR_KEY_IN_DATABRICKS>"

spark.conf.set(
    f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
    storage_key
)

# Verify connection
files = dbutils.fs.ls(f"abfss://bronze@{storage_account}.dfs.core.windows.net/traffic/")
for f in files:
    print(f.name, f.size)

print("\n=== STORAGE CONFIGURED SUCCESSFULLY ===")

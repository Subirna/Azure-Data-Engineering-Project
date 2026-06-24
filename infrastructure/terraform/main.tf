terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.85.0"
    }
  }

  backend "azurerm" {
    resource_group_name  = "rg-terraform-state"
    storage_account_name = "tfstateuktraffic"
    container_name       = "tfstate"
    key                  = "uk-traffic.terraform.tfstate"
  }
}

provider "azurerm" {
  features {}
}

data "azurerm_client_config" "current" {}

# ──────────────────────────────────────────────
# Resource Group
# ──────────────────────────────────────────────
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}

# ──────────────────────────────────────────────
# Modules
# ──────────────────────────────────────────────
module "key_vault" {
  source              = "./modules/key_vault"
  key_vault_name      = var.key_vault_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tenant_id           = data.azurerm_client_config.current.tenant_id
  object_id           = data.azurerm_client_config.current.object_id
  tags                = var.tags
}

module "data_lake" {
  source               = "./modules/data_lake"
  storage_account_name = var.storage_account_name
  resource_group_name  = azurerm_resource_group.main.name
  location             = azurerm_resource_group.main.location
  tags                 = var.tags
}

module "data_factory" {
  source              = "./modules/data_factory"
  data_factory_name   = var.data_factory_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  key_vault_id        = module.key_vault.key_vault_id
  storage_account_id  = module.data_lake.storage_account_id
  tags                = var.tags
}

module "databricks" {
  source                    = "./modules/databricks"
  databricks_workspace_name = var.databricks_workspace_name
  resource_group_name       = azurerm_resource_group.main.name
  location                  = azurerm_resource_group.main.location
  tags                      = var.tags
}

module "synapse" {
  source                     = "./modules/synapse"
  synapse_workspace_name     = var.synapse_workspace_name
  resource_group_name        = azurerm_resource_group.main.name
  location                   = azurerm_resource_group.main.location
  storage_account_id         = module.data_lake.storage_account_id
  storage_account_url        = module.data_lake.primary_dfs_endpoint
  synapse_sql_admin_login    = var.synapse_sql_admin_login
  synapse_sql_admin_password = var.synapse_sql_admin_password
  tags                       = var.tags
}

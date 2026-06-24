variable "synapse_workspace_name" { type = string }
variable "resource_group_name" { type = string }
variable "location" { type = string }
variable "storage_account_id" { type = string }
variable "storage_account_url" { type = string }
variable "synapse_sql_admin_login" { type = string }
variable "synapse_sql_admin_password" {
  type      = string
  sensitive = true
}
variable "tags" { type = map(string) }

resource "azurerm_synapse_workspace" "main" {
  name                                 = var.synapse_workspace_name
  resource_group_name                  = var.resource_group_name
  location                             = var.location
  storage_data_lake_gen2_filesystem_id = "${var.storage_account_id}/default/gold"
  sql_administrator_login              = var.synapse_sql_admin_login
  sql_administrator_login_password     = var.synapse_sql_admin_password
  tags                                 = var.tags

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_synapse_sql_pool" "dedicated" {
  name                 = "traffic_dwh"
  synapse_workspace_id = azurerm_synapse_workspace.main.id
  sku_name             = "DW100c"
  create_mode          = "Default"
  tags                 = var.tags
}

resource "azurerm_synapse_firewall_rule" "allow_azure" {
  name                 = "AllowAllAzureIps"
  synapse_workspace_id = azurerm_synapse_workspace.main.id
  start_ip_address     = "0.0.0.0"
  end_ip_address       = "0.0.0.0"
}

output "synapse_workspace_name" {
  value = azurerm_synapse_workspace.main.name
}

output "synapse_workspace_id" {
  value = azurerm_synapse_workspace.main.id
}

output "sql_pool_name" {
  value = azurerm_synapse_sql_pool.dedicated.name
}

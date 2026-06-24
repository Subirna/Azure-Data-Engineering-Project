variable "data_factory_name" { type = string }
variable "resource_group_name" { type = string }
variable "location" { type = string }
variable "key_vault_id" { type = string }
variable "storage_account_id" { type = string }
variable "tags" { type = map(string) }

resource "azurerm_data_factory" "main" {
  name                = var.data_factory_name
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags

  identity {
    type = "SystemAssigned"
  }

  global_parameter {
    name  = "environment"
    type  = "String"
    value = "dev"
  }
}

resource "azurerm_data_factory_linked_service_key_vault" "key_vault" {
  name            = "ls_key_vault"
  data_factory_id = azurerm_data_factory.main.id
  key_vault_id    = var.key_vault_id
}

resource "azurerm_data_factory_linked_service_data_lake_storage_gen2" "adls" {
  name                 = "ls_adls_gen2"
  data_factory_id      = azurerm_data_factory.main.id
  storage_account_key  = null
  url                  = "https://${split("/", var.storage_account_id)[8]}.dfs.core.windows.net"
  use_managed_identity = true
}

output "data_factory_name" {
  value = azurerm_data_factory.main.name
}

output "data_factory_id" {
  value = azurerm_data_factory.main.id
}

output "data_factory_identity" {
  value = azurerm_data_factory.main.identity[0].principal_id
}

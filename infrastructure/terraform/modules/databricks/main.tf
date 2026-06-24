variable "databricks_workspace_name" { type = string }
variable "resource_group_name" { type = string }
variable "location" { type = string }
variable "tags" { type = map(string) }

resource "azurerm_databricks_workspace" "main" {
  name                        = var.databricks_workspace_name
  resource_group_name         = var.resource_group_name
  location                    = var.location
  sku                         = "standard"
  managed_resource_group_name = "${var.resource_group_name}-databricks-managed"
  tags                        = var.tags

  custom_parameters {
    no_public_ip = true
  }
}

output "workspace_url" {
  value = azurerm_databricks_workspace.main.workspace_url
}

output "workspace_id" {
  value = azurerm_databricks_workspace.main.workspace_id
}

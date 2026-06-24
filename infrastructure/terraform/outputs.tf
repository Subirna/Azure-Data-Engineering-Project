output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "storage_account_name" {
  value = module.data_lake.storage_account_name
}

output "storage_account_primary_dfs_endpoint" {
  value = module.data_lake.primary_dfs_endpoint
}

output "data_factory_name" {
  value = module.data_factory.data_factory_name
}

output "data_factory_id" {
  value = module.data_factory.data_factory_id
}

output "databricks_workspace_url" {
  value = module.databricks.workspace_url
}

output "synapse_workspace_name" {
  value = module.synapse.synapse_workspace_name
}

output "key_vault_uri" {
  value = module.key_vault.key_vault_uri
}

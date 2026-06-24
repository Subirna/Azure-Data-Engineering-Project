variable "resource_group_name" {
  description = "Name of the Azure resource group"
  type        = string
  default     = "rg-uk-traffic-dev"
}

variable "location" {
  description = "Azure region for all resources"
  type        = string
  default     = "uksouth"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "uk-traffic"
}

variable "storage_account_name" {
  description = "Name of the ADLS Gen2 storage account"
  type        = string
  default     = "uktrafficdldev"
}

variable "data_factory_name" {
  description = "Name of the Azure Data Factory"
  type        = string
  default     = "adf-uk-traffic-dev"
}

variable "databricks_workspace_name" {
  description = "Name of the Databricks workspace"
  type        = string
  default     = "dbw-uk-traffic-dev"
}

variable "synapse_workspace_name" {
  description = "Name of the Synapse workspace"
  type        = string
  default     = "syn-uk-traffic-dev"
}

variable "key_vault_name" {
  description = "Name of the Azure Key Vault"
  type        = string
  default     = "kv-uk-traffic-dev"
}

variable "synapse_sql_admin_login" {
  description = "SQL admin username for Synapse"
  type        = string
  default     = "sqladminuser"
}

variable "synapse_sql_admin_password" {
  description = "SQL admin password for Synapse"
  type        = string
  sensitive   = true
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    environment = "dev"
    project     = "uk-traffic-intelligence"
    owner       = "data-engineering"
    managed_by  = "terraform"
  }
}

# 1. Create the main resource group for the function app
resource "azurerm_resource_group" "rg" {
  location = var.location
  name     = var.resourceGroupName
}

resource "azurerm_service_plan" "app_service_plan" {
  name                = var.functionPlanName
  resource_group_name = azurerm_resource_group.rg.name
  location            = var.location
  sku_name            = "FC1"
  os_type             = "Linux"
  zone_balancing_enabled = var.zoneRedundant
}

resource "azurerm_storage_account" "storageAccount" {
  name                     = var.storageAccountName
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_storage_container" "storageContainer" {
  name                  = "deploymentpackage"
  storage_account_id  = azurerm_storage_account.storageAccount.id
  container_access_type = "private"
}

resource "azurerm_log_analytics_workspace" "logAnalyticsWorkspace" {
  name                = var.logAnalyticsName
  location            = var.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_application_insights" "appInsights" {
  name                = var.applicationInsightsName
  location            = var.location
  resource_group_name = azurerm_resource_group.rg.name
  application_type    = "web"
  workspace_id = azurerm_log_analytics_workspace.logAnalyticsWorkspace.id
}

resource "azurerm_function_app_flex_consumption" "functionApps" {
  name                        = var.functionAppName
  resource_group_name         = azurerm_resource_group.rg.name
  location                    = var.location
  service_plan_id             = azurerm_service_plan.app_service_plan.id
  
  storage_container_type      = "blobContainer"
  storage_container_endpoint  = "${azurerm_storage_account.storageAccount.primary_blob_endpoint}${azurerm_storage_container.storageContainer.name}"
  storage_authentication_type = "StorageAccountConnectionString"
  storage_access_key          = azurerm_storage_account.storageAccount.primary_access_key
  runtime_name                = var.functionAppRuntime
  runtime_version             = var.functionAppRuntimeVersion
  maximum_instance_count      = var.maximumInstanceCount
  instance_memory_in_mb       = var.instanceMemoryMB
  
  site_config {
    application_insights_connection_string = azurerm_application_insights.appInsights.connection_string
  }
  timeouts {
    create = "60m"
    update = "30m"
    delete = "30m"
  }
  app_settings = {
    # "AzureWebJobsStorage" = azurerm_storage_account.storageAccount.primary_connection_string //workaround until https://github.com/hashicorp/terraform-provider-azurerm/pull/29099 gets released
    "AzureWebJobsStorage__accountName" = azurerm_storage_account.storageAccount.name
    "AZURE_STORAGE_CONNECTION_STRING"       = azurerm_storage_account.botstorage.primary_connection_string
    "BINANCE_API_KEY"                       = var.binance_api_key
    "BINANCE_API_SECRET"                    = var.binance_api_secret
  }
}

# resource "azurerm_role_assignment" "storage_roleassignment" {
#   scope = azurerm_storage_account.storageAccount.id
#   role_definition_name = "Storage Blob Data Owner"
#   principal_id = azurerm_function_app_flex_consumption.functionApps.identity[0].principal_id
#   principal_type = "ServicePrincipal"
# }

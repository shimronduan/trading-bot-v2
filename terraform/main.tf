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
  allow_nested_items_to_be_public = false
  shared_access_key_enabled = true
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

locals {
  blobStorageAndContainer = "${azurerm_storage_account.storageAccount.primary_blob_endpoint}deploymentpackage"
}

resource "azurerm_function_app_flex_consumption" "functionApps" {
  name                        = var.functionAppName
  resource_group_name         = azurerm_resource_group.rg.name
  location                    = var.location
  service_plan_id             = azurerm_service_plan.app_service_plan.id
  storage_container_type      = "blobContainer"
  storage_container_endpoint  = local.blobStorageAndContainer
  storage_authentication_type = "StorageAccountConnectionString"
  runtime_name                = var.functionAppRuntime
  runtime_version             = var.functionAppRuntimeVersion
  maximum_instance_count      = var.maximumInstanceCount
  instance_memory_in_mb       = var.instanceMemoryMB
  site_config {
    application_insights_connection_string = azurerm_application_insights.appInsights.connection_string
  }
  app_settings = {
    "AzureWebJobsStorage"                   = azurerm_storage_account.storageAccount.primary_connection_string
    "AZURE_STORAGE_CONNECTION_STRING"       = azurerm_storage_account.botstorage.primary_connection_string
    "BINANCE_API_KEY"                       = var.binance_api_key
    "BINANCE_API_SECRET"                    = var.binance_api_secret
  }
}

resource "azurerm_role_assignment" "storage_roleassignment" {
  scope = azurerm_storage_account.storageAccount.id
  role_definition_name = "Storage Blob Data Owner"
  principal_id = azurerm_function_app_flex_consumption.functionApps.identity.0.principal_id
  principal_type = "ServicePrincipal"
}


# # 5. Create the Linux Function App
# resource "azurerm_linux_function_app" "main" {
#   name                = "trading-bot-app-v2"
#   resource_group_name = azurerm_resource_group.main.name
#   location            = azurerm_resource_group.main.location

#   storage_account_name       = azurerm_storage_account.main.name
#   storage_account_access_key = azurerm_storage_account.main.primary_access_key
#   service_plan_id            = azurerm_service_plan.main.id

#   site_config {
#     application_stack {
#       python_version = "3.12"
#     }
#   }

#   app_settings = {
#     "APPINSIGHTS_INSTRUMENTATIONKEY" = azurerm_application_insights.main.instrumentation_key
#     "FUNCTIONS_EXTENSION_VERSION"           = "~4"
#     "AZURE_STORAGE_CONNECTION_STRING"       = azurerm_storage_account.botstorage.primary_connection_string
#     "BINANCE_API_KEY"                       = var.binance_api_key
#     "BINANCE_API_SECRET"                    = var.binance_api_secret
#   }
# }
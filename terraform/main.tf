# 1. Create the main resource group for the function app
resource "azurerm_resource_group" "main" {
  name     = "trading-bot-${var.app_version}-rg"
  location = "Germany West Central"
}

# 2. Create the storage account required by the function app
resource "azurerm_storage_account" "main" {
  name                     = "tradingbotapp${var.app_version}sa" # Must be globally unique
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

# 4. Create the Consumption Service Plan
resource "azurerm_service_plan" "main" {
  name                = "trading-bot-app-${var.app_version}-plan"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = "Y1" # Y1 is the code for the Consumption plan
}

# 5. Create the Linux Function App
resource "azurerm_linux_function_app" "main" {
  name                = "trading-bot-app-${var.app_version}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location

  storage_account_name       = azurerm_storage_account.main.name
  storage_account_access_key = azurerm_storage_account.main.primary_access_key
  service_plan_id            = azurerm_service_plan.main.id

  site_config {
    application_stack {
      python_version = "3.12"
    }
  }

  app_settings = {
    "APPINSIGHTS_INSTRUMENTATIONKEY" = azurerm_application_insights.main.instrumentation_key
    "FUNCTIONS_EXTENSION_VERSION"           = "~4"
    "AZURE_STORAGE_CONNECTION_STRING"       = azurerm_storage_account.botstorage.primary_connection_string
    "BINANCE_API_KEY"                       = var.binance_api_key
    "BINANCE_API_SECRET"                    = var.binance_api_secret
  }
}
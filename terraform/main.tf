# Configure the Terraform Azure provider and the remote state backend
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.90" # Pinned to a stable version range
    }
  }
  backend "azurerm" {
    # Replace these with the names from your one-time setup
    resource_group_name  = "tfstate-rg"
    storage_account_name = "tfstatesa17329"
    container_name       = "trading-bot-v2-tfstate"
    key                  = "prod.terraform.tfstate"
  }
}

variable "binance_api_key" {
  description = "The API key for the Binance account."
  type        = string
  sensitive   = true 
}
variable "binance_api_secret" {
  description = "The API secret for the Binance account."
  type        = string
  sensitive   = true 
}

# Configure the Azure Provider
provider "azurerm" {
  features {}
}

# 1. Create the main resource group for the function app
resource "azurerm_resource_group" "main" {
  name     = "trading-bot-v2-rg"
  location = "Germany West Central"
}

# 2. Create the storage account required by the function app
resource "azurerm_storage_account" "main" {
  name                     = "tradingbotappv2sa" # Must be globally unique
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

# 2. Create the storage account required by the function app
resource "azurerm_storage_account" "botstorage" {
  name                     = "tradingbotv2sa" # Must be globally unique
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_storage_queue" "orders" {
  name                 = "orders"
  storage_account_name = azurerm_storage_account.botstorage.name
}

resource "azurerm_storage_table" "takeprofitandstoploss" {
  name                 = "TakeProfitAndStopLoss"
  storage_account_name = azurerm_storage_account.botstorage.name
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = "trading-bot-v2-log-analytics"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

# 3. Create the Application Insights for monitoring
resource "azurerm_application_insights" "main" {
  name                = "trading-bot-app-v2-insights"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  application_type    = "web"
  workspace_id        = azurerm_log_analytics_workspace.main.id
}

# 4. Create the Consumption Service Plan
resource "azurerm_service_plan" "main" {
  name                = "trading-bot-app-v2-plan"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = "Y1" # Y1 is the code for the Consumption plan
}

# 5. Create the Linux Function App
resource "azurerm_linux_function_app" "main" {
  name                = "trading-bot-app-v2"
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
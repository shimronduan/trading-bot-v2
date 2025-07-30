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
resource "azurerm_resource_group" "flexrg" {
  name     = "trading-bot-v2-flex-rg"
  location = "Germany West Central"
}

# 2. Create the storage account required by the function app
resource "azurerm_storage_account" "main" {
  name                     = "tradingbotappv2sa" # Must be globally unique
  resource_group_name      = azurerm_resource_group.flexrg.name
  location                 = azurerm_resource_group.flexrg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

# 2. Create the storage account required by the function app
resource "azurerm_storage_account" "botstorage" {
  name                     = "tradingbotv2sa" # Must be globally unique
  resource_group_name      = azurerm_resource_group.flexrg.name
  location                 = azurerm_resource_group.flexrg.location
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
  location            = azurerm_resource_group.flexrg.location
  resource_group_name = azurerm_resource_group.flexrg.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

# 3. Create the Application Insights for monitoring
resource "azurerm_application_insights" "main" {
  name                = "trading-bot-app-v2-insights"
  location            = azurerm_resource_group.flexrg.location
  resource_group_name = azurerm_resource_group.flexrg.name
  application_type    = "web"
  workspace_id        = azurerm_log_analytics_workspace.main.id
}

# 4. Create the Consumption Service Plan
resource "azurerm_service_plan" "main" {
  name                = "trading-bot-app-v2-plan"
  resource_group_name = azurerm_resource_group.flexrg.name
  location            = azurerm_resource_group.flexrg.location
  os_type             = "Linux"
  sku_name            = "FC1" # FC1 is the code for the Flex Consumption plan
}

# 5. Create the Linux Function App
resource "azurerm_linux_function_app" "main" {
  name                = "trading-bot-app-v2"
  resource_group_name = azurerm_resource_group.flexrg.name
  location            = azurerm_resource_group.flexrg.location
  service_plan_id     = azurerm_service_plan.main.id

  storage_account_name       = azurerm_storage_account.main.name
  storage_account_access_key = azurerm_storage_account.main.primary_access_key

  # The 'site_config' block provides the necessary runtime configuration.
  site_config {
    application_stack {
      python_version = "3.12"
    }
    # This setting is also part of the required configuration.
    always_on = false 
  }

  app_settings = {
    "FUNCTIONS_EXTENSION_VERSION"           = "~4"
    "APPINSIGHTS_INSTRUMENTATIONKEY"        = azurerm_application_insights.main.instrumentation_key
    "AZURE_STORAGE_CONNECTION_STRING"       = azurerm_storage_account.botstorage.primary_connection_string
    "BINANCE_API_KEY"                       = var.binance_api_key
    "BINANCE_API_SECRET"                    = var.binance_api_secret
    "WEBSITE_NODE_DEFAULT_VERSION" = "~20"
  }
}
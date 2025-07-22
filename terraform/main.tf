# Configure the Terraform Azure provider and the remote state backend
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.0"
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
  name                     = "tradingbotv2appsa" # Must be globally unique
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

# 3. Create the Application Insights for monitoring
resource "azurerm_application_insights" "main" {
  name                = "trading-bot-v2-app-insights"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  application_type    = "web"
}

# 4. Create the Consumption Service Plan
resource "azurerm_service_plan" "main" {
  name                = "trading-bot-v2-app-plan"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = "Y1" # Y1 is the code for the Consumption plan
}

# 5. Create the Linux Function App
resource "azurerm_linux_function_app" "main" {
  name                = "trading-bot-v2-app"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location

  storage_account_name       = azurerm_storage_account.main.name
  storage_account_access_key = azurerm_storage_account.main.primary_access_key
  service_plan_id            = azurerm_service_plan.main.id

  site_config {
    application_stack {
      python_version = "3.9"
    }
  }

  app_settings = {
    "APPINSIGHTS_INSTRUMENTATIONKEY" = azurerm_application_insights.main.instrumentation_key
    "FUNCTIONS_EXTENSION_VERSION"    = "~4"
  }
}
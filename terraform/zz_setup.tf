terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
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

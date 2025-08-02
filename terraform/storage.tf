# 2. Create the storage account required by the function app
resource "azurerm_storage_account" "botstorage" {
  name                     = "tradingbot${var.app_version}sa" # Must be globally unique
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_storage_queue" "orders" {
  name                 = "orders"
  storage_account_name = azurerm_storage_account.botstorage.name
}

resource "azurerm_storage_queue" "futures" {
  name                 = "futures"
  storage_account_name = azurerm_storage_account.botstorage.name
}

resource "azurerm_storage_table" "takeprofitandstoploss" {
  name                 = "TakeProfitAndStopLoss"
  storage_account_name = azurerm_storage_account.botstorage.name
}
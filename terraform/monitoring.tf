resource "azurerm_log_analytics_workspace" "main" {
  name                = "trading-bot-${var.app_version}-log-analytics"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

# 3. Create the Application Insights for monitoring
resource "azurerm_application_insights" "main" {
  name                = "trading-bot-app-${var.app_version}-insights"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  application_type    = "web"
  workspace_id        = azurerm_log_analytics_workspace.main.id
}

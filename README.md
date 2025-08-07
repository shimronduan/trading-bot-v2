# 🤖 Automated Futures Trading Bot v2

A sophisticated, cloud-native automated trading bot built with Python and Azure Functions that executes futures trades on Binance based on technical analysis signals. The bot features advanced risk management with multiple take-profit levels, trailing stop-losses, and intelligent position management.

## 🏗️ **Architecture Overview**

This trading bot follows a modular, microservices architecture designed for scalability and maintainability:

```
trading-bot-v2/
├── 📁 models/                     # Data structures
│   ├── position_info.py          # Position data class
│   └── symbol_info.py            # Symbol information
├── 📁 managers/                   # Business logic components
│   ├── position_manager.py       # Position operations
│   ├── order_calculator.py       # Trade calculations
│   └── take_profit_stop_loss_manager.py  # TP/SL management
├── 📁 functions/                  # Azure Functions endpoints
│   ├── futures_http_trigger.py   # HTTP webhook receiver
│   ├── futures_queue_trigger.py  # Queue message processor
│   └── futures_handler.py        # Core trading logic
├── 📁 utils/                      # Utility functions
├── 📁 config/                     # Configuration management
├── 📁 terraform/                  # Infrastructure as Code
├── futures_client.py             # Main trading client
├── technical_analysis.py         # TA indicators
└── trading_config.py             # Trading parameters
```

## ✨ **Key Features**

### 🎯 **Advanced Trading Features**
- **Multi-Level Take Profits**: Configurable partial position closing at different ATR levels
- **Trailing Stop Loss**: Dynamic stop-loss adjustment based on market movement
- **Position Management**: Intelligent handling of existing positions and conflicting signals
- **ATR-Based Risk Management**: Uses Average True Range for dynamic risk calculation
- **Leverage Management**: Configurable leverage with automatic position sizing

### 🛡️ **Risk Management**
- **Dynamic Position Sizing**: Calculates trade size based on account balance and risk parameters
- **Minimum Notional Validation**: Ensures all orders meet exchange requirements
- **Order Conflict Prevention**: Cancels existing orders before placing new ones
- **Opposing Position Handling**: Automatically closes opposite positions

### ☁️ **Cloud Infrastructure**
- **Azure Functions**: Serverless compute for cost-effective scaling
- **Queue Processing**: Reliable message processing with retry logic
- **Table Storage**: Configuration and trade history storage
- **Blob Storage**: Log and data persistence
- **Terraform Deployment**: Infrastructure as Code for reproducible deployments

### 📊 **Technical Analysis**
- **ATR (Average True Range)**: For dynamic stop-loss and take-profit calculations
- **Custom Indicators**: Extensible technical analysis framework
- **Real-time Data**: Live market data from Binance Futures API

## 🚀 **Getting Started**

### **Prerequisites**
- Python 3.8+
- Azure subscription (for cloud deployment)
- Binance Futures account with API access
- Git

### **Local Development Setup**

1. **Clone the repository**
```bash
git clone https://github.com/shimronduan/trading-bot-v2.git
cd trading-bot-v2
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
Create a `local.settings.json` file:
```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "your_storage_connection_string",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "BINANCE_API_KEY": "your_binance_api_key",
    "BINANCE_API_SECRET": "your_binance_api_secret",
    "AZURE_STORAGE_CONNECTION_STRING": "your_azure_storage_connection",
    "AZURE_TABLE_STORAGE_CONNECTION_STRING": "your_table_storage_connection"
  }
}
```

5. **Run locally**
```bash
func start
```

## 📋 **Configuration**

### **Trading Parameters** (`trading_config.py`)
```python
SYMBOL = 'DOGEUSDT'              # Trading pair
LEVERAGE = 5                      # Futures leverage
WALLET_ALLOCATION = 0.75          # 75% of available balance
TAKE_PROFIT_PERCENT = 0.005       # 0.5%
STOP_LOSS_PERCENT = 0.005         # 0.5%
```

### **Risk Management Settings**
- **Position Sizing**: Based on account balance and leverage
- **ATR Multipliers**: Configurable for different market conditions
- **Minimum Notional**: Automatic validation against exchange limits

## 🔗 **API Endpoints**

### **HTTP Webhook** (`/api/futures`)
Receives trading signals from external sources (TradingView, custom indicators, etc.)

**Request Body:**
```json
{
  "signal": "Long|Short|Close",
  "symbol": "DOGEUSDT",
  "timestamp": "2025-08-06T12:00:00Z"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "BUY position opened for 1000 DOGEUSDT at ~0.12345",
  "timestamp": "2025-08-06T12:00:00Z"
}
```

### **Queue Processing**
Processes trading signals asynchronously for reliability and scalability.

## 🏗️ **Deployment**

### **Azure Deployment with Terraform**

1. **Configure Terraform variables** (`terraform/vars.tf`)
2. **Initialize Terraform**
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

3. **Deploy function code**
```bash
func azure functionapp publish your-function-app-name
```

### **GitHub Actions CI/CD**
Automated deployment pipeline included for continuous integration.

## 🧪 **Testing**

### **Unit Tests**
```bash
python -m pytest tests/
```

### **Integration Tests**
```bash
python -m pytest tests/integration/
```

### **Manual Testing**
Use the included testing endpoint to validate functionality:
```bash
curl -X POST https://your-function-app.azurewebsites.net/api/testing \
  -H "Content-Type: application/json" \
  -d '{"signal": "Long"}'
```

## 📊 **Monitoring & Logging**

### **Azure Application Insights**
- Real-time performance monitoring
- Error tracking and alerting
- Custom metrics and dashboards

### **Logging Levels**
- **INFO**: Trade executions and position changes
- **WARNING**: Market conditions and validation issues
- **ERROR**: API failures and critical errors

### **Key Metrics**
- Trade success rate
- Average profit/loss per trade
- API response times
- Position sizing accuracy

## 🔒 **Security Best Practices**

### **API Key Management**
- Store keys in Azure Key Vault
- Use managed identities where possible
- Implement key rotation policies

### **Network Security**
- IP whitelisting for webhook endpoints
- HTTPS enforcement
- Function-level authentication

### **Data Protection**
- Encrypted storage for sensitive data
- Audit logging for compliance
- Regular security assessments

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### **Development Guidelines**
- Follow PEP 8 style guidelines
- Add unit tests for new features
- Update documentation for API changes
- Use type hints for better code clarity

## 📝 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ **Disclaimer**

**This trading bot is for educational and research purposes only. Cryptocurrency trading involves significant risk of loss. The authors are not responsible for any financial losses incurred through the use of this software. Always test thoroughly with small amounts and understand the risks before deploying with significant capital.**

## 📞 **Support**

- 📧 **Email**: [your-email@example.com]
- 🐛 **Issues**: [GitHub Issues](https://github.com/shimronduan/trading-bot-v2/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/shimronduan/trading-bot-v2/discussions)

## 🙏 **Acknowledgments**

- [Binance API](https://github.com/binance/binance-connector-python) for trading functionality
- [Azure Functions](https://docs.microsoft.com/en-us/azure/azure-functions/) for serverless computing
- [pandas-ta](https://github.com/twopirllc/pandas-ta) for technical analysis indicators

---

**Happy Trading! 🚀📈**

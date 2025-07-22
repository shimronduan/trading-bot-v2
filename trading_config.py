from decimal import Decimal

# General trading config
USDT_MIN_BALANCE = Decimal('1') 
ZERO_DECIMAL = Decimal('0')
HALF_DECIMAL = Decimal('0.5')

# Stop loss or take profit 
STOP_LOSS_PCT_STANDARD = Decimal('0.01')  # 1% stop loss
TP_TARGET_MULTIPLIER = Decimal('0.001')  # 0.1% profit target

# Stop loss/take profit - oco multipliers
TP_OCO_MULTIPLIER = Decimal('0.008')     # 0.8% take profit OCO
SL_OCO_MULTIPLIER = Decimal('0.0079')    # 0.79% stop loss OCO
SL_LIMIT_OCO_MULTIPLIER = Decimal('0.008') # 0.8% stop loss limit OCO

# Binance formatting
GENERIC_ROUNDING = Decimal('0.00000001')


# Configuration for futures trading
SYMBOL = 'DOGEUSDT'
LEVERAGE = 5
WALLET_ALLOCATION = 0.75  # 75% of available wallet balance
TAKE_PROFIT_PERCENT = 0.005  # 0.5%
STOP_LOSS_PERCENT = 0.005    # 0.5%
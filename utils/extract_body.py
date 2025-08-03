def extractMessageBody(message):
    # Parse each line and extract values
    lines = message.split('\n')
    signal_type = ""
    ticker = None
    price = None
    atr = 0
    if(message.lower().__contains__('close')):
        signal_type = 'Close'
    else:
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                if key == 'Signal':
                    signal_type = "Long" if value == "UT_BUY" else "Short"
                elif key == 'Ticker':
                    ticker = value
                elif key == 'Price':
                    price = float(value)
                elif key == 'ATR':
                    atr = float(value)
    return signal_type, ticker, price, atr
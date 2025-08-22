import azure.functions as func
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from binance.um_futures import UMFutures
from config.configuration import get_env_variables

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Analytics HTTP trigger function processed a request.')
    
    try:
        # Get the interval query parameter
        interval = req.params.get('interval')
        
        if not interval:
            return func.HttpResponse(
                json.dumps({
                    "error": "Missing required query parameter 'interval'",
                    "valid_intervals": ["7d", "30d", "90d", "1yr"],
                    "example": "GET /analytics?interval=7d"
                }),
                status_code=400,
                mimetype="application/json"
            )
        
        # Validate interval parameter
        valid_intervals = ["7d", "30d", "90d", "1yr"]
        if interval not in valid_intervals:
            return func.HttpResponse(
                json.dumps({
                    "error": f"Invalid interval '{interval}'",
                    "valid_intervals": valid_intervals,
                    "example": "GET /analytics?interval=7d"
                }),
                status_code=400,
                mimetype="application/json"
            )
        
        # Calculate date range based on interval
        end_date = datetime.now()
        
        if interval == "7d":
            start_date = end_date - timedelta(days=7)
        elif interval == "30d":
            start_date = end_date - timedelta(days=30)
        elif interval == "90d":
            start_date = end_date - timedelta(days=90)
        elif interval == "1yr":
            start_date = end_date - timedelta(days=365)
        
        logging.info(f"Analytics request for interval: {interval} from {start_date} to {end_date}")
        
        # Initialize Binance Futures client
        env_vars = get_env_variables()
        client = UMFutures(env_vars["API_KEY"], env_vars["API_SECRET"])
        
        # Fetch trades from Binance Futures API
        trades_data = fetch_user_trades(client, start_date, end_date)
        
        # Calculate PnL and aggregate by day
        daily_pnl = calculate_daily_pnl(trades_data)
        
        logging.info(f"Calculated daily PnL: {daily_pnl}")
        
        # Format response as required
        response = []
        for date_str in sorted(daily_pnl.keys()):
            pnl_percent = daily_pnl[date_str]
            formatted_pnl = f"{pnl_percent:+.1f}%" if pnl_percent != 0 else "0.0%"
            response.append({
                "date": date_str,
                "pnl_percent": formatted_pnl
            })
        
        logging.info(f"Final response: {response}")
        
        return func.HttpResponse(
            json.dumps(response, indent=2),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Error in analytics function: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "error": "Internal server error",
                "message": f"An error occurred while processing the analytics request: {str(e)}"
            }),
            status_code=500,
            mimetype="application/json"
        )

def fetch_user_trades(client: UMFutures, start_date: datetime, end_date: datetime) -> list:
    """Fetch user trades from Binance Futures API for the given date range"""
    try:
        all_trades = []
        
        # Get all positions to find symbols that have been traded
        try:
            # Get account information to find symbols with trades
            account_info = client.account()
            traded_symbols = set()
            
            # Check positions for symbols that have been traded
            for position in account_info.get('positions', []):
                if float(position.get('unrealizedPnl', 0)) != 0 or float(position.get('positionAmt', 0)) != 0:
                    traded_symbols.add(position['symbol'])
            
            # If no positions found, try to get from account trades for common symbols
            if not traded_symbols:
                # Add some common trading symbols as fallback
                common_symbols = ['BTCUSDT', 'ETHUSDT', 'DOGEUSDT', 'ADAUSDT', 'DOTUSDT']
                traded_symbols.update(common_symbols)
            
            # Binance API limitation: Maximum time interval is 7 days
            # Split longer periods into 7-day chunks
            current_start = start_date
            
            while current_start < end_date:
                current_end = min(current_start + timedelta(days=7), end_date)
                
                # Convert datetime to milliseconds timestamp for Binance API
                start_timestamp = int(current_start.timestamp() * 1000)
                end_timestamp = int(current_end.timestamp() * 1000)
                
                logging.info(f"Fetching trades for period: {current_start.strftime('%Y-%m-%d')} to {current_end.strftime('%Y-%m-%d')}")
                
                # Fetch trades for each symbol in this 7-day window
                for symbol in traded_symbols:
                    try:
                        symbol_trades = client.get_account_trades(
                            symbol=symbol,
                            startTime=start_timestamp,
                            endTime=end_timestamp,
                            limit=1000  # Maximum allowed by Binance
                        )
                        all_trades.extend(symbol_trades)
                        if len(symbol_trades) > 0:
                            logging.info(f"Fetched {len(symbol_trades)} trades for {symbol} in period {current_start.strftime('%Y-%m-%d')} to {current_end.strftime('%Y-%m-%d')}")
                    except Exception as symbol_error:
                        # Skip symbols that have no trades or cause errors
                        if "Maximum time interval is 7 days" not in str(symbol_error):
                            logging.warning(f"No trades found for {symbol} in period {current_start.strftime('%Y-%m-%d')} to {current_end.strftime('%Y-%m-%d')}: {str(symbol_error)}")
                        continue
                
                # Move to next 7-day window
                current_start = current_end
            
        except Exception as account_error:
            # Fallback: try to get trades for the default symbol from config
            from trading_config import SYMBOL
            logging.warning(f"Could not fetch account info, trying default symbol {SYMBOL}: {str(account_error)}")
            
            # Split into 7-day chunks for fallback as well
            current_start = start_date
            while current_start < end_date:
                current_end = min(current_start + timedelta(days=7), end_date)
                start_timestamp = int(current_start.timestamp() * 1000)
                end_timestamp = int(current_end.timestamp() * 1000)
                
                try:
                    symbol_trades = client.get_account_trades(
                        symbol=SYMBOL,
                        startTime=start_timestamp,
                        endTime=end_timestamp,
                        limit=1000
                    )
                    all_trades.extend(symbol_trades)
                except Exception as fallback_error:
                    logging.warning(f"Error fetching fallback trades for {SYMBOL}: {str(fallback_error)}")
                
                current_start = current_end
        
        logging.info(f"Total fetched {len(all_trades)} trades from Binance Futures API")
        return all_trades
        
    except Exception as e:
        logging.error(f"Error fetching trades from Binance API: {str(e)}")
        raise

def calculate_daily_pnl(trades_data: list) -> dict:
    """Calculate comprehensive PnL percentage including all fees and unrealized PnL"""
    daily_pnl = defaultdict(float)
    
    if not trades_data:
        logging.info("No trades data to process")
        return dict(daily_pnl)
    
    logging.info(f"Processing {len(trades_data)} trades")
    
    # Get Binance client for additional data
    from binance.um_futures import UMFutures
    from config.configuration import get_env_variables
    
    env_vars = get_env_variables()
    client = UMFutures(env_vars["API_KEY"], env_vars["API_SECRET"])
    
    # Group trades by UTC date and calculate comprehensive PnL per day
    daily_realized_pnl = defaultdict(float)
    daily_commission = defaultdict(float)
    daily_trade_values = defaultdict(float)
    
    # Process trades with proper UTC timezone handling
    for trade in trades_data:
        try:
            # Convert timestamp to UTC date properly
            trade_timestamp = int(trade['time']) / 1000
            trade_date_utc = datetime.utcfromtimestamp(trade_timestamp).strftime('%Y-%m-%d')
            
            # Realized PnL from trade
            realized_pnl = float(trade.get('realizedPnl', '0'))
            
            # Commission fees (always negative impact)
            commission = float(trade.get('commission', '0'))
            
            if realized_pnl != 0 or commission != 0:
                daily_realized_pnl[trade_date_utc] += realized_pnl
                daily_commission[trade_date_utc] += commission
                
                # Track trade values
                qty = float(trade['qty'])
                price = float(trade['price'])
                trade_value = qty * price
                daily_trade_values[trade_date_utc] += trade_value
                
                logging.info(f"Trade: {trade['symbol']} on {trade_date_utc} UTC, Realized PnL: {realized_pnl:.4f} USDT, Commission: {commission:.4f} USDT")
            
        except Exception as e:
            logging.warning(f"Error processing trade: {e}")
            continue
    
    # Get funding fees for the date range
    daily_funding_fees = get_funding_fees(client, list(daily_realized_pnl.keys()))
    
    # Get account balance and unrealized PnL
    try:
        account_info = client.account()
        total_wallet_balance = float(account_info.get('totalWalletBalance', 1000))
        total_unrealized_pnl = float(account_info.get('totalUnrealizedPnl', 0))
        
        logging.info(f"Total wallet balance: {total_wallet_balance:.2f} USDT")
        logging.info(f"Total unrealized PnL: {total_unrealized_pnl:.2f} USDT")
        
        # Calculate comprehensive daily PnL percentages
        total_days = len(daily_realized_pnl) if daily_realized_pnl else 1
        
        for date_str in sorted(set(list(daily_realized_pnl.keys()) + list(daily_funding_fees.keys()))):
            # Components of daily PnL
            realized_pnl_usdt = daily_realized_pnl.get(date_str, 0)
            commission_usdt = daily_commission.get(date_str, 0)
            funding_fees_usdt = daily_funding_fees.get(date_str, 0)
            
            # Distribute unrealized PnL proportionally across trading days
            # (This is an approximation since we don't have historical unrealized PnL)
            unrealized_pnl_daily = total_unrealized_pnl / total_days if total_days > 0 else 0
            
            # Total daily PnL = Realized PnL - Commission Fees - Funding Fees + Unrealized PnL portion
            total_daily_pnl_usdt = realized_pnl_usdt - abs(commission_usdt) - abs(funding_fees_usdt) + unrealized_pnl_daily
            
            # Convert to percentage of wallet balance
            if total_wallet_balance > 0:
                pnl_percent = (total_daily_pnl_usdt / total_wallet_balance) * 100
                daily_pnl[date_str] = pnl_percent
                
                logging.info(f"Date: {date_str} UTC - Realized: {realized_pnl_usdt:.2f}, Commission: -{abs(commission_usdt):.2f}, Funding: -{abs(funding_fees_usdt):.2f}, Unrealized portion: {unrealized_pnl_daily:.2f} = Total: {total_daily_pnl_usdt:.2f} USDT ({pnl_percent:.2f}%)")
        
    except Exception as e:
        logging.warning(f"Could not get comprehensive account data: {e}")
        
        # Fallback to basic calculation
        for date_str, realized_pnl_usdt in daily_realized_pnl.items():
            commission_usdt = daily_commission.get(date_str, 0)
            funding_fees_usdt = daily_funding_fees.get(date_str, 0)
            
            # Basic calculation without unrealized PnL
            total_daily_pnl_usdt = realized_pnl_usdt - abs(commission_usdt) - abs(funding_fees_usdt)
            
            # Use trade value as approximation for balance
            daily_trade_value = daily_trade_values[date_str]
            if daily_trade_value > 0:
                estimated_margin = daily_trade_value / 5  # Assume 5x leverage
                pnl_percent = (total_daily_pnl_usdt / estimated_margin) * 100
                daily_pnl[date_str] = pnl_percent
                
                logging.info(f"Date: {date_str} UTC (fallback) - Total PnL: {total_daily_pnl_usdt:.2f} USDT, Est. Percentage: {pnl_percent:.2f}%")
    
    # If no PnL data found, try the position tracking method
    if not daily_pnl:
        logging.info("No PnL data found, trying position tracking method...")
        return calculate_daily_pnl_position_tracking(trades_data)
    
    logging.info(f"Calculated comprehensive daily PnL: {dict(daily_pnl)}")
    return dict(daily_pnl)

def get_funding_fees(client: UMFutures, trade_dates: list) -> dict:
    """Fetch funding fees for the given dates"""
    daily_funding_fees = defaultdict(float)
    
    try:
        if not trade_dates:
            return dict(daily_funding_fees)
        
        # Convert date strings to timestamps
        date_list = sorted(trade_dates)
        start_date_str = date_list[0]
        end_date_str = date_list[-1]
        
        # Convert to timestamps (add 1 day to end date to include the full day)
        start_timestamp = int(datetime.strptime(start_date_str, '%Y-%m-%d').timestamp() * 1000)
        end_timestamp = int((datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)).timestamp() * 1000)
        
        logging.info(f"Fetching funding fees from {start_date_str} to {end_date_str}")
        
        # Get funding fee history
        funding_history = client.get_income_history(
            incomeType='FUNDING_FEE',
            startTime=start_timestamp,
            endTime=end_timestamp,
            limit=1000
        )
        
        for fee_record in funding_history:
            fee_timestamp = int(fee_record['time']) / 1000
            fee_date = datetime.utcfromtimestamp(fee_timestamp).strftime('%Y-%m-%d')
            fee_amount = float(fee_record['income'])
            
            daily_funding_fees[fee_date] += fee_amount
            logging.info(f"Funding fee on {fee_date}: {fee_amount:.4f} USDT for {fee_record['symbol']}")
        
        logging.info(f"Total funding fees by date: {dict(daily_funding_fees)}")
        
    except Exception as e:
        logging.warning(f"Could not fetch funding fees: {e}")
    
    return dict(daily_funding_fees)

def calculate_daily_pnl_position_tracking(trades_data: list) -> dict:
    """Alternative method: Calculate PnL using position tracking"""
    daily_pnl = defaultdict(float)
    
    # Group trades by symbol and process each symbol separately
    symbol_trades = defaultdict(list)
    for trade in trades_data:
        symbol_trades[trade['symbol']].append(trade)
    
    logging.info(f"Processing {len(symbol_trades)} symbols")
    
    for symbol, trades in symbol_trades.items():
        # Sort trades by time for proper position tracking
        trades.sort(key=lambda x: int(x['time']))
        
        # Simple approach: pair buy and sell trades
        buy_trades = []
        sell_trades = []
        
        for trade in trades:
            side = trade['side']
            qty = float(trade['qty'])
            price = float(trade['price'])
            trade_time = int(trade['time'])
            
            if side == 'BUY':
                buy_trades.append({'qty': qty, 'price': price, 'time': trade_time})
            else:  # SELL
                sell_trades.append({'qty': qty, 'price': price, 'time': trade_time})
        
        # Match buy and sell trades chronologically
        while buy_trades and sell_trades:
            buy_trade = buy_trades.pop(0)
            sell_trade = sell_trades.pop(0)
            
            # Calculate PnL for this pair
            buy_price = buy_trade['price']
            sell_price = sell_trade['price']
            
            # Use the later timestamp for the date
            close_time = max(buy_trade['time'], sell_trade['time'])
            trade_date = datetime.fromtimestamp(close_time / 1000).strftime('%Y-%m-%d')
            
            # Calculate PnL percentage
            pnl_percent = ((sell_price - buy_price) / buy_price) * 100
            daily_pnl[trade_date] += pnl_percent
            
            logging.info(f"Paired trade {symbol}: Buy: {buy_price:.4f}, Sell: {sell_price:.4f}, PnL: {pnl_percent:.2f}% on {trade_date}")
    
    logging.info(f"Position tracking result: {dict(daily_pnl)}")
    return dict(daily_pnl)

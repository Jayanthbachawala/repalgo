import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from core.brokers.factory import BrokerFactory

class MarketData:
    """
    Market data handler using custom broker integrations
    Supports: Zerodha, Upstox, AngelOne, Nubra, Dhan
    """
    
    def __init__(self, broker_name: str = None):
        self.broker = None
        self.broker_name = broker_name
        self.mock_mode = True  # Start in mock mode, switch when broker authenticated
        
        # Initialize broker if specified
        if broker_name:
            self.broker = BrokerFactory.create_broker(broker_name)
            if self.broker and self.broker.is_authenticated():
                self.mock_mode = False
        
        self.load_mock_data()
    
    def set_broker_instance(self, broker: 'BrokerInterface'):
        """Set an already authenticated broker instance"""
        if broker and broker.is_authenticated():
            self.broker = broker
            self.broker_name = broker.broker_name
            self.mock_mode = False
            return True
        return False
    
    def load_mock_data(self):
        """Load mock data for testing without API"""
        mock_data_path = "data/mock_data.json"
        if os.path.exists(mock_data_path):
            try:
                with open(mock_data_path, 'r') as f:
                    self.mock_data = json.load(f)
                
                if "stocks" not in self.mock_data:
                    self.create_mock_data()
            except:
                self.create_mock_data()
        else:
            self.create_mock_data()
    
    def create_mock_data(self):
        """Create realistic mock market data"""
        indices = ["NIFTY", "BANKNIFTY", "FINNIFTY", "SENSEX"]
        stocks = [
            "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR", "ICICIBANK", "SBIN", 
            "BHARTIARTL", "KOTAKBANK", "ITC", "AXISBANK", "LT", "TATAMOTORS", "WIPRO", 
            "ADANIENT", "ASIANPAINT", "BAJAJFINSV", "BAJFINANCE", "HCLTECH", "HEROMOTOCO",
            "MARUTI", "NESTLEIND", "ONGC", "POWERGRID", "SUNPHARMA", "TATASTEEL", "TECHM",
            "TITAN", "ULTRACEMCO", "UPL", "COALINDIA", "NTPC", "GRASIM", "JSWSTEEL",
            "INDUSINDBK", "DRREDDY", "EICHERMOT", "BAJAJ-AUTO", "DIVISLAB", "CIPLA",
            "M&M", "APOLLOHOSP", "BRITANNIA", "ADANIPORTS", "BPCL", "SHREECEM", "IOC",
            "HINDALCO", "VEDL", "GAIL", "TATACONSUM", "DABUR", "PIDILITIND", "BERGEPAINT",
            "COLPAL", "HAVELLS", "MARICO", "GODREJCP", "LUPIN", "BIOCON", "DMART",
            "BANDHANBNK", "TATAPOWER", "ADANIGREEN", "SIEMENS", "ABB", "BOSCHLTD",
            "MOTHERSON", "MPHASIS", "LTTS", "PERSISTENT", "COFORGE", "MINDTREE",
            "IRCTC", "ZOMATO", "NYKAA", "PAYTM", "POLICYBZR", "DELHIVERY"
        ]
        
        all_symbols = indices + stocks
        
        self.mock_data = {
            "indices": {},
            "stocks": {},
            "option_chain": {},
            "historical": {}
        }
        
        # Generate mock index data
        for symbol in indices:
            base_price = {
                "NIFTY": 19500,
                "BANKNIFTY": 45000,
                "FINNIFTY": 19800,
                "SENSEX": 65000
            }[symbol]
            
            self.mock_data["indices"][symbol] = {
                "ltp": base_price + np.random.normal(0, 100),
                "change": np.random.normal(0, 2),
                "change_percent": np.random.normal(0, 1),
                "volume": np.random.randint(1000000, 10000000),
                "oi": np.random.randint(50000, 500000)
            }
        
        # Generate mock stock data
        for symbol in stocks:
            base_price = {
                "RELIANCE": 2450, "TCS": 3600, "HDFCBANK": 1650, "INFY": 1450,
                "HINDUNILVR": 2650, "ICICIBANK": 980, "SBIN": 620, "BHARTIARTL": 890,
                "KOTAKBANK": 1780, "ITC": 450, "AXISBANK": 1050, "LT": 3400,
                "TATAMOTORS": 750, "WIPRO": 420, "ADANIENT": 2200
            }.get(symbol, 1000)
            
            self.mock_data["stocks"][symbol] = {
                "ltp": base_price + np.random.normal(0, 20),
                "change": np.random.normal(0, 15),
                "change_percent": np.random.normal(0, 1.5),
                "volume": np.random.randint(500000, 5000000),
                "oi": np.random.randint(100000, 2000000),
                "oi_change": np.random.randint(-50000, 50000),
                "delivery_pct": np.random.uniform(30, 80),
                "pe_ratio": np.random.uniform(15, 45),
                "market_cap": np.random.uniform(100000, 1500000)
            }
            
        # Generate option chain for all symbols
        for symbol in all_symbols:
            if symbol in indices:
                base_price = self.mock_data["indices"][symbol]["ltp"]
                strike_interval = 100
            else:
                base_price = self.mock_data["stocks"][symbol]["ltp"]
                strike_interval = 50 if base_price > 1000 else 25
            
            strikes = []
            atm_price = int(base_price / strike_interval) * strike_interval
            
            for i in range(-10, 11):
                strike = atm_price + (i * strike_interval)
            
                # CE options
                ce_data = {
                    "strike": strike,
                    "type": "CE",
                    "ltp": max(0.5, base_price - strike + np.random.normal(0, 50)),
                    "bid": 0,
                    "ask": 0,
                    "volume": np.random.randint(0, 100000),
                    "oi": np.random.randint(0, 500000),
                    "oi_change": np.random.randint(-10000, 10000),
                    "iv": np.random.uniform(15, 35),
                    "delta": max(0, min(1, 0.5 + (base_price - strike) / 1000)),
                    "gamma": np.random.uniform(0.0001, 0.01),
                    "theta": -np.random.uniform(1, 10),
                    "vega": np.random.uniform(5, 50)
                }
                
                ce_data["bid"] = max(0.05, ce_data["ltp"] - np.random.uniform(0.5, 2))
                ce_data["ask"] = ce_data["ltp"] + np.random.uniform(0.5, 2)
                
                # PE options
                pe_data = {
                    "strike": strike,
                    "type": "PE",
                    "ltp": max(0.5, strike - base_price + np.random.normal(0, 50)),
                    "bid": 0,
                    "ask": 0,
                    "volume": np.random.randint(0, 100000),
                    "oi": np.random.randint(0, 500000),
                    "oi_change": np.random.randint(-10000, 10000),
                    "iv": np.random.uniform(15, 35),
                    "delta": -max(0, min(1, 0.5 - (base_price - strike) / 1000)),
                    "gamma": np.random.uniform(0.0001, 0.01),
                    "theta": -np.random.uniform(1, 10),
                    "vega": np.random.uniform(5, 50)
                }
                
                pe_data["bid"] = max(0.05, pe_data["ltp"] - np.random.uniform(0.5, 2))
                pe_data["ask"] = pe_data["ltp"] + np.random.uniform(0.5, 2)
                
                strikes.extend([ce_data, pe_data])
            
            self.mock_data["option_chain"][symbol] = strikes
        
        # Generate historical data for all symbols
        for symbol in all_symbols:
            if symbol in indices:
                base_price = self.mock_data["indices"][symbol]["ltp"]
            else:
                base_price = self.mock_data["stocks"][symbol]["ltp"]
            
            timestamps = []
            prices = []
            volumes = []
            ois = []
            
            current_time = datetime.now()
            for i in range(100):
                timestamps.append(current_time - timedelta(minutes=i))
                prices.append(base_price + np.random.normal(0, 50) * np.sin(i/10))
                volumes.append(np.random.randint(1000, 10000))
                ois.append(np.random.randint(10000, 100000))
            
            self.mock_data["historical"][symbol] = {
                "timestamps": [ts.isoformat() for ts in reversed(timestamps)],
                "open": [p + np.random.normal(0, 5) for p in reversed(prices)],
                "high": [p + abs(np.random.normal(0, 20)) for p in reversed(prices)],
                "low": [p - abs(np.random.normal(0, 20)) for p in reversed(prices)],
                "close": list(reversed(prices)),
                "volume": list(reversed(volumes)),
                "oi": list(reversed(ois))
            }
    
    def get_live_price(self, symbol: str) -> Dict:
        """Get live price for a symbol using broker API or mock data"""
        data_source = "mock"
        
        # Try broker first if connected
        if not self.mock_mode and self.broker and self.broker.is_authenticated():
            try:
                # Determine exchange based on symbol
                exchange = "NSE" if symbol in self.get_available_symbols("stocks") else "NSE"
                
                quotes = self.broker.get_live_quotes([{"symbol": symbol, "exchange": exchange}])
                
                if quotes and symbol in quotes:
                    result = quotes[symbol]
                    result['data_source'] = 'live'
                    return result
                else:
                    # Broker doesn't support live quotes yet
                    data_source = "broker_unsupported"
            except Exception as e:
                print(f"Broker quote error: {e}")
                data_source = "broker_error"
        
        # Use mock data with clear indicator
        if symbol in self.mock_data["indices"]:
            result = self.mock_data["indices"][symbol].copy()
        elif symbol in self.mock_data["stocks"]:
            result = self.mock_data["stocks"][symbol].copy()
        else:
            # Generate realistic mock data for unknown symbols
            import random
            base_price = random.randint(100, 25000)
            change = random.uniform(-5, 5)
            result = {
                "ltp": base_price,
                "change": base_price * (change/100),
                "change_percent": change,
                "volume": random.randint(10000, 10000000),
                "oi": random.randint(1000, 500000)
            }
        
        result['data_source'] = data_source
        return result
    
    def get_option_chain(self, symbol: str, expiry: str) -> pd.DataFrame:
        """Get option chain data for a symbol and expiry"""
        # Use broker API if available and supports live data
        if not self.mock_mode and self.broker and self.broker.is_authenticated():
            # Check if broker supports live quotes
            test_quote = self.get_live_price(symbol)
            if test_quote.get('data_source') == 'live':
                try:
                    df = self.broker.get_option_chain(symbol, expiry)
                    if not df.empty:
                        return df
                except Exception as e:
                    print(f"Option chain error: {e}")
        
        # Fall back to mock data
        if symbol in self.mock_data["option_chain"]:
            data = self.mock_data["option_chain"][symbol]
            df = pd.DataFrame(data)
            return df
        else:
            return pd.DataFrame()
    
    def get_historical_data(self, symbol: str, interval: str = "5m", 
                          days: int = 7, exchange: str = "NSE") -> pd.DataFrame:
        """
        Get historical OHLC data using broker API
        
        Args:
            symbol: Symbol name
            interval: '1m', '5m', '15m', '1h', '1d'
            days: Number of days of history
            exchange: Exchange name (NSE, NFO, BSE, etc.)
        """
        # Use broker API if available and supports live data
        if not self.mock_mode and self.broker and self.broker.is_authenticated():
            # Check if broker supports live quotes
            test_quote = self.get_live_price(symbol)
            if test_quote.get('data_source') == 'live':
                try:
                    to_date = datetime.now().strftime("%Y-%m-%d")
                    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
                    
                    df = self.broker.get_historical_data(symbol, from_date, to_date, interval, exchange)
                    if not df.empty:
                        return df
                except Exception as e:
                    print(f"Historical data error: {e}")
        
        # Fall back to mock data
        if symbol in self.mock_data["historical"]:
            data = self.mock_data["historical"][symbol]
            df = pd.DataFrame(data)
            # Ensure timestamp column exists
            if 'timestamp' not in df.columns and 'date' in df.columns:
                df['timestamp'] = df['date']
            elif 'timestamp' not in df.columns:
                # Generate timestamps for mock data
                df['timestamp'] = pd.date_range(end=pd.Timestamp.now(), periods=len(df), freq='1D')
            return df
        # Return empty DataFrame with proper columns
        return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    def get_expiry_dates(self, symbol: str) -> List[str]:
        """Get available expiry dates for a symbol"""
        if self.mock_mode:
            # Generate mock expiry dates
            today = datetime.now()
            expiries = []
            
            # Weekly expiries for next 4 weeks
            for i in range(4):
                # Find next Thursday
                days_ahead = 3 - today.weekday()  # Thursday is 3
                if days_ahead <= 0:
                    days_ahead += 7
                expiry_date = today + timedelta(days=days_ahead + (i * 7))
                expiries.append(expiry_date.strftime("%Y-%m-%d"))
            
            return expiries
        
        # Broker API would return expiries
        return []
    
    def get_chart_data(self, symbol: str, timeframe: str = "5minute") -> Dict:
        """Get historical chart data"""
        if self.mock_mode:
            if symbol in self.mock_data["historical"]:
                data = self.mock_data["historical"][symbol]
                return {
                    "timestamp": [datetime.fromisoformat(ts) for ts in data["timestamps"]],
                    "open": data["open"],
                    "high": data["high"],
                    "low": data["low"],
                    "close": data["close"],
                    "volume": data["volume"],
                    "oi": data["oi"]
                }
            else:
                # Return empty structure with proper keys
                now = datetime.now()
                return {
                    "timestamp": [now - timedelta(minutes=i*5) for i in range(20, 0, -1)],
                    "open": [0] * 20,
                    "high": [0] * 20,
                    "low": [0] * 20,
                    "close": [0] * 20,
                    "volume": [0] * 20,
                    "oi": [0] * 20
                }
        
        # Use get_historical_data for real data
        interval_map = {
            "1minute": "1m",
            "5minute": "5m",
            "15minute": "15m",
            "1hour": "1h",
            "1day": "1d"
        }
        
        interval = interval_map.get(timeframe, "5m")
        df = self.get_historical_data(symbol, interval=interval, days=7)
        
        if not df.empty:
            return {
                "timestamp": df['timestamp'].tolist(),
                "open": df['open'].tolist(),
                "high": df['high'].tolist(),
                "low": df['low'].tolist(),
                "close": df['close'].tolist(),
                "volume": df['volume'].tolist(),
                "oi": df.get('oi', [0] * len(df)).tolist()
            }
        
        # Return empty structure with proper keys when no data available
        now = datetime.now()
        return {
            "timestamp": [now - timedelta(minutes=i*5) for i in range(20, 0, -1)],
            "open": [0] * 20,
            "high": [0] * 20,
            "low": [0] * 20,
            "close": [0] * 20,
            "volume": [0] * 20,
            "oi": [0] * 20
        }
    
    def get_top_gainers_losers(self) -> Dict[str, List]:
        """Get top gainers and losers"""
        if self.mock_mode:
            # Generate mock top gainers/losers
            symbols = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR", 
                      "ICICIBANK", "SBIN", "BHARTIARTL", "KOTAKBANK", "ITC"]
            
            gainers = []
            losers = []
            
            for symbol in symbols[:5]:
                change = np.random.uniform(2, 8)
                gainers.append((symbol, change))
            
            for symbol in symbols[5:]:
                change = np.random.uniform(-8, -2)
                losers.append((symbol, change))
            
            return {
                "gainers": sorted(gainers, key=lambda x: x[1], reverse=True),
                "losers": sorted(losers, key=lambda x: x[1])
            }
        
        # Broker API would return top movers
        return {"gainers": [], "losers": []}
    
    def get_available_symbols(self, symbol_type: str = "all") -> List[str]:
        """Get list of available symbols"""
        # All major indices
        indices = [
            "NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX",
            "BANKEX", "NIFTYIT", "NIFTYPHARMA", "NIFTYAUTO", "NIFTYMETAL"
        ]
        
        # Comprehensive NSE stock list (Top 200+ stocks)
        stocks = [
            # Nifty 50 stocks
            "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR", "ITC", "SBIN", 
            "BHARTIARTL", "KOTAKBANK", "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "SUNPHARMA",
            "TITAN", "ULTRACEMCO", "BAJFINANCE", "NESTLEIND", "WIPRO", "HCLTECH", "TATAMOTORS",
            "ONGC", "NTPC", "POWERGRID", "M&M", "ADANIENT", "JSWSTEEL", "TATASTEEL", "INDUSINDBK",
            "BAJAJFINSV", "COALINDIA", "DRREDDY", "GRASIM", "HINDALCO", "TECHM", "CIPLA", "APOLLOHOSP",
            "EICHERMOT", "BRITANNIA", "DIVISLAB", "ADANIPORTS", "TATACONSUM", "BPCL", "UPL", "HEROMOTOCO",
            "SBILIFE", "BAJAJ-AUTO", "HDFCLIFE", "LTIM",
            
            # Nifty Next 50
            "ACC", "ADANIGREEN", "ADANITRANS", "AMBUJACEM", "BANDHANBNK", "BERGEPAINT", "BIOCON",
            "BOSCHLTD", "COLPAL", "DABUR", "DLF", "GAIL", "GODREJCP", "HAVELLS", "HINDPETRO",
            "ICICIPRULI", "INDIGO", "JINDALSTEL", "MCDOWELL-N", "NAUKRI", "NMDC", "PAGEIND",
            "PETRONET", "PGHH", "PIDILITIND", "PNB", "SIEMENS", "TATAPOWER", "TORNTPHARM", "TRENT",
            "VEDL", "VOLTAS", "ZOMATO", "ABB", "ALKEM", "AUROPHARMA", "BAJAJHLDNG", "BEL",
            
            # Additional popular stocks
            "PAYTM", "POLICYBZR", "DMART", "IRCTC", "SRF", "MOTHERSON", "CROMPTON", "DIXON",
            "MAXHEALTH", "LICI", "JUBLFOOD", "PVR", "CANBK", "FEDERALBNK", "IDFCFIRSTB", "AUBANK",
            "RBLBANK", "YESBANK", "M&MFIN", "SHRIRAMFIN", "CHOLAFIN", "PFC", "RECLTD", "IRFC",
            "SUZLON", "ADANIPOWER", "TATAPOWER", "NHPC", "SJVN", "SAIL", "NMDC", "MOIL",
            
            # IT & Tech
            "PERSISTENT", "COFORGE", "MPHASIS", "LTTS", "TECHM", "MINDTREE", "CYIENT", "KPITTECH",
            
            # Pharma
            "LUPIN", "BIOCON", "GRANULES", "LALPATHLAB", "METROPOLIS", "THYROCARE",
            
            # Auto & Auto Ancillary
            "TVSMOTOR", "BAJAJ-AUTO", "HEROMOTOCO", "ASHOKLEY", "ESCORTS", "EXIDEIND", "MRF",
            "APOLLOTYRE", "CEAT", "BALKRISIND", "MOTHERSON", "BOSCHLTD", "ENDURANCE",
            
            # Banks & Financial Services
            "BANKBARODA", "UNIONBANK", "IOB", "INDIANB", "CENTRALBK", "MAHABANK", "IIFL", "ICICIGI",
            "SBICARD", "HDFCAMC", "MUTHOOTFIN", "MANAPPURAM", "LICHSGFIN",
            
            # FMCG & Consumer
            "MARICO", "GODREJCP", "VBL", "VARUN", "TATACONSUM", "PGHH", "COLPAL", "RADICO",
            
            # Metals & Mining
            "HINDZINC", "NATIONALUM", "VEDL", "COALINDIA", "NMDC", "SAIL", "JINDALSTEL", "JSWSTEEL",
            
            # Cement
            "ULTRACEMCO", "AMBUJACEM", "ACC", "SHREECEM", "RAMCOCEM", "JKCEMENT", "HEIDELBERG",
            
            # Telecom & Media
            "BHARTIARTL", "IDEA", "ZEEL", "SUNTV", "DISHTV", "NETWORK18",
            
            # Retail & E-commerce  
            "TRENT", "SHOPERSTOP", "VMART", "NYKAA", "POLICYBZR",
            
            # Real Estate
            "DLF", "GODREJPROP", "OBEROIRLTY", "BRIGADE", "PRESTIGE", "PHOENIXLTD",
            
            # Infrastructure & Construction
            "LT", "LARTOUROB", "NCC", "NBCC", "IRBINVIT", "IRB", "GMRINFRA"
        ]
        
        # Remove duplicates and sort
        stocks = sorted(list(set(stocks)))
        
        if symbol_type == "indices":
            return indices
        elif symbol_type == "stocks":
            return stocks
        else:
            return indices + stocks
    
    def get_stock_fundamentals(self, symbol: str) -> Dict:
        """Get stock fundamentals like P/E, Market Cap, etc."""
        if symbol in self.mock_data.get("stocks", {}):
            stock_data = self.mock_data["stocks"][symbol]
            return {
                'pe_ratio': stock_data.get('pe_ratio', 0),
                'market_cap': stock_data.get('market_cap', 0),
                'delivery_pct': stock_data.get('delivery_pct', 0)
            }
        return {'pe_ratio': 0, 'market_cap': 0, 'delivery_pct': 0}
    
    def calculate_max_pain(self, option_chain: pd.DataFrame) -> float:
        """Calculate max pain point from option chain"""
        if option_chain.empty:
            return 0
        
        strikes = option_chain['strike'].unique()
        max_pain = 0
        min_pain_value = float('inf')
        
        for strike in strikes:
            pain = 0
            
            # Calculate pain for CE holders
            ce_options = option_chain[(option_chain['type'] == 'CE') & (option_chain['strike'] < strike)]
            for _, opt in ce_options.iterrows():
                pain += (strike - opt['strike']) * opt['oi']
            
            # Calculate pain for PE holders
            pe_options = option_chain[(option_chain['type'] == 'PE') & (option_chain['strike'] > strike)]
            for _, opt in pe_options.iterrows():
                pain += (opt['strike'] - strike) * opt['oi']
            
            if pain < min_pain_value:
                min_pain_value = pain
                max_pain = strike
        
        return max_pain
    
    def get_broker_status(self) -> Dict:
        """Get current broker connection status"""
        if self.broker and self.broker.is_authenticated():
            return {
                "connected": True,
                "broker": self.broker_name,
                "mode": "Live"
            }
        return {
            "connected": False,
            "broker": None,
            "mode": "Mock"
        }

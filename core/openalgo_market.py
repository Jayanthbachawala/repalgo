import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from core.openalgo_auth import OpenAlgoAuth

class OpenAlgoMarketData:
    def __init__(self, openalgo_auth: OpenAlgoAuth):
        self.auth = openalgo_auth
        
    def get_live_price(self, symbol: str, exchange: str = "NFO") -> Dict:
        if not self.auth.is_connected():
            return {"error": "Not connected to OpenAlgo"}
        
        result = self.auth.get_quotes(symbol, exchange)
        
        if result['success']:
            quote_data = result['data']
            return {
                'ltp': quote_data.get('lp', 0),
                'change': quote_data.get('change', 0),
                'change_percent': quote_data.get('change_percent', 0),
                'volume': quote_data.get('volume', 0),
                'oi': quote_data.get('oi', 0),
                'high': quote_data.get('high', 0),
                'low': quote_data.get('low', 0),
                'open': quote_data.get('open', 0),
                'close': quote_data.get('close', 0)
            }
        else:
            return {"error": result.get('message', 'Failed to fetch price')}
    
    def get_option_chain_live(self, symbol: str, expiry: str = None) -> pd.DataFrame:
        if not self.auth.is_connected():
            return pd.DataFrame()
        
        option_data = []
        
        if symbol == "NIFTY":
            base_symbol = "NIFTY"
            base_price = 19500
            step = 50
        elif symbol == "BANKNIFTY":
            base_symbol = "BANKNIFTY"
            base_price = 45000
            step = 100
        elif symbol == "FINNIFTY":
            base_symbol = "FINNIFTY"
            base_price = 19700
            step = 50
        else:
            return pd.DataFrame()
        
        if not expiry:
            expiry = self._get_next_expiry()
        
        for i in range(-5, 6):
            strike = base_price + (i * step)
            
            ce_symbol = f"{base_symbol}{expiry}{strike}CE"
            pe_symbol = f"{base_symbol}{expiry}{strike}PE"
            
            ce_quote = self.auth.get_quotes(ce_symbol, "NFO")
            pe_quote = self.auth.get_quotes(pe_symbol, "NFO")
            
            if ce_quote['success']:
                ce_data = ce_quote['data']
                option_data.append({
                    'strike': strike,
                    'type': 'CE',
                    'ltp': ce_data.get('lp', 0),
                    'bid': ce_data.get('bid', 0),
                    'ask': ce_data.get('ask', 0),
                    'volume': ce_data.get('volume', 0),
                    'oi': ce_data.get('oi', 0),
                    'oi_change': ce_data.get('oi_change', 0),
                    'iv': ce_data.get('iv', 20),
                    'delta': 0.5,
                    'gamma': 0.005,
                    'theta': -5,
                    'vega': 20
                })
            
            if pe_quote['success']:
                pe_data = pe_quote['data']
                option_data.append({
                    'strike': strike,
                    'type': 'PE',
                    'ltp': pe_data.get('lp', 0),
                    'bid': pe_data.get('bid', 0),
                    'ask': pe_data.get('ask', 0),
                    'volume': pe_data.get('volume', 0),
                    'oi': pe_data.get('oi', 0),
                    'oi_change': pe_data.get('oi_change', 0),
                    'iv': pe_data.get('iv', 20),
                    'delta': -0.5,
                    'gamma': 0.005,
                    'theta': -5,
                    'vega': 20
                })
        
        return pd.DataFrame(option_data) if option_data else pd.DataFrame()
    
    def _get_next_expiry(self) -> str:
        today = datetime.now()
        days_ahead = 3 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        
        next_thursday = today + timedelta(days=days_ahead)
        return next_thursday.strftime("%d%b").upper()
    
    def get_market_depth(self, symbol: str, exchange: str = "NFO") -> Dict:
        if not self.auth.is_connected():
            return {}
        
        result = self.auth.get_depth(symbol, exchange)
        
        if result['success']:
            depth_data = result['data']
            return {
                'bids': depth_data.get('bids', []),
                'asks': depth_data.get('asks', []),
                'total_bid_qty': sum(bid.get('quantity', 0) for bid in depth_data.get('bids', [])),
                'total_ask_qty': sum(ask.get('quantity', 0) for ask in depth_data.get('asks', []))
            }
        else:
            return {}
    
    def get_positions_from_broker(self) -> List[Dict]:
        if not self.auth.is_connected():
            return []
        
        result = self.auth.get_positions()
        
        if result['success']:
            positions_data = result['data']
            positions = []
            
            for pos in positions_data.get('positions', []):
                positions.append({
                    'symbol': pos.get('symbol', ''),
                    'quantity': pos.get('netqty', 0),
                    'average_price': pos.get('netavgprice', 0),
                    'ltp': pos.get('ltp', 0),
                    'pnl': pos.get('pnl', 0),
                    'product': pos.get('product', ''),
                    'exchange': pos.get('exchange', '')
                })
            
            return positions
        else:
            return []
    
    def place_option_order(self, order_params: Dict) -> Dict:
        if not self.auth.is_connected():
            return {
                'success': False,
                'message': 'Not connected to OpenAlgo'
            }
        
        openalgo_order = {
            'apikey': self.auth.api_key,
            'strategy': order_params.get('strategy', 'AI_TRADER'),
            'symbol': order_params.get('symbol'),
            'action': order_params.get('action', 'BUY'),
            'exchange': order_params.get('exchange', 'NFO'),
            'pricetype': order_params.get('price_type', 'MARKET'),
            'product': order_params.get('product', 'MIS'),
            'quantity': str(order_params.get('quantity', 1)),
            'position_size': str(order_params.get('quantity', 1))
        }
        
        if order_params.get('price_type') == 'LIMIT':
            openalgo_order['price'] = str(order_params.get('price', 0))
        
        result = self.auth.place_order(openalgo_order)
        
        return result
    
    def get_historical_ohlc(self, symbol: str, exchange: str = "NSE", 
                            interval: str = "1d", days: int = 30) -> pd.DataFrame:
        """
        Get historical OHLC data for charts
        
        Args:
            symbol: Trading symbol
            exchange: Exchange (NSE, NFO, BSE, etc.)
            interval: Time interval (1m, 5m, 15m, 30m, 1h, 1d)
            days: Number of days of history
        
        Returns:
            DataFrame with OHLC, volume, OI data
        """
        if not self.auth.is_connected():
            return pd.DataFrame()
        
        from datetime import datetime, timedelta
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        result = self.auth.get_historical_data(symbol, exchange, interval, start_date, end_date)
        
        if result['success']:
            data = result['data']
            
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data)
                
                if 'timestamp' in df.columns or 'date' in df.columns:
                    time_col = 'timestamp' if 'timestamp' in df.columns else 'date'
                    df[time_col] = pd.to_datetime(df[time_col])
                    df = df.sort_values(time_col)
                
                return df
        
        return pd.DataFrame()
    
    def get_supported_brokers(self) -> List[str]:
        """
        Get list of all supported brokers via OpenAlgo
        """
        return [
            "Zerodha", "AngelOne", "Upstox", "Fyers", "Dhan", 
            "Flattrade", "Shoonya", "AliceBlue", "5Paisa", "IIFL", 
            "Kotak Securities", "Paytm", "Groww", "Firstock", 
            "Motilal Oswal", "Tradejini", "IndMoney", "Zebu", 
            "Wisdom", "Pocketful", "Definedge", "Compositedge", 
            "Ibulls", "Fivepaisaxts", "Dhan Sandbox"
        ]

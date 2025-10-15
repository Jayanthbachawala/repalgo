import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .base import BrokerInterface

class UpstoxBroker(BrokerInterface):
    """
    Upstox API v2 Integration
    Docs: https://upstox.com/developer/api-documentation/
    """
    
    def __init__(self):
        super().__init__()
        self.broker_name = "Upstox"
        self.base_url = "https://api.upstox.com/v2"
        self.api_key = None
        self.api_secret = None
        self.session = requests.Session()
    
    def authenticate(self, credentials: Dict) -> Dict:
        """
        Step 1: Generate authorization URL
        
        Args:
            credentials: {'api_key': '...', 'api_secret': '...', 'redirect_uri': '...'}
        
        Returns:
            Dict with authorization URL
        """
        self.api_key = credentials.get('api_key')
        self.api_secret = credentials.get('api_secret')
        redirect_uri = credentials.get('redirect_uri', 'http://127.0.0.1:8000')
        
        if not self.api_key:
            return {
                'success': False,
                'message': 'API key is required'
            }
        
        auth_url = (
            f"{self.base_url}/login/authorization/dialog?"
            f"response_type=code&client_id={self.api_key}&redirect_uri={redirect_uri}"
        )
        
        return {
            'success': True,
            'message': 'Redirect user to authorization URL',
            'auth_url': auth_url,
            'next_step': 'Exchange authorization code for access_token'
        }
    
    def get_access_token(self, auth_code: str, credentials: Dict) -> Dict:
        """
        Step 2: Exchange authorization code for access token
        
        Args:
            auth_code: Authorization code from OAuth callback
            credentials: {'api_key': '...', 'api_secret': '...', 'redirect_uri': '...'}
        
        Returns:
            Dict with access token
        """
        self.api_key = credentials.get('api_key')
        self.api_secret = credentials.get('api_secret')
        redirect_uri = credentials.get('redirect_uri', 'http://127.0.0.1:8000')
        
        if not all([self.api_key, self.api_secret, auth_code]):
            return {
                'success': False,
                'message': 'API key, secret, and authorization code required'
            }
        
        try:
            response = self.session.post(
                f"{self.base_url}/login/authorization/token",
                headers={
                    'accept': 'application/json',
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                data={
                    'code': auth_code,
                    'client_id': self.api_key,
                    'client_secret': self.api_secret,
                    'redirect_uri': redirect_uri,
                    'grant_type': 'authorization_code'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data['access_token']
                self.authenticated = True
                
                return {
                    'success': True,
                    'message': 'Authentication successful',
                    'access_token': self.access_token,
                    'token_type': data.get('token_type'),
                    'expires_in': data.get('expires_in')
                }
            else:
                return {
                    'success': False,
                    'message': f'Authentication failed: {response.text}'
                }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    def _get_headers(self) -> Dict:
        """Get auth headers for API requests"""
        headers = {
            'Accept': 'application/json'
        }
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        return headers
    
    def get_historical_data(self, symbol: str, exchange: str, 
                          interval: str, from_date: str, to_date: str) -> pd.DataFrame:
        """
        Get historical OHLC data from Upstox (NO AUTH REQUIRED - Public API)
        
        Supported Intervals: 1minute, 30minute, day, week, month
        Note: 1h not supported by Upstox - use 30m or 1d instead
        """
        try:
            instrument_key = self._get_instrument_key(symbol, exchange)
            
            if not instrument_key:
                print(f"Upstox: Could not resolve instrument key for {symbol} on {exchange}")
                return pd.DataFrame()
            
            interval_map = {
                '1m': '1minute', 
                '30m': '30minute',
                '1d': 'day', 
                '1w': 'week', 
                '1M': 'month'
            }
            
            if interval == '1h':
                print(f"Upstox: 1h interval not supported. Use '30m' or '1d' instead.")
                return pd.DataFrame()
            
            upstox_interval = interval_map.get(interval, 'day')
            
            url = (
                f"{self.base_url}/historical-candle/"
                f"{instrument_key}/{upstox_interval}/{to_date}/{from_date}"
            )
            
            response = self.session.get(
                url,
                headers={'Accept': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                candles = data['data']['candles']
                
                df = pd.DataFrame(candles, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi'
                ])
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                return df
            else:
                return pd.DataFrame()
        
        except Exception as e:
            print(f"Upstox historical data error: {e}")
            return pd.DataFrame()
    
    def _get_instrument_key(self, symbol: str, exchange: str) -> Optional[str]:
        """
        Get proper instrument key for Upstox
        
        Format: {EXCHANGE}_{SEGMENT}|{SYMBOL_TOKEN or SYMBOL}
        
        Segments:
        - NSE_EQ: NSE stocks
        - NSE_INDEX: Indices (NIFTY, BANKNIFTY)
        - NFO_OPT: NFO options
        - NFO_FUT: NFO futures
        - BSE_EQ: BSE stocks
        """
        exchange = exchange.upper()
        symbol = symbol.upper()
        
        if exchange == "NSE":
            if symbol in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]:
                return f"NSE_INDEX|{symbol}"
            else:
                return f"NSE_EQ|{symbol}"
        
        elif exchange == "NFO":
            if "CE" in symbol or "PE" in symbol:
                return f"NFO_OPT|{symbol}"
            elif "FUT" in symbol:
                return f"NFO_FUT|{symbol}"
            else:
                return f"NFO_FUT|{symbol}"
        
        elif exchange == "BSE":
            return f"BSE_EQ|{symbol}"
        
        else:
            return f"{exchange}_EQ|{symbol}"
    
    def get_live_quotes(self, symbols: List[Dict]) -> Dict:
        """Get live quotes from Upstox"""
        if not self.is_authenticated():
            return {}
        
        try:
            instrument_keys = [
                self._get_instrument_key(s['symbol'], s['exchange']) for s in symbols
            ]
            instrument_keys = [k for k in instrument_keys if k]
            
            response = self.session.get(
                f"{self.base_url}/market-quote/quotes",
                params={'instrument_key': ','.join(instrument_keys)},
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()['data']
            else:
                return {}
        
        except Exception as e:
            print(f"Upstox quote error: {e}")
            return {}
    
    def get_option_chain(self, symbol: str, expiry: str = None) -> pd.DataFrame:
        """
        Get option chain from Upstox
        Phase 2 feature - returning empty DataFrame for MVP
        """
        return pd.DataFrame()
    
    def place_order(self, order_params: Dict) -> Dict:
        """Place order on Upstox"""
        if not self.is_authenticated():
            return {'success': False, 'message': 'Not authenticated'}
        
        try:
            response = self.session.post(
                f"{self.base_url}/order/place",
                json=order_params,
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'message': response.text
                }
        
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    def get_positions(self) -> List[Dict]:
        """Get current positions"""
        if not self.is_authenticated():
            return []
        
        try:
            response = self.session.get(
                f"{self.base_url}/portfolio/short-term-positions",
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()['data']
                return data
            else:
                return []
        
        except Exception as e:
            print(f"Upstox positions error: {e}")
            return []
    
    def get_funds(self) -> Dict:
        """Get account funds"""
        if not self.is_authenticated():
            return {}
        
        try:
            response = self.session.get(
                f"{self.base_url}/user/get-funds-and-margin",
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()['data']
            else:
                return {}
        
        except Exception as e:
            print(f"Upstox funds error: {e}")
            return {}
    
    def cancel_order(self, order_id: str) -> Dict:
        """Cancel order"""
        if not self.is_authenticated():
            return {'success': False, 'message': 'Not authenticated'}
        
        try:
            response = self.session.delete(
                f"{self.base_url}/order/cancel",
                params={'order_id': order_id},
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'message': response.text
                }
        
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }

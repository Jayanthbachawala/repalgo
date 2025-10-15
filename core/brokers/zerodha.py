import requests
import hashlib
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .base import BrokerInterface

class ZerodhaBroker(BrokerInterface):
    """
    Zerodha Kite Connect API Integration
    Docs: https://kite.trade/docs/connect/v3/
    """
    
    def __init__(self):
        super().__init__()
        self.broker_name = "Zerodha"
        self.base_url = "https://api.kite.trade"
        self.login_url = "https://kite.zerodha.com/connect/login"
        self.api_key = None
        self.api_secret = None
        self.session = requests.Session()
    
    def authenticate(self, credentials: Dict) -> Dict:
        """
        Step 1: Generate login URL for user authentication
        
        Args:
            credentials: {'api_key': '...', 'api_secret': '...', 'redirect_uri': '...'}
        
        Returns:
            Dict with login URL
        """
        self.api_key = credentials.get('api_key')
        self.api_secret = credentials.get('api_secret')
        
        if not self.api_key:
            return {
                'success': False,
                'message': 'API key is required'
            }
        
        login_url = f"{self.login_url}?v=3&api_key={self.api_key}"
        
        return {
            'success': True,
            'message': 'Redirect user to login URL',
            'login_url': login_url,
            'next_step': 'Exchange request_token for access_token after callback'
        }
    
    def get_access_token(self, request_token: str, credentials: Dict) -> Dict:
        """
        Step 2: Exchange request token for access token
        
        Args:
            request_token: Token from OAuth callback
            credentials: {'api_key': '...', 'api_secret': '...'}
        
        Returns:
            Dict with access token
        """
        self.api_key = credentials.get('api_key')
        self.api_secret = credentials.get('api_secret')
        
        if not all([self.api_key, self.api_secret, request_token]):
            return {
                'success': False,
                'message': 'API key, secret, and request token required'
            }
        
        checksum = hashlib.sha256(
            f"{self.api_key}{request_token}{self.api_secret}".encode()
        ).hexdigest()
        
        try:
            response = self.session.post(
                f"{self.base_url}/session/token",
                data={
                    'api_key': self.api_key,
                    'request_token': request_token,
                    'checksum': checksum
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data['data']['access_token']
                self.authenticated = True
                
                return {
                    'success': True,
                    'message': 'Authentication successful',
                    'access_token': self.access_token,
                    'user_data': data['data']
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
        if not self.access_token or not self.api_key:
            return {}
        return {
            'Authorization': f'token {self.api_key}:{self.access_token}',
            'X-Kite-Version': '3'
        }
    
    def get_historical_data(self, symbol: str, exchange: str, 
                          interval: str, from_date: str, to_date: str) -> pd.DataFrame:
        """
        Get historical OHLC data from Zerodha
        
        Intervals: minute, 3minute, 5minute, 10minute, 15minute, 30minute, 60minute, day
        """
        if not self.is_authenticated():
            return pd.DataFrame()
        
        try:
            instrument_token = self._get_instrument_token(symbol, exchange)
            
            if not instrument_token:
                return pd.DataFrame()
            
            interval_map = {
                '1m': 'minute', '3m': '3minute', '5m': '5minute',
                '10m': '10minute', '15m': '15minute', '30m': '30minute',
                '1h': '60minute', '1d': 'day'
            }
            kite_interval = interval_map.get(interval, interval)
            
            response = self.session.get(
                f"{self.base_url}/instruments/historical/{instrument_token}/{kite_interval}",
                params={
                    'from': from_date,
                    'to': to_date
                },
                headers=self._get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                candles = data['data']['candles']
                
                df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi'])
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                return df
            else:
                return pd.DataFrame()
        
        except Exception as e:
            print(f"Zerodha historical data error: {e}")
            return pd.DataFrame()
    
    def _get_instrument_token(self, symbol: str, exchange: str) -> Optional[str]:
        """
        Get instrument token for symbol
        For MVP: Using symbol lookup via search API
        TODO: Cache instrument master CSV for better performance
        """
        if not self.is_authenticated():
            return None
        
        try:
            response = self.session.get(
                f"{self.base_url}/instruments",
                params={'exchange': exchange},
                headers=self._get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                instruments = response.text.split('\n')
                for line in instruments[1:]:
                    parts = line.split(',')
                    if len(parts) > 2 and parts[2].strip() == symbol:
                        return parts[0]
            
            return f"{exchange}:{symbol}"
        
        except Exception as e:
            print(f"Zerodha instrument token error: {e}")
            return f"{exchange}:{symbol}"
    
    def get_live_quotes(self, symbols: List[Dict]) -> Dict:
        """Get live quotes from Zerodha"""
        if not self.is_authenticated():
            return {}
        
        try:
            instruments = [f"{s['exchange']}:{s['symbol']}" for s in symbols]
            
            response = self.session.get(
                f"{self.base_url}/quote",
                params={'i': instruments},
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()['data']
            else:
                return {}
        
        except Exception as e:
            print(f"Zerodha quote error: {e}")
            return {}
    
    def get_option_chain(self, symbol: str, expiry: str = None) -> pd.DataFrame:
        """
        Get option chain from Zerodha
        Note: Requires instrument master for full implementation
        Phase 2 feature - returning empty DataFrame for MVP
        """
        return pd.DataFrame()
    
    def place_order(self, order_params: Dict) -> Dict:
        """Place order on Zerodha"""
        if not self.is_authenticated():
            return {'success': False, 'message': 'Not authenticated'}
        
        try:
            response = self.session.post(
                f"{self.base_url}/orders/regular",
                data=order_params,
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
                f"{self.base_url}/portfolio/positions",
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()['data']
                return data.get('net', [])
            else:
                return []
        
        except Exception as e:
            print(f"Zerodha positions error: {e}")
            return []
    
    def get_funds(self) -> Dict:
        """Get account funds"""
        if not self.is_authenticated():
            return {}
        
        try:
            response = self.session.get(
                f"{self.base_url}/user/margins",
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()['data']
            else:
                return {}
        
        except Exception as e:
            print(f"Zerodha funds error: {e}")
            return {}
    
    def cancel_order(self, order_id: str) -> Dict:
        """Cancel order"""
        if not self.is_authenticated():
            return {'success': False, 'message': 'Not authenticated'}
        
        try:
            response = self.session.delete(
                f"{self.base_url}/orders/regular/{order_id}",
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

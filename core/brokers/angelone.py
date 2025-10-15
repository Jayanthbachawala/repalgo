import requests
import pandas as pd
import pyotp
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .base import BrokerInterface

class AngelOneBroker(BrokerInterface):
    """
    AngelOne SmartAPI Integration
    Docs: https://smartapi.angelbroking.com/docs
    Uses TOTP-based authentication (no OAuth)
    """
    
    def __init__(self):
        super().__init__()
        self.broker_name = "AngelOne"
        self.base_url = "https://apiconnect.angelone.in"
        self.api_key = None
        self.client_code = None
        self.pin = None
        self.totp_token = None
        self.session = requests.Session()
        self.feed_token = None
    
    def authenticate(self, credentials: Dict) -> Dict:
        """
        Authenticate with AngelOne using TOTP
        
        Args:
            credentials: {
                'api_key': '...',
                'client_code': '...',
                'pin': '...',
                'totp_token': '...'  # QR code value from enable-totp
            }
        
        Returns:
            Dict with auth status and tokens
        """
        self.api_key = credentials.get('api_key')
        self.client_code = credentials.get('client_code')
        self.pin = credentials.get('pin')
        self.totp_token = credentials.get('totp_token')
        
        if not all([self.api_key, self.client_code, self.pin, self.totp_token]):
            return {
                'success': False,
                'message': 'API key, client code, PIN, and TOTP token required'
            }
        
        try:
            totp = pyotp.TOTP(self.totp_token).now()
            
            response = self.session.post(
                f"{self.base_url}/rest/auth/angelbroking/user/v1/loginByPassword",
                json={
                    'clientcode': self.client_code,
                    'password': self.pin,
                    'totp': totp
                },
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-UserType': 'USER',
                    'X-SourceID': 'WEB',
                    'X-ClientLocalIP': '127.0.0.1',
                    'X-ClientPublicIP': '127.0.0.1',
                    'X-MACAddress': '00:00:00:00:00:00',
                    'X-PrivateKey': self.api_key
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status'):
                    self.access_token = data['data']['jwtToken']
                    self.feed_token = data['data']['feedToken']
                    self.authenticated = True
                    
                    return {
                        'success': True,
                        'message': 'Authentication successful',
                        'access_token': self.access_token,
                        'feed_token': self.feed_token,
                        'user_data': data['data']
                    }
                else:
                    return {
                        'success': False,
                        'message': data.get('message', 'Authentication failed')
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
    
    def get_access_token(self, auth_code: str, credentials: Dict) -> Dict:
        """AngelOne doesn't use OAuth, uses TOTP instead"""
        return self.authenticate(credentials)
    
    def _get_headers(self) -> Dict:
        """Get auth headers for API requests"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-UserType': 'USER',
            'X-SourceID': 'WEB',
            'X-ClientLocalIP': '127.0.0.1',
            'X-ClientPublicIP': '127.0.0.1',
            'X-MACAddress': '00:00:00:00:00:00',
            'X-PrivateKey': self.api_key
        }
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        return headers
    
    def get_historical_data(self, symbol: str, exchange: str, 
                          interval: str, from_date: str, to_date: str) -> pd.DataFrame:
        """
        Get historical OHLC data from AngelOne
        
        Intervals: ONE_MINUTE, THREE_MINUTE, FIVE_MINUTE, TEN_MINUTE, 
                  FIFTEEN_MINUTE, THIRTY_MINUTE, ONE_HOUR, ONE_DAY
        """
        if not self.is_authenticated():
            return pd.DataFrame()
        
        try:
            symboltoken = self._get_symbol_token(symbol, exchange)
            
            if not symboltoken:
                return pd.DataFrame()
            
            interval_map = {
                '1m': 'ONE_MINUTE', '3m': 'THREE_MINUTE', '5m': 'FIVE_MINUTE',
                '10m': 'TEN_MINUTE', '15m': 'FIFTEEN_MINUTE', '30m': 'THIRTY_MINUTE',
                '1h': 'ONE_HOUR', '1d': 'ONE_DAY'
            }
            angel_interval = interval_map.get(interval, 'ONE_DAY')
            
            from_datetime = f"{from_date} 09:15"
            to_datetime = f"{to_date} 15:30"
            
            response = self.session.post(
                f"{self.base_url}/rest/secure/angelbroking/historical/v1/getCandleData",
                json={
                    'exchange': exchange,
                    'symboltoken': symboltoken,
                    'interval': angel_interval,
                    'fromdate': from_datetime,
                    'todate': to_datetime
                },
                headers=self._get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                candles = data['data']
                
                df = pd.DataFrame(candles, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume'
                ])
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['oi'] = 0
                
                return df
            else:
                return pd.DataFrame()
        
        except Exception as e:
            print(f"AngelOne historical data error: {e}")
            return pd.DataFrame()
    
    def _get_symbol_token(self, symbol: str, exchange: str) -> Optional[str]:
        """Search for symbol token"""
        if not self.is_authenticated():
            return None
        
        try:
            response = self.session.post(
                f"{self.base_url}/rest/secure/angelbroking/order/v1/searchScrip",
                json={
                    'exchange': exchange,
                    'searchscrip': symbol
                },
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data') and len(data['data']) > 0:
                    return data['data'][0]['symboltoken']
            
            return None
        
        except Exception as e:
            print(f"AngelOne symbol search error: {e}")
            return None
    
    def get_live_quotes(self, symbols: List[Dict]) -> Dict:
        """Get live quotes from AngelOne"""
        if not self.is_authenticated():
            return {}
        
        try:
            results = {}
            
            for sym in symbols:
                symboltoken = self._get_symbol_token(sym['symbol'], sym['exchange'])
                
                if symboltoken:
                    response = self.session.post(
                        f"{self.base_url}/rest/secure/angelbroking/market/v1/quote/",
                        json={
                            'mode': 'FULL',
                            'exchangeTokens': {
                                sym['exchange']: [symboltoken]
                            }
                        },
                        headers=self._get_headers(),
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        quote_data = response.json()
                        results[sym['symbol']] = quote_data.get('data', {})
            
            return results
        
        except Exception as e:
            print(f"AngelOne quote error: {e}")
            return {}
    
    def get_option_chain(self, symbol: str, expiry: str = None) -> pd.DataFrame:
        """
        Get option chain from AngelOne
        Phase 2 feature - returning empty DataFrame for MVP
        """
        return pd.DataFrame()
    
    def place_order(self, order_params: Dict) -> Dict:
        """Place order on AngelOne"""
        if not self.is_authenticated():
            return {'success': False, 'message': 'Not authenticated'}
        
        try:
            response = self.session.post(
                f"{self.base_url}/rest/secure/angelbroking/order/v1/placeOrder",
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
                f"{self.base_url}/rest/secure/angelbroking/order/v1/getPosition",
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()['data']
                return data
            else:
                return []
        
        except Exception as e:
            print(f"AngelOne positions error: {e}")
            return []
    
    def get_funds(self) -> Dict:
        """Get account funds"""
        if not self.is_authenticated():
            return {}
        
        try:
            response = self.session.get(
                f"{self.base_url}/rest/secure/angelbroking/user/v1/getRMS",
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()['data']
            else:
                return {}
        
        except Exception as e:
            print(f"AngelOne funds error: {e}")
            return {}
    
    def cancel_order(self, order_id: str) -> Dict:
        """Cancel order"""
        if not self.is_authenticated():
            return {'success': False, 'message': 'Not authenticated'}
        
        try:
            response = self.session.post(
                f"{self.base_url}/rest/secure/angelbroking/order/v1/cancelOrder",
                json={
                    'variety': 'NORMAL',
                    'orderid': order_id
                },
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

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .base import BrokerInterface

class DhanBroker(BrokerInterface):
    """
    Dhan API v2 Integration
    Docs: https://dhanhq.co/docs/v2/
    """
    
    def __init__(self):
        super().__init__()
        self.broker_name = "Dhan"
        self.base_url = "https://api.dhan.co/v2"
        self.auth_url = "https://auth.dhan.co"
        self.client_id = None
        self.session = requests.Session()
    
    def authenticate(self, credentials: Dict) -> Dict:
        """
        For individual traders using direct access token
        
        Args:
            credentials: {
                'access_token': '...',  # 24-hour token from web.dhan.co
                'client_id': '...'      # Dhan client ID
            }
        
        Returns:
            Dict with auth status
        """
        access_token = credentials.get('access_token')
        self.client_id = credentials.get('client_id')
        
        if not access_token:
            return {
                'success': False,
                'message': 'Access token is required. Get it from web.dhan.co → Profile → DhanHQ APIs'
            }
        
        self.access_token = access_token
        self.authenticated = True
        
        return {
            'success': True,
            'message': 'Authentication successful (24-hour validity)',
            'access_token': self.access_token
        }
    
    def get_access_token(self, auth_code: str, credentials: Dict) -> Dict:
        """
        API Key based authentication (for partners/apps)
        Dhan uses 3-step OAuth flow
        
        Args:
            auth_code: Not used (implement 3-step flow separately)
            credentials: {'api_key': '...', 'api_secret': '...'}
        
        Returns:
            Dict with instructions for OAuth flow
        """
        return {
            'success': False,
            'message': 'Use direct access_token from web.dhan.co or implement 3-step OAuth flow'
        }
    
    def _get_headers(self) -> Dict:
        """Get auth headers for API requests"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        if self.access_token:
            headers['access-token'] = self.access_token
        return headers
    
    def get_historical_data(self, symbol: str, exchange: str, 
                          interval: str, from_date: str, to_date: str) -> pd.DataFrame:
        """
        Get historical OHLC data from Dhan
        
        Intervals: 
        - Daily: '1d'
        - Intraday: '1m', '5m', '15m', '25m', '1h' (maps to 1, 5, 15, 25, 60)
        
        Note: Requires securityId instead of symbol
        """
        if not self.is_authenticated():
            return pd.DataFrame()
        
        try:
            security_id = self._get_security_id(symbol, exchange)
            
            if not security_id:
                print(f"Dhan: Could not resolve securityId for {symbol}")
                return pd.DataFrame()
            
            interval_map = {
                '1m': '1', '5m': '5', '15m': '15', 
                '25m': '25', '1h': '60', '1d': 'daily'
            }
            
            dhan_interval = interval_map.get(interval, 'daily')
            
            if dhan_interval == 'daily':
                endpoint = f"{self.base_url}/charts/historical"
                payload = {
                    'securityId': security_id,
                    'exchangeSegment': self._get_exchange_segment(exchange),
                    'instrument': 'EQUITY',
                    'fromDate': from_date,
                    'toDate': to_date,
                    'oi': exchange == 'NFO'
                }
            else:
                endpoint = f"{self.base_url}/charts/intraday"
                from_datetime = f"{from_date} 09:30:00"
                to_datetime = f"{to_date} 15:30:00"
                
                payload = {
                    'securityId': security_id,
                    'exchangeSegment': self._get_exchange_segment(exchange),
                    'instrument': 'EQUITY' if exchange == 'NSE' else 'FUTIDX',
                    'interval': dhan_interval,
                    'fromDate': from_datetime,
                    'toDate': to_datetime,
                    'oi': exchange == 'NFO'
                }
            
            response = self.session.post(
                endpoint,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                df = pd.DataFrame({
                    'timestamp': pd.to_datetime(data.get('timestamp', []), unit='s'),
                    'open': data.get('open', []),
                    'high': data.get('high', []),
                    'low': data.get('low', []),
                    'close': data.get('close', []),
                    'volume': data.get('volume', []),
                    'oi': data.get('open_interest', [0] * len(data.get('timestamp', [])))
                })
                
                return df
            else:
                print(f"Dhan historical data error: {response.text}")
                return pd.DataFrame()
        
        except Exception as e:
            print(f"Dhan historical data exception: {e}")
            return pd.DataFrame()
    
    def _get_security_id(self, symbol: str, exchange: str) -> Optional[str]:
        """
        Get Dhan securityId for symbol
        Note: Requires security master download or API call
        Placeholder - returns None for now (need to implement security lookup)
        """
        security_map = {
            'NIFTY': '1333',     # Example
            'BANKNIFTY': '25',   # Example
            'RELIANCE': '500',   # Example
        }
        return security_map.get(symbol)
    
    def _get_exchange_segment(self, exchange: str) -> str:
        """Map exchange to Dhan exchange segment"""
        exchange_map = {
            'NSE': 'NSE_EQ',
            'NFO': 'NSE_FNO',
            'BSE': 'BSE_EQ',
            'MCX': 'MCX_COMM'
        }
        return exchange_map.get(exchange, 'NSE_EQ')
    
    def get_live_quotes(self, symbols: List[Dict]) -> Dict:
        """
        Get live quotes from Dhan
        Endpoint: POST /v2/marketfeed/ltp or /v2/marketfeed/quote
        """
        if not self.is_authenticated():
            return {}
        
        try:
            security_ids = []
            exchange_segments = []
            
            for sym in symbols:
                sec_id = self._get_security_id(sym['symbol'], sym['exchange'])
                if sec_id:
                    security_ids.append(sec_id)
                    exchange_segments.append(self._get_exchange_segment(sym['exchange']))
            
            if not security_ids:
                return {}
            
            response = self.session.post(
                f"{self.base_url}/marketfeed/ltp",
                headers=self._get_headers(),
                json={
                    'NSE_EQ': security_ids
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {}
        
        except Exception as e:
            print(f"Dhan quotes error: {e}")
            return {}
    
    def get_option_chain(self, symbol: str, expiry: str = None) -> pd.DataFrame:
        """
        Get option chain from Dhan
        Phase 2 feature - returning empty DataFrame for MVP
        """
        return pd.DataFrame()
    
    def place_order(self, order_params: Dict) -> Dict:
        """
        Place order on Dhan
        Endpoint: POST /v2/orders
        """
        if not self.is_authenticated():
            return {'success': False, 'message': 'Not authenticated'}
        
        try:
            response = self.session.post(
                f"{self.base_url}/orders",
                headers=self._get_headers(),
                json=order_params,
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
        """
        Get current positions
        Endpoint: GET /v2/positions
        """
        if not self.is_authenticated():
            return []
        
        try:
            response = self.session.get(
                f"{self.base_url}/positions",
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            else:
                return []
        
        except Exception as e:
            print(f"Dhan positions error: {e}")
            return []
    
    def get_funds(self) -> Dict:
        """
        Get account funds
        Endpoint: GET /v2/fundlimit
        """
        if not self.is_authenticated():
            return {}
        
        try:
            response = self.session.get(
                f"{self.base_url}/fundlimit",
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {}
        
        except Exception as e:
            print(f"Dhan funds error: {e}")
            return {}
    
    def cancel_order(self, order_id: str) -> Dict:
        """
        Cancel order
        Endpoint: DELETE /v2/orders/{orderId}
        """
        if not self.is_authenticated():
            return {'success': False, 'message': 'Not authenticated'}
        
        try:
            response = self.session.delete(
                f"{self.base_url}/orders/{order_id}",
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

import os
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional

class OpenAlgoAuth:
    def __init__(self):
        self.api_key = os.getenv("OPENALGO_API_KEY", "")
        self.host = os.getenv("OPENALGO_HOST", "http://127.0.0.1:5000")
        self.session = requests.Session()
        self.authenticated = False
        
    def set_credentials(self, api_key: str, host: str = None):
        self.api_key = api_key
        if host:
            self.host = host
        self.authenticated = True
        
    def get_headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def verify_connection(self) -> Dict:
        try:
            if not self.api_key:
                return {
                    'success': False,
                    'message': 'API key not configured'
                }
            
            response = self.session.get(
                f"{self.host}/api/v1/funds",
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                self.authenticated = True
                return {
                    'success': True,
                    'message': 'Connected to OpenAlgo successfully',
                    'data': response.json()
                }
            elif response.status_code == 401:
                return {
                    'success': False,
                    'message': 'Invalid API key'
                }
            else:
                return {
                    'success': False,
                    'message': f'Connection failed: {response.status_code}'
                }
                
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'message': 'Cannot connect to OpenAlgo. Make sure OpenAlgo is running.'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Connection error: {str(e)}'
            }
    
    def get_funds(self) -> Dict:
        try:
            response = self.session.get(
                f"{self.host}/api/v1/funds",
                headers=self.get_headers(),
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
                    'message': f'Failed to fetch funds: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error fetching funds: {str(e)}'
            }
    
    def get_positions(self) -> Dict:
        try:
            response = self.session.get(
                f"{self.host}/api/v1/positions",
                headers=self.get_headers(),
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
                    'message': f'Failed to fetch positions: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error fetching positions: {str(e)}'
            }
    
    def get_orderbook(self) -> Dict:
        try:
            response = self.session.get(
                f"{self.host}/api/v1/orderbook",
                headers=self.get_headers(),
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
                    'message': f'Failed to fetch orderbook: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error fetching orderbook: {str(e)}'
            }
    
    def place_order(self, order_params: Dict) -> Dict:
        try:
            response = self.session.post(
                f"{self.host}/api/v1/placeorder",
                headers=self.get_headers(),
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
                    'message': f'Order placement failed: {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error placing order: {str(e)}'
            }
    
    def cancel_order(self, order_id: str) -> Dict:
        try:
            response = self.session.post(
                f"{self.host}/api/v1/cancelorder",
                headers=self.get_headers(),
                json={'orderid': order_id},
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
                    'message': f'Order cancellation failed: {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error cancelling order: {str(e)}'
            }
    
    def get_quotes(self, symbol: str, exchange: str = "NSE") -> Dict:
        try:
            response = self.session.post(
                f"{self.host}/api/v1/quotes",
                headers=self.get_headers(),
                json={
                    'symbol': symbol,
                    'exchange': exchange
                },
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
                    'message': f'Failed to fetch quotes: {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error fetching quotes: {str(e)}'
            }
    
    def get_depth(self, symbol: str, exchange: str = "NSE") -> Dict:
        try:
            response = self.session.post(
                f"{self.host}/api/v1/depth",
                headers=self.get_headers(),
                json={
                    'symbol': symbol,
                    'exchange': exchange
                },
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
                    'message': f'Failed to fetch market depth: {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error fetching market depth: {str(e)}'
            }
    
    def close_all_positions(self) -> Dict:
        try:
            response = self.session.post(
                f"{self.host}/api/v1/closeposition",
                headers=self.get_headers(),
                json={},
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
                    'message': f'Failed to close positions: {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error closing positions: {str(e)}'
            }
    
    def get_broker_info(self) -> Dict:
        try:
            response = self.session.get(
                f"{self.host}/api/v1/brokerinfo",
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'broker': data.get('broker', 'Unknown'),
                    'user': data.get('user', 'Unknown'),
                    'data': data
                }
            else:
                return {
                    'success': False,
                    'message': f'Failed to fetch broker info: {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error fetching broker info: {str(e)}'
            }
    
    def is_connected(self) -> bool:
        return self.authenticated and bool(self.api_key)
    
    def get_historical_data(self, symbol: str, exchange: str, interval: str, 
                           start_date: str, end_date: str) -> Dict:
        """
        Get historical OHLC data from OpenAlgo
        
        Args:
            symbol: Trading symbol
            exchange: Exchange (NSE, NFO, BSE, etc.)
            interval: Time interval (1m, 5m, 15m, 1h, 1d, etc.)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            Dict with historical data (OHLC, volume, OI)
        """
        try:
            response = self.session.post(
                f"{self.host}/api/v1/history",
                headers=self.get_headers(),
                json={
                    'symbol': symbol,
                    'exchange': exchange,
                    'interval': interval,
                    'start_date': start_date,
                    'end_date': end_date
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'message': f'Failed to fetch historical data: {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error fetching historical data: {str(e)}'
            }
    
    def get_intervals(self) -> Dict:
        """Get supported time intervals for historical data"""
        try:
            response = self.session.get(
                f"{self.host}/api/v1/intervals",
                headers=self.get_headers(),
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
                    'message': f'Failed to fetch intervals: {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error fetching intervals: {str(e)}'
            }
    
    def place_smart_order(self, order_params: Dict) -> Dict:
        """
        Place smart order with position-aware sizing
        """
        try:
            response = self.session.post(
                f"{self.host}/api/v1/placesmartorder",
                headers=self.get_headers(),
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
                    'message': f'Smart order placement failed: {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error placing smart order: {str(e)}'
            }
    
    def get_position_book(self) -> Dict:
        """Get position book via OpenAlgo API"""
        try:
            response = self.session.get(
                f"{self.host}/api/v1/positionbook",
                headers=self.get_headers(),
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
                    'message': f'Failed to fetch position book: {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error fetching position book: {str(e)}'
            }

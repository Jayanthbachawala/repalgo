import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .base import BrokerInterface

class NubraBroker(BrokerInterface):
    """
    Nubra API Integration
    Docs: https://nubra.io/products/api/docs/
    """
    
    def __init__(self):
        super().__init__()
        self.broker_name = "Nubra"
        self.base_url_prod = "https://api.nubra.io"
        self.base_url_uat = "https://uatapi.nubra.io"
        self.base_url = self.base_url_prod
        self.session = requests.Session()
        self.session_token = None
        self.device_id = None
    
    def authenticate(self, credentials: Dict) -> Dict:
        """
        Step 1: Send OTP to phone number
        
        Args:
            credentials: {
                'phone': '...',
                'device_id': '...',
                'env': 'PROD' or 'UAT'  # optional, defaults to PROD
            }
        
        Returns:
            Dict with temp_token to be used in next step
        """
        phone = credentials.get('phone')
        self.device_id = credentials.get('device_id', 'AI_TRADER_001')
        env = credentials.get('env', 'PROD')
        
        self.base_url = self.base_url_prod if env == 'PROD' else self.base_url_uat
        
        if not phone:
            return {
                'success': False,
                'message': 'Phone number is required'
            }
        
        try:
            response = self.session.post(
                f"{self.base_url}/sendphoneotp",
                headers={'Content-Type': 'application/json'},
                json={
                    'phone': phone,
                    'skip_totp': False
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'message': 'OTP sent successfully',
                    'temp_token': data.get('temp_token'),
                    'next_step': 'verify_otp',
                    'expiry': data.get('expiry', 30)
                }
            else:
                return {
                    'success': False,
                    'message': f'Failed to send OTP: {response.text}'
                }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    def verify_otp(self, phone: str, otp: str, temp_token: str) -> Dict:
        """
        Step 2: Verify OTP
        
        Args:
            phone: Phone number
            otp: OTP received on phone
            temp_token: Token from authenticate() response
        
        Returns:
            Dict with auth_token for PIN verification
        """
        if not all([phone, otp, temp_token]):
            return {
                'success': False,
                'message': 'Phone, OTP, and temp_token are required'
            }
        
        try:
            response = self.session.post(
                f"{self.base_url}/verifyphoneotp",
                headers={
                    'x-temp-token': temp_token,
                    'x-device-id': self.device_id,
                    'Content-Type': 'application/json'
                },
                json={
                    'phone': phone,
                    'otp': otp
                },
                timeout=10
            )
            
            data = response.json()
            
            # Check if response has auth_token (success indicator)
            if data.get('auth_token') and data.get('next') == 'ENTER_MPIN':
                return {
                    'success': True,
                    'message': data.get('message', 'OTP verified successfully'),
                    'auth_token': data.get('auth_token'),
                    'next_step': 'verify_pin'
                }
            elif response.status_code in [200, 201]:
                return {
                    'success': True,
                    'message': data.get('message', 'OTP verified successfully'),
                    'auth_token': data.get('auth_token'),
                    'next_step': 'verify_pin'
                }
            else:
                return {
                    'success': False,
                    'message': f'OTP verification failed: {data.get("message", response.text)}'
                }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    def verify_pin(self, pin: str, auth_token: str) -> Dict:
        """
        Step 3: Verify PIN to get session token
        
        Args:
            pin: User's MPIN
            auth_token: Token from verify_otp() response
        
        Returns:
            Dict with session_token for API access
        """
        if not all([pin, auth_token]):
            return {
                'success': False,
                'message': 'PIN and auth_token are required'
            }
        
        try:
            response = self.session.post(
                f"{self.base_url}/verifypin",
                headers={
                    'Authorization': f'Bearer {auth_token}',
                    'x-device-id': self.device_id,
                    'Content-Type': 'application/json'
                },
                json={
                    'pin': pin
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.session_token = data.get('session_token')
                self.access_token = self.session_token
                self.authenticated = True
                
                return {
                    'success': True,
                    'message': 'Authentication successful',
                    'session_token': self.session_token,
                    'user_data': {
                        'email': data.get('email'),
                        'phone': data.get('phone'),
                        'userId': data.get('userId')
                    }
                }
            else:
                return {
                    'success': False,
                    'message': f'PIN verification failed: {response.text}'
                }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    def get_access_token(self, auth_code: str, credentials: Dict) -> Dict:
        """
        Nubra uses multi-step OTP flow, not OAuth
        Use authenticate() → verify_otp() → verify_pin() instead
        """
        return {
            'success': False,
            'message': 'Nubra uses OTP authentication. Use authenticate() → verify_otp() → verify_pin() flow'
        }
    
    def _get_headers(self) -> Dict:
        """Get auth headers for API requests"""
        headers = {
            'Content-Type': 'application/json',
            'x-device-id': self.device_id
        }
        if self.session_token:
            headers['Authorization'] = f'Bearer {self.session_token}'
        return headers
    
    def get_historical_data(self, symbol: str, exchange: str, 
                          interval: str, from_date: str, to_date: str) -> pd.DataFrame:
        """
        Get historical OHLC data from Nubra
        Note: Actual endpoint not documented yet - placeholder implementation
        """
        if not self.is_authenticated():
            return pd.DataFrame()
        
        # Placeholder - actual Nubra historical data endpoint to be documented
        return pd.DataFrame()
    
    def get_live_quotes(self, symbols: List[Dict]) -> Dict:
        """
        Get live quotes from Nubra
        Note: Actual endpoint not documented yet - placeholder implementation
        """
        if not self.is_authenticated():
            return {}
        
        # Placeholder - actual Nubra quotes endpoint to be documented
        return {}
    
    def get_option_chain(self, symbol: str, expiry: str = None) -> pd.DataFrame:
        """
        Get option chain from Nubra
        Phase 2 feature - returning empty DataFrame for MVP
        """
        return pd.DataFrame()
    
    def place_order(self, order_params: Dict) -> Dict:
        """
        Place order on Nubra
        Note: Actual endpoint not documented yet - placeholder implementation
        """
        if not self.is_authenticated():
            return {'success': False, 'message': 'Not authenticated'}
        
        # Placeholder - actual Nubra order placement endpoint to be documented
        return {
            'success': False,
            'message': 'Order placement endpoint not yet documented by Nubra'
        }
    
    def get_positions(self) -> List[Dict]:
        """
        Get current positions
        Note: Actual endpoint not documented yet - placeholder implementation
        """
        if not self.is_authenticated():
            return []
        
        # Placeholder
        return []
    
    def get_funds(self) -> Dict:
        """
        Get account funds
        Note: Actual endpoint not documented yet - placeholder implementation
        """
        if not self.is_authenticated():
            return {}
        
        # Placeholder
        return {}
    
    def cancel_order(self, order_id: str) -> Dict:
        """
        Cancel order
        Note: Actual endpoint not documented yet - placeholder implementation
        """
        if not self.is_authenticated():
            return {'success': False, 'message': 'Not authenticated'}
        
        # Placeholder
        return {
            'success': False,
            'message': 'Order cancellation endpoint not yet documented by Nubra'
        }

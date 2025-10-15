import os
import requests
import json
from datetime import datetime, timedelta
import streamlit as st

class UpstoxAuth:
    def __init__(self):
        self.api_key = os.getenv("UPSTOX_API_KEY", "")
        self.api_secret = os.getenv("UPSTOX_API_SECRET", "")
        self.redirect_uri = os.getenv("UPSTOX_REDIRECT_URI", "")
        self.base_url = "https://api.upstox.com/v2"
        
    def authenticate(self, api_key=None, api_secret=None, redirect_uri=None):
        """
        Authenticate with Upstox API
        Returns token on success or error message
        """
        try:
            # Use provided credentials or fallback to environment
            api_key = api_key or self.api_key
            api_secret = api_secret or self.api_secret
            redirect_uri = redirect_uri or self.redirect_uri
            
            if not all([api_key, api_secret, redirect_uri]):
                return {
                    'success': False,
                    'message': 'Missing required credentials. Please provide API key, secret, and redirect URI.'
                }
            
            # In mock mode, return a fake token
            if not api_key.startswith('real_'):
                return {
                    'success': True,
                    'token': 'mock_token_' + str(int(datetime.now().timestamp())),
                    'message': 'Mock authentication successful'
                }
            
            # Real authentication flow would go here
            auth_url = f"{self.base_url}/login/authorization/dialog"
            params = {
                'response_type': 'code',
                'client_id': api_key,
                'redirect_uri': redirect_uri
            }
            
            # This would typically redirect user to Upstox login page
            # For now, we'll simulate the process
            return {
                'success': False,
                'message': 'Please implement OAuth flow for production use. Currently in mock mode.'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Authentication error: {str(e)}'
            }
    
    def get_access_token(self, auth_code):
        """
        Exchange authorization code for access token
        """
        try:
            url = f"{self.base_url}/login/authorization/token"
            
            data = {
                'code': auth_code,
                'client_id': self.api_key,
                'client_secret': self.api_secret,
                'redirect_uri': self.redirect_uri,
                'grant_type': 'authorization_code'
            }
            
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                return {
                    'success': True,
                    'access_token': token_data.get('access_token'),
                    'token_type': token_data.get('token_type'),
                    'expires_in': token_data.get('expires_in')
                }
            else:
                return {
                    'success': False,
                    'message': f'Token exchange failed: {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Token exchange error: {str(e)}'
            }
    
    def validate_token(self, token):
        """
        Validate if the access token is still valid
        """
        try:
            # Mock validation
            if token and token.startswith('mock_token_'):
                return {'success': True, 'valid': True}
            
            # Real validation would make API call
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(f"{self.base_url}/user/profile", headers=headers)
            
            return {
                'success': True,
                'valid': response.status_code == 200
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Token validation error: {str(e)}'
            }
    
    def get_user_profile(self, token):
        """
        Get user profile information
        """
        try:
            if token and token.startswith('mock_token_'):
                return {
                    'success': True,
                    'profile': {
                        'user_name': 'Demo User',
                        'email': 'demo@example.com',
                        'user_id': 'DEMO123',
                        'broker': 'UPSTOX'
                    }
                }
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(f"{self.base_url}/user/profile", headers=headers)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'profile': response.json().get('data', {})
                }
            else:
                return {
                    'success': False,
                    'message': f'Profile fetch failed: {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Profile fetch error: {str(e)}'
            }
    
    def logout(self, token):
        """
        Logout and invalidate token
        """
        try:
            if token and token.startswith('mock_token_'):
                return {'success': True, 'message': 'Mock logout successful'}
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.delete(f"{self.base_url}/logout", headers=headers)
            
            return {
                'success': response.status_code == 200,
                'message': 'Logout successful' if response.status_code == 200 else 'Logout failed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Logout error: {str(e)}'
            }

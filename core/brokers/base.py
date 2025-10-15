from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime

class BrokerInterface(ABC):
    """
    Unified broker interface for all Indian brokers
    Provides standardized methods for authentication, market data, and trading
    """
    
    def __init__(self):
        self.authenticated = False
        self.access_token = None
        self.broker_name = "Unknown"
    
    @abstractmethod
    def authenticate(self, credentials: Dict) -> Dict:
        """
        Authenticate with broker
        
        Args:
            credentials: Dict containing broker-specific auth params
        
        Returns:
            Dict with 'success', 'message', and optional 'data'
        """
        pass
    
    @abstractmethod
    def get_access_token(self, auth_code: str, credentials: Dict) -> Dict:
        """
        Exchange authorization code for access token
        
        Args:
            auth_code: Authorization code from OAuth callback
            credentials: Dict containing API credentials
        
        Returns:
            Dict with access token and user info
        """
        pass
    
    @abstractmethod
    def get_historical_data(self, symbol: str, exchange: str, 
                          interval: str, from_date: str, to_date: str) -> pd.DataFrame:
        """
        Get historical OHLC data
        
        Args:
            symbol: Trading symbol
            exchange: Exchange code (NSE, NFO, BSE, etc.)
            interval: Time interval (1m, 5m, 15m, 1h, 1d, etc.)
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
        
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume, oi
        """
        pass
    
    @abstractmethod
    def get_live_quotes(self, symbols: List[Dict]) -> Dict:
        """
        Get live market quotes
        
        Args:
            symbols: List of dicts with 'symbol' and 'exchange'
        
        Returns:
            Dict with symbol quotes
        """
        pass
    
    @abstractmethod
    def get_option_chain(self, symbol: str, expiry: str = None) -> pd.DataFrame:
        """
        Get option chain data
        
        Args:
            symbol: Underlying symbol (NIFTY, BANKNIFTY, etc.)
            expiry: Expiry date (optional)
        
        Returns:
            DataFrame with option chain
        """
        pass
    
    @abstractmethod
    def place_order(self, order_params: Dict) -> Dict:
        """
        Place trading order
        
        Args:
            order_params: Dict with order parameters
        
        Returns:
            Dict with order status
        """
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Dict]:
        """
        Get current positions
        
        Returns:
            List of position dicts
        """
        pass
    
    @abstractmethod
    def get_funds(self) -> Dict:
        """
        Get account funds/margin
        
        Returns:
            Dict with funds info
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> Dict:
        """
        Cancel pending order
        
        Args:
            order_id: Order ID to cancel
        
        Returns:
            Dict with cancellation status
        """
        pass
    
    def is_authenticated(self) -> bool:
        """Check if broker is authenticated"""
        return self.authenticated and bool(self.access_token)
    
    def get_broker_name(self) -> str:
        """Get broker name"""
        return self.broker_name

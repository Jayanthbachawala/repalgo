from typing import Optional
from .base import BrokerInterface
from .zerodha import ZerodhaBroker
from .upstox import UpstoxBroker
from .angelone import AngelOneBroker
from .nubra import NubraBroker
from .dhan import DhanBroker

class BrokerFactory:
    """
    Factory class for creating broker instances
    Provides centralized broker selection and initialization
    """
    
    SUPPORTED_BROKERS = {
        'zerodha': ZerodhaBroker,
        'upstox': UpstoxBroker,
        'angelone': AngelOneBroker,
        'nubra': NubraBroker,
        'dhan': DhanBroker
    }
    
    @classmethod
    def create_broker(cls, broker_name: str) -> Optional[BrokerInterface]:
        """
        Create broker instance by name
        
        Args:
            broker_name: Name of broker ('zerodha', 'upstox', 'angelone')
        
        Returns:
            Broker instance or None if not supported
        """
        broker_name = broker_name.lower().strip()
        
        broker_class = cls.SUPPORTED_BROKERS.get(broker_name)
        
        if broker_class:
            return broker_class()
        else:
            return None
    
    @classmethod
    def get_supported_brokers(cls) -> list:
        """Get list of supported broker names"""
        return list(cls.SUPPORTED_BROKERS.keys())
    
    @classmethod
    def get_broker_display_names(cls) -> dict:
        """Get mapping of broker codes to display names"""
        return {
            'zerodha': 'Zerodha (Kite Connect)',
            'upstox': 'Upstox',
            'angelone': 'AngelOne (SmartAPI)',
            'nubra': 'Nubra',
            'dhan': 'Dhan'
        }

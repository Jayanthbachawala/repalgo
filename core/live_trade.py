import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
from core.brokers.base import BrokerInterface
import uuid
import json
import os

class LiveTradingEngine:
    def __init__(self, broker: BrokerInterface = None):
        self.broker = broker
        self.positions = []
        self.trade_history = []
        self.enabled = False
    
    def set_broker(self, broker: BrokerInterface):
        """Set the broker instance"""
        self.broker = broker
        
    def enable_live_trading(self) -> Dict:
        if not self.broker or not self.broker.is_authenticated():
            return {
                'success': False,
                'message': 'Broker not authenticated. Please connect to a broker first.'
            }
        
        self.enabled = True
        return {
            'success': True,
            'message': f"Live trading enabled with {self.broker.broker_name}",
            'broker': self.broker.broker_name
        }
    
    def disable_live_trading(self) -> Dict:
        self.enabled = False
        return {
            'success': True,
            'message': 'Live trading disabled'
        }
    
    def execute_live_trade(self, signal: Dict, risk_manager) -> Dict:
        if not self.enabled:
            return {
                'success': False,
                'message': 'Live trading is not enabled'
            }
        
        if not self.broker or not self.broker.is_authenticated():
            return {
                'success': False,
                'message': 'Broker not authenticated'
            }
        
        if not risk_manager.validate_trade(signal):
            return {
                'success': False,
                'message': 'Trade rejected by risk manager'
            }
        
        try:
            symbol = signal['symbol']
            strike = signal['strike']
            option_type = signal['type']
            action = signal['action']
            
            # Prepare order parameters
            order_params = {
                'symbol': symbol,
                'strike': strike,
                'option_type': option_type,
                'action': action.upper(),
                'quantity': signal.get('quantity', 1),
                'order_type': 'MARKET',
                'product': 'MIS',
                'exchange': 'NFO'
            }
            
            # Place order using broker
            result = self.broker.place_order(order_params)
            
            if result.get('success'):
                order_data = result.get('data', {})
                
                trade_record = {
                    'id': str(uuid.uuid4()),
                    'order_id': order_data.get('order_id', str(uuid.uuid4())),
                    'symbol': symbol,
                    'strike': strike,
                    'type': option_type,
                    'action': action,
                    'quantity': signal.get('quantity', 1),
                    'price': signal.get('price', 0),
                    'timestamp': datetime.now().isoformat(),
                    'trade_type': 'live',
                    'confidence': signal.get('confidence', 0),
                    'reasoning': signal.get('reasoning', ''),
                    'status': 'executed',
                    'broker': self.broker.broker_name
                }
                
                self.trade_history.append(trade_record)
                self._save_trade_history()
                
                return {
                    'success': True,
                    'message': f'Live order executed: {symbol} {strike}{option_type}',
                    'order_id': trade_record['order_id'],
                    'trade': trade_record
                }
            else:
                return result
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error executing live trade: {str(e)}'
            }
    
    def get_live_positions(self) -> List[Dict]:
        """Get current live positions from broker"""
        if not self.broker or not self.broker.is_authenticated():
            return []
        
        try:
            positions = self.broker.get_positions()
            return positions if positions else []
        except Exception as e:
            print(f"Error fetching positions: {e}")
            return []
    
    def close_position(self, position: Dict) -> Dict:
        """Close a live position"""
        if not self.enabled:
            return {
                'success': False,
                'message': 'Live trading is not enabled'
            }
        
        if not self.broker or not self.broker.is_authenticated():
            return {
                'success': False,
                'message': 'Broker not authenticated'
            }
        
        try:
            # Determine action (reverse of position)
            action = 'SELL' if position.get('quantity', 0) > 0 else 'BUY'
            
            order_params = {
                'symbol': position['symbol'],
                'strike': position.get('strike'),
                'option_type': position.get('type'),
                'action': action,
                'quantity': abs(position.get('quantity', 1)),
                'order_type': 'MARKET',
                'product': position.get('product', 'MIS'),
                'exchange': position.get('exchange', 'NFO')
            }
            
            result = self.broker.place_order(order_params)
            
            if result.get('success'):
                return {
                    'success': True,
                    'message': 'Position closed successfully',
                    'data': result.get('data')
                }
            else:
                return result
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error closing position: {str(e)}'
            }
    
    def get_account_funds(self) -> Dict:
        """Get account funds from broker"""
        if not self.broker or not self.broker.is_authenticated():
            return {}
        
        try:
            return self.broker.get_funds()
        except Exception as e:
            print(f"Error fetching funds: {e}")
            return {}
    
    def _save_trade_history(self):
        """Save trade history to file"""
        try:
            os.makedirs('data', exist_ok=True)
            with open('data/live_trades.json', 'w') as f:
                json.dump(self.trade_history, f, indent=2)
        except Exception as e:
            print(f"Error saving trade history: {e}")
    
    def load_trade_history(self):
        """Load trade history from file"""
        try:
            if os.path.exists('data/live_trades.json'):
                with open('data/live_trades.json', 'r') as f:
                    self.trade_history = json.load(f)
        except Exception as e:
            print(f"Error loading trade history: {e}")
    
    def get_trade_history(self) -> List[Dict]:
        """Get trade history"""
        return self.trade_history
    
    def is_enabled(self) -> bool:
        """Check if live trading is enabled"""
        return self.enabled and self.broker and self.broker.is_authenticated()

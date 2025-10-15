import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

class RiskManager:
    def __init__(self):
        # Default risk parameters
        self.max_loss_per_trade = 5000  # ₹5000 max loss per trade
        self.max_daily_loss = 15000     # ₹15000 max daily loss
        self.max_portfolio_risk = 50000 # ₹50000 max portfolio risk
        self.max_positions_per_symbol = 3
        self.max_total_positions = 10
        
        # Risk thresholds
        self.stop_loss_percent = 0.10    # 10% stop loss
        self.take_profit_percent = 0.20  # 20% take profit
        self.position_size_percent = 0.02 # 2% of capital per position
        
        # Liquidity requirements
        self.min_volume = 1000
        self.max_bid_ask_spread = 0.05   # 5% max spread
        self.min_open_interest = 5000
        
        # Time-based restrictions
        self.market_open_time = (9, 15)   # 9:15 AM
        self.market_close_time = (15, 30) # 3:30 PM
        self.no_trade_before = (9, 20)    # No trades before 9:20 AM
        self.no_trade_after = (15, 15)    # No trades after 3:15 PM
        
        self.enabled = True
        self.daily_pnl = 0
        self.current_positions = []
        
    def validate_trade(self, signal: Dict) -> bool:
        """
        Comprehensive trade validation
        Returns True if trade passes all risk checks
        """
        if not self.enabled:
            return True  # Risk management disabled
        
        validation_results = {
            'time_check': self.validate_trading_time(),
            'position_limit_check': self.validate_position_limits(signal),
            'risk_limit_check': self.validate_risk_limits(signal),
            'liquidity_check': self.validate_liquidity(signal),
            'spread_check': self.validate_spread(signal),
            'volatility_check': self.validate_volatility(signal),
            'daily_loss_check': self.validate_daily_loss_limit()
        }
        
        # All checks must pass
        all_passed = all(validation_results.values())
        
        # Log validation results
        self.log_validation(signal, validation_results)
        
        return all_passed
    
    def validate_trading_time(self) -> bool:
        """Check if current time is within allowed trading hours"""
        now = datetime.now()
        current_time = (now.hour, now.minute)
        
        # Check if market is open
        market_open = self.market_open_time
        market_close = self.market_close_time
        
        # Check if within trading hours
        within_market_hours = (
            (current_time >= market_open) and 
            (current_time <= market_close)
        )
        
        # Check if not in restricted time zones
        not_in_early_restriction = current_time >= self.no_trade_before
        not_in_late_restriction = current_time <= self.no_trade_after
        
        # Check if it's a weekday
        is_weekday = now.weekday() < 5
        
        return (within_market_hours and 
                not_in_early_restriction and 
                not_in_late_restriction and 
                is_weekday)
    
    def validate_position_limits(self, signal: Dict) -> bool:
        """Check position limit constraints"""
        symbol = signal['symbol']
        
        # Count current positions for this symbol
        symbol_positions = len([p for p in self.current_positions 
                               if p['symbol'] == symbol])
        
        # Check symbol-specific position limit
        if symbol_positions >= self.max_positions_per_symbol:
            return False
        
        # Check total position limit
        if len(self.current_positions) >= self.max_total_positions:
            return False
        
        return True
    
    def validate_risk_limits(self, signal: Dict) -> bool:
        """Check risk limit constraints"""
        estimated_trade_value = signal.get('price', 0) * signal.get('quantity', 1)
        
        # Check per-trade risk limit
        if estimated_trade_value > self.max_loss_per_trade:
            return False
        
        # Calculate current portfolio risk
        current_portfolio_value = sum(p.get('current_value', 0) 
                                    for p in self.current_positions)
        
        # Check portfolio risk limit
        if (current_portfolio_value + estimated_trade_value) > self.max_portfolio_risk:
            return False
        
        return True
    
    def validate_daily_loss_limit(self) -> bool:
        """Check if daily loss limit has been breached"""
        return abs(self.daily_pnl) < self.max_daily_loss
    
    def validate_liquidity(self, signal: Dict) -> bool:
        """Check liquidity requirements"""
        # Get option data from signal
        volume = signal.get('volume', 0)
        open_interest = signal.get('open_interest', 0)
        
        # Check minimum volume
        if volume < self.min_volume:
            return False
        
        # Check minimum open interest
        if open_interest < self.min_open_interest:
            return False
        
        return True
    
    def validate_spread(self, signal: Dict) -> bool:
        """Check bid-ask spread requirements"""
        bid = signal.get('bid', 0)
        ask = signal.get('ask', 0)
        ltp = signal.get('price', 0)
        
        if ltp == 0 or ask <= bid:
            return False
        
        # Calculate spread percentage
        spread_percent = (ask - bid) / ltp
        
        return spread_percent <= self.max_bid_ask_spread
    
    def validate_volatility(self, signal: Dict) -> bool:
        """Check volatility constraints"""
        iv = signal.get('iv', 20) / 100  # Convert percentage to decimal
        
        # Avoid extremely high volatility (> 50%)
        if iv > 0.50:
            return False
        
        # Avoid extremely low volatility (< 5%)
        if iv < 0.05:
            return False
        
        return True
    
    def calculate_position_size(self, signal: Dict, available_capital: float) -> int:
        """Calculate appropriate position size based on risk parameters"""
        if available_capital <= 0:
            return 0
        
        price_per_lot = signal.get('price', 0) * signal.get('lot_size', 75)
        
        if price_per_lot <= 0:
            return 1
        
        # Calculate based on percentage of capital
        max_amount = available_capital * self.position_size_percent
        
        # Calculate based on risk per trade
        risk_based_amount = min(max_amount, self.max_loss_per_trade)
        
        # Calculate number of lots
        lots = int(risk_based_amount / price_per_lot)
        
        return max(1, lots)  # Minimum 1 lot
    
    def calculate_stop_loss(self, entry_price: float, option_type: str) -> float:
        """Calculate stop loss price"""
        if option_type.upper() in ['CE', 'CALL']:
            # For calls, stop loss is below entry
            return entry_price * (1 - self.stop_loss_percent)
        else:
            # For puts, stop loss is below entry (puts lose value when underlying goes up)
            return entry_price * (1 - self.stop_loss_percent)
    
    def calculate_take_profit(self, entry_price: float, option_type: str) -> float:
        """Calculate take profit price"""
        # Take profit is always above entry for both calls and puts
        return entry_price * (1 + self.take_profit_percent)
    
    def add_position(self, trade_data: Dict):
        """Add a new position to tracking"""
        position = {
            'id': trade_data.get('id'),
            'symbol': trade_data.get('symbol'),
            'strike': trade_data.get('strike'),
            'type': trade_data.get('type'),
            'quantity': trade_data.get('quantity', 1),
            'entry_price': trade_data.get('entry_price'),
            'entry_time': trade_data.get('entry_time', datetime.now()),
            'stop_loss': self.calculate_stop_loss(
                trade_data.get('entry_price', 0), 
                trade_data.get('type', 'CE')
            ),
            'take_profit': self.calculate_take_profit(
                trade_data.get('entry_price', 0), 
                trade_data.get('type', 'CE')
            ),
            'current_price': trade_data.get('entry_price'),
            'unrealized_pnl': 0,
            'status': 'open'
        }
        
        self.current_positions.append(position)
    
    def remove_position(self, position_id: str):
        """Remove a position from tracking"""
        self.current_positions = [p for p in self.current_positions 
                                 if p.get('id') != position_id]
    
    def update_position_prices(self, price_updates: Dict):
        """Update current prices for all positions"""
        for position in self.current_positions:
            key = f"{position['symbol']}_{position['type']}_{position['strike']}"
            if key in price_updates:
                old_price = position['current_price']
                new_price = price_updates[key]
                position['current_price'] = new_price
                
                # Calculate unrealized P&L
                pnl = (new_price - position['entry_price']) * position['quantity']
                position['unrealized_pnl'] = pnl
    
    def check_stop_loss_take_profit(self) -> List[Dict]:
        """Check if any positions hit stop loss or take profit"""
        alerts = []
        
        for position in self.current_positions:
            current_price = position['current_price']
            
            # Check stop loss
            if current_price <= position['stop_loss']:
                alerts.append({
                    'type': 'stop_loss',
                    'position': position,
                    'message': f"Stop loss hit for {position['symbol']} {position['type']} {position['strike']}"
                })
            
            # Check take profit
            elif current_price >= position['take_profit']:
                alerts.append({
                    'type': 'take_profit',
                    'position': position,
                    'message': f"Take profit hit for {position['symbol']} {position['type']} {position['strike']}"
                })
        
        return alerts
    
    def get_portfolio_summary(self) -> Dict:
        """Get current portfolio risk summary"""
        total_positions = len(self.current_positions)
        total_unrealized_pnl = sum(p.get('unrealized_pnl', 0) for p in self.current_positions)
        total_investment = sum(
            p.get('entry_price', 0) * p.get('quantity', 0) 
            for p in self.current_positions
        )
        
        # Calculate risk metrics
        portfolio_delta = sum(p.get('delta', 0) * p.get('quantity', 0) 
                            for p in self.current_positions)
        
        return {
            'total_positions': total_positions,
            'total_investment': total_investment,
            'unrealized_pnl': total_unrealized_pnl,
            'daily_pnl': self.daily_pnl,
            'portfolio_delta': portfolio_delta,
            'risk_utilization': (total_investment / self.max_portfolio_risk) * 100,
            'daily_loss_utilization': (abs(self.daily_pnl) / self.max_daily_loss) * 100
        }
    
    def get_risk_metrics(self) -> Dict:
        """Get detailed risk metrics"""
        portfolio_summary = self.get_portfolio_summary()
        
        # Calculate additional metrics
        max_drawdown = min(0, min(p.get('unrealized_pnl', 0) for p in self.current_positions) if self.current_positions else 0)
        
        winning_positions = len([p for p in self.current_positions if p.get('unrealized_pnl', 0) > 0])
        total_positions = len(self.current_positions)
        win_rate = (winning_positions / total_positions * 100) if total_positions > 0 else 0
        
        return {
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'average_position_size': portfolio_summary['total_investment'] / max(1, total_positions),
            'risk_reward_ratio': self.take_profit_percent / self.stop_loss_percent,
            'positions_at_risk': len([p for p in self.current_positions 
                                    if p.get('unrealized_pnl', 0) < -self.max_loss_per_trade * 0.5])
        }
    
    def log_validation(self, signal: Dict, validation_results: Dict):
        """Log validation results for debugging"""
        # In production, this would log to a file or database
        failed_checks = [check for check, result in validation_results.items() if not result]
        
        if failed_checks:
            print(f"Trade validation failed for {signal.get('symbol')} {signal.get('strike')}")
            print(f"Failed checks: {failed_checks}")
    
    def update_settings(self, new_settings: Dict):
        """Update risk management settings"""
        for key, value in new_settings.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def get_settings(self) -> Dict:
        """Get current risk management settings"""
        return {
            'max_loss_per_trade': self.max_loss_per_trade,
            'max_daily_loss': self.max_daily_loss,
            'max_portfolio_risk': self.max_portfolio_risk,
            'max_positions_per_symbol': self.max_positions_per_symbol,
            'max_total_positions': self.max_total_positions,
            'stop_loss_percent': self.stop_loss_percent,
            'take_profit_percent': self.take_profit_percent,
            'position_size_percent': self.position_size_percent,
            'enabled': self.enabled
        }

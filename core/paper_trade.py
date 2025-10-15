import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid
import json
import os

class PaperTradingEngine:
    def __init__(self):
        self.portfolio_value = 100000  # Starting with ₹1 lakh
        self.available_balance = 100000
        self.positions = []
        self.trade_history = []
        self.daily_pnl = 0
        self.total_pnl = 0
        
        # Auto trading settings
        self.auto_paper_trade = True
        self.max_daily_trades = 5
        self.trades_today = 0
        
        # Load existing data
        self.load_portfolio_data()
        
    def load_portfolio_data(self):
        """Load existing portfolio data if available"""
        try:
            if os.path.exists('data/portfolio.json'):
                with open('data/portfolio.json', 'r') as f:
                    data = json.load(f)
                    self.portfolio_value = data.get('portfolio_value', 100000)
                    self.available_balance = data.get('available_balance', 100000)
                    self.total_pnl = data.get('total_pnl', 0)
                    
            if os.path.exists('data/positions.json'):
                with open('data/positions.json', 'r') as f:
                    self.positions = json.load(f)
                    
            if os.path.exists('data/trade_history.json'):
                with open('data/trade_history.json', 'r') as f:
                    self.trade_history = json.load(f)
        except Exception as e:
            print(f"Error loading portfolio data: {e}")
    
    def save_portfolio_data(self):
        """Save portfolio data to files"""
        try:
            os.makedirs('data', exist_ok=True)
            
            # Save portfolio summary
            portfolio_data = {
                'portfolio_value': self.portfolio_value,
                'available_balance': self.available_balance,
                'total_pnl': self.total_pnl,
                'last_updated': datetime.now().isoformat()
            }
            
            with open('data/portfolio.json', 'w') as f:
                json.dump(portfolio_data, f, default=str)
            
            # Save positions
            with open('data/positions.json', 'w') as f:
                json.dump(self.positions, f, default=str)
            
            # Save trade history (keep last 1000 trades)
            recent_history = self.trade_history[-1000:] if len(self.trade_history) > 1000 else self.trade_history
            with open('data/trade_history.json', 'w') as f:
                json.dump(recent_history, f, default=str)
                
        except Exception as e:
            print(f"Error saving portfolio data: {e}")
    
    def execute_trade(self, signal: Dict, trade_type: str = 'paper') -> Dict:
        """
        Execute a trade based on AI signal
        
        Parameters:
        signal: AI signal dictionary
        trade_type: 'paper' or 'live'
        
        Returns:
        Dictionary with execution result
        """
        try:
            if signal['action'] == 'BUY':
                return self.open_position(signal, trade_type)
            elif signal['action'] == 'SELL':
                return self.close_position(signal, trade_type)
            else:
                return {'success': False, 'message': 'Invalid action'}
                
        except Exception as e:
            return {'success': False, 'message': f'Trade execution error: {str(e)}'}
    
    def open_position(self, signal: Dict, trade_type: str) -> Dict:
        """Open a new position"""
        # Check if we can afford this trade
        entry_price = signal.get('price', 0)
        quantity = signal.get('quantity', 1)
        lot_size = signal.get('lot_size', 75)  # Default NIFTY lot size
        
        total_cost = entry_price * quantity * lot_size
        
        if total_cost > self.available_balance:
            return {
                'success': False, 
                'message': f'Insufficient balance. Required: ₹{total_cost:.2f}, Available: ₹{self.available_balance:.2f}'
            }
        
        # Check daily trade limit
        if self.trades_today >= self.max_daily_trades and trade_type == 'paper':
            return {
                'success': False,
                'message': f'Daily trade limit ({self.max_daily_trades}) reached'
            }
        
        # Create position
        position = {
            'id': str(uuid.uuid4()),
            'signal_id': signal.get('id'),
            'symbol': signal['symbol'],
            'strike': signal['strike'],
            'type': signal['type'],
            'action': signal['action'],
            'quantity': quantity,
            'lot_size': lot_size,
            'entry_price': entry_price,
            'current_price': entry_price,
            'entry_time': datetime.now().isoformat(),
            'trade_type': trade_type,
            'status': 'open',
            'confidence': signal['confidence'],
            'reasoning': signal['reasoning'],
            'unrealized_pnl': 0,
            'stop_loss': entry_price * 0.9,  # 10% stop loss
            'take_profit': entry_price * 1.2,  # 20% take profit
            'parameters': signal.get('parameters', {})
        }
        
        # Update balances
        self.available_balance -= total_cost
        self.positions.append(position)
        
        # Record trade
        self.record_trade(position, 'OPEN')
        
        # Update counters
        if trade_type == 'paper':
            self.trades_today += 1
        
        # Save data
        self.save_portfolio_data()
        
        return {
            'success': True,
            'message': f'Position opened successfully. Cost: ₹{total_cost:.2f}',
            'position_id': position['id'],
            'position': position
        }
    
    def close_position(self, signal: Dict, trade_type: str = None) -> Dict:
        """Close an existing position"""
        # Find matching open position
        symbol = signal['symbol']
        strike = signal['strike']
        option_type = signal['type']
        
        matching_positions = [
            p for p in self.positions 
            if (p['symbol'] == symbol and 
                p['strike'] == strike and 
                p['type'] == option_type and 
                p['status'] == 'open')
        ]
        
        if not matching_positions:
            return {
                'success': False,
                'message': f'No open position found for {symbol} {option_type} {strike}'
            }
        
        # Close the first matching position (FIFO)
        position = matching_positions[0]
        exit_price = signal.get('price', position['current_price'])
        exit_time = datetime.now()
        
        # Calculate P&L
        entry_cost = position['entry_price'] * position['quantity'] * position['lot_size']
        exit_value = exit_price * position['quantity'] * position['lot_size']
        pnl = exit_value - entry_cost
        
        # Update position
        position['exit_price'] = exit_price
        position['exit_time'] = exit_time.isoformat()
        position['realized_pnl'] = pnl
        position['status'] = 'closed'
        
        # Update balances
        self.available_balance += exit_value
        self.daily_pnl += pnl
        self.total_pnl += pnl
        
        # Calculate new portfolio value
        self.portfolio_value = self.available_balance + sum(
            p['current_price'] * p['quantity'] * p['lot_size'] 
            for p in self.positions if p['status'] == 'open'
        )
        
        # Record trade
        self.record_trade(position, 'CLOSE')
        
        # Save data
        self.save_portfolio_data()
        
        return {
            'success': True,
            'message': f'Position closed. P&L: ₹{pnl:.2f}',
            'pnl': pnl,
            'position': position
        }
    
    def update_position_prices(self, price_updates: Dict):
        """Update current prices for all open positions"""
        for position in self.positions:
            if position['status'] == 'open':
                key = f"{position['symbol']}_{position['type']}_{position['strike']}"
                
                if key in price_updates:
                    old_price = position['current_price']
                    new_price = price_updates[key]
                    position['current_price'] = new_price
                    
                    # Calculate unrealized P&L
                    entry_cost = position['entry_price'] * position['quantity'] * position['lot_size']
                    current_value = new_price * position['quantity'] * position['lot_size']
                    position['unrealized_pnl'] = current_value - entry_cost
        
        # Update portfolio value
        open_positions_value = sum(
            p['current_price'] * p['quantity'] * p['lot_size'] 
            for p in self.positions if p['status'] == 'open'
        )
        
        self.portfolio_value = self.available_balance + open_positions_value
        
        # Check for stop loss / take profit
        self.check_auto_exits()
    
    def check_auto_exits(self):
        """Check and execute automatic exits for stop loss / take profit"""
        positions_to_close = []
        
        for position in self.positions:
            if position['status'] == 'open':
                current_price = position['current_price']
                
                # Check stop loss
                if current_price <= position['stop_loss']:
                    positions_to_close.append({
                        'position': position,
                        'reason': 'stop_loss',
                        'exit_price': position['stop_loss']
                    })
                
                # Check take profit
                elif current_price >= position['take_profit']:
                    positions_to_close.append({
                        'position': position,
                        'reason': 'take_profit',
                        'exit_price': position['take_profit']
                    })
        
        # Execute auto exits
        for exit_info in positions_to_close:
            self.auto_close_position(exit_info)
    
    def auto_close_position(self, exit_info: Dict):
        """Automatically close a position"""
        position = exit_info['position']
        exit_price = exit_info['exit_price']
        reason = exit_info['reason']
        
        # Create a mock signal for closing
        close_signal = {
            'symbol': position['symbol'],
            'strike': position['strike'],
            'type': position['type'],
            'price': exit_price,
            'action': 'SELL',
            'reason': f'Auto exit: {reason}'
        }
        
        result = self.close_position(close_signal, position['trade_type'])
        
        if result['success']:
            print(f"Auto exit executed: {reason} for {position['symbol']} {position['type']} {position['strike']}")
    
    def record_trade(self, position: Dict, action: str):
        """Record trade in history"""
        trade_record = {
            'id': str(uuid.uuid4()),
            'position_id': position['id'],
            'symbol': position['symbol'],
            'strike': position['strike'],
            'type': position['type'],
            'action': action,
            'quantity': position['quantity'],
            'price': position['entry_price'] if action == 'OPEN' else position.get('exit_price'),
            'timestamp': datetime.now().isoformat(),
            'trade_type': position['trade_type'],
            'confidence': position.get('confidence', 0),
            'reasoning': position.get('reasoning', ''),
            'pnl': position.get('realized_pnl', 0) if action == 'CLOSE' else 0
        }
        
        self.trade_history.append(trade_record)
    
    def get_portfolio_value(self) -> float:
        """Get current portfolio value"""
        return self.portfolio_value
    
    def get_daily_pnl(self) -> float:
        """Get today's P&L"""
        # Calculate P&L for trades closed today
        today = datetime.now().date()
        today_trades = [
            t for t in self.trade_history 
            if (datetime.fromisoformat(t['timestamp']).date() == today and 
                t['action'] == 'CLOSE')
        ]
        
        return sum(t['pnl'] for t in today_trades)
    
    def get_current_positions(self) -> List[Dict]:
        """Get all open positions with current P&L"""
        open_positions = [p for p in self.positions if p['status'] == 'open']
        
        # Add current P&L calculation
        for position in open_positions:
            entry_cost = position['entry_price'] * position['quantity'] * position['lot_size']
            current_value = position['current_price'] * position['quantity'] * position['lot_size']
            position['pnl'] = current_value - entry_cost
        
        return open_positions
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary"""
        closed_positions = [p for p in self.positions if p['status'] == 'closed']
        
        if not closed_positions:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': self.total_pnl,
                'average_win': 0,
                'average_loss': 0,
                'profit_factor': 0,
                'max_win': 0,
                'max_loss': 0
            }
        
        winning_trades = [p for p in closed_positions if p['realized_pnl'] > 0]
        losing_trades = [p for p in closed_positions if p['realized_pnl'] < 0]
        
        total_wins = sum(p['realized_pnl'] for p in winning_trades)
        total_losses = abs(sum(p['realized_pnl'] for p in losing_trades))
        
        return {
            'total_trades': len(closed_positions),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': (len(winning_trades) / len(closed_positions)) * 100 if closed_positions else 0,
            'total_pnl': self.total_pnl,
            'average_win': total_wins / len(winning_trades) if winning_trades else 0,
            'average_loss': total_losses / len(losing_trades) if losing_trades else 0,
            'profit_factor': total_wins / total_losses if total_losses > 0 else float('inf'),
            'max_win': max(p['realized_pnl'] for p in winning_trades) if winning_trades else 0,
            'max_loss': min(p['realized_pnl'] for p in losing_trades) if losing_trades else 0
        }
    
    def auto_paper_trade_top_movers(self, market_data, signal_engine):
        """Automatically paper trade top gainers and losers"""
        if not self.auto_paper_trade or self.trades_today >= self.max_daily_trades:
            return
        
        try:
            # Get top movers
            top_movers = market_data.get_top_gainers_losers()
            
            # Generate signals for top movers
            symbols_to_trade = ['NIFTY', 'BANKNIFTY', 'FINNIFTY']
            
            for symbol in symbols_to_trade:
                if self.trades_today >= self.max_daily_trades:
                    break
                
                # Get option chain
                expiry_dates = market_data.get_expiry_dates(symbol)
                if expiry_dates:
                    option_chain = market_data.get_option_chain(symbol, expiry_dates[0])
                    underlying_price = market_data.get_live_price(symbol).get('ltp', 0)
                    
                    if not option_chain.empty and underlying_price > 0:
                        signals = signal_engine.generate_signals(
                            symbol, option_chain, underlying_price, {}
                        )
                        
                        # Execute the best signal
                        if signals:
                            best_signal = signals[0]  # Highest confidence
                            if best_signal['confidence'] > 75:  # Only high confidence signals
                                result = self.execute_trade(best_signal, 'paper')
                                if result['success']:
                                    print(f"Auto paper trade executed: {symbol} {best_signal['type']} {best_signal['strike']}")
                                    
        except Exception as e:
            print(f"Auto paper trading error: {e}")
    
    def reset_daily_counters(self):
        """Reset daily counters (call this at market open)"""
        self.trades_today = 0
        self.daily_pnl = 0

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os
import sqlite3

class TradeJournal:
    def __init__(self):
        self.db_path = 'data/trades.db'
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database for trade journal"""
        os.makedirs('data', exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create trades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id TEXT PRIMARY KEY,
                position_id TEXT,
                symbol TEXT NOT NULL,
                strike REAL NOT NULL,
                option_type TEXT NOT NULL,
                trade_type TEXT NOT NULL,
                action TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                entry_price REAL,
                exit_price REAL,
                entry_time TIMESTAMP,
                exit_time TIMESTAMP,
                pnl REAL DEFAULT 0,
                confidence REAL,
                reasoning TEXT,
                ai_signal_id TEXT,
                parameters TEXT,
                status TEXT DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create performance metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                total_pnl REAL DEFAULT 0,
                win_rate REAL DEFAULT 0,
                profit_factor REAL DEFAULT 0,
                max_drawdown REAL DEFAULT 0,
                sharpe_ratio REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date)
            )
        ''')
        
        # Create AI learning table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_learning (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id TEXT NOT NULL,
                predicted_confidence REAL,
                actual_outcome TEXT,
                actual_pnl REAL,
                parameters TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                symbol TEXT,
                action TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_trade_entry(self, trade_data: Dict) -> bool:
        """Log a new trade entry"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trades (
                    id, position_id, symbol, strike, option_type, trade_type,
                    action, quantity, entry_price, entry_time, confidence,
                    reasoning, ai_signal_id, parameters, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade_data.get('id'),
                trade_data.get('position_id'),
                trade_data.get('symbol'),
                trade_data.get('strike'),
                trade_data.get('type'),
                trade_data.get('trade_type', 'paper'),
                'ENTRY',
                trade_data.get('quantity', 1),
                trade_data.get('entry_price'),
                trade_data.get('entry_time', datetime.now().isoformat()),
                trade_data.get('confidence', 0),
                trade_data.get('reasoning', ''),
                trade_data.get('signal_id'),
                json.dumps(trade_data.get('parameters', {})),
                'open'
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error logging trade entry: {e}")
            return False
    
    def log_trade_exit(self, trade_data: Dict) -> bool:
        """Log a trade exit"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update existing trade record
            cursor.execute('''
                UPDATE trades SET
                    exit_price = ?,
                    exit_time = ?,
                    pnl = ?,
                    status = 'closed',
                    updated_at = CURRENT_TIMESTAMP
                WHERE position_id = ? AND status = 'open'
            ''', (
                trade_data.get('exit_price'),
                trade_data.get('exit_time', datetime.now().isoformat()),
                trade_data.get('pnl', 0),
                trade_data.get('position_id')
            ))
            
            # Also insert exit record
            cursor.execute('''
                INSERT INTO trades (
                    id, position_id, symbol, strike, option_type, trade_type,
                    action, quantity, exit_price, exit_time, pnl, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                f"{trade_data.get('position_id')}_exit",
                trade_data.get('position_id'),
                trade_data.get('symbol'),
                trade_data.get('strike'),
                trade_data.get('type'),
                trade_data.get('trade_type', 'paper'),
                'EXIT',
                trade_data.get('quantity', 1),
                trade_data.get('exit_price'),
                trade_data.get('exit_time', datetime.now().isoformat()),
                trade_data.get('pnl', 0),
                'closed'
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error logging trade exit: {e}")
            return False
    
    def get_trade_history(self, days: int = 30, symbol: str = None, trade_type: str = None) -> pd.DataFrame:
        """Get trade history as DataFrame"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = '''
                SELECT * FROM trades 
                WHERE entry_time >= date('now', '-{} days')
                AND action = 'ENTRY'
            '''.format(days)
            
            params = []
            
            if symbol:
                query += ' AND symbol = ?'
                params.append(symbol)
            
            if trade_type:
                query += ' AND trade_type = ?'
                params.append(trade_type)
            
            query += ' ORDER BY entry_time DESC'
            
            df = pd.read_sql_query(query, conn, params=params)
            
            if not df.empty:
                df['entry_time'] = pd.to_datetime(df['entry_time'])
                df['exit_time'] = pd.to_datetime(df['exit_time'])
                
                # Parse parameters JSON
                df['parameters'] = df['parameters'].apply(
                    lambda x: json.loads(x) if x and x != '{}' else {}
                )
            
            conn.close()
            return df
            
        except Exception as e:
            print(f"Error fetching trade history: {e}")
            return pd.DataFrame()
    
    def get_total_trades(self) -> int:
        """Get total number of trades"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM trades WHERE action = "ENTRY"')
            result = cursor.fetchone()
            
            conn.close()
            return result[0] if result else 0
            
        except Exception as e:
            print(f"Error getting total trades: {e}")
            return 0
    
    def get_win_rate(self) -> float:
        """Calculate win rate percentage"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get winning trades
            cursor.execute('SELECT COUNT(*) FROM trades WHERE action = "ENTRY" AND pnl > 0')
            winning_trades = cursor.fetchone()[0]
            
            # Get total closed trades
            cursor.execute('SELECT COUNT(*) FROM trades WHERE action = "ENTRY" AND status = "closed"')
            total_trades = cursor.fetchone()[0]
            
            conn.close()
            
            return (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
            
        except Exception as e:
            print(f"Error calculating win rate: {e}")
            return 0.0
    
    def get_max_drawdown(self) -> float:
        """Calculate maximum drawdown"""
        try:
            df = self.get_trade_history(days=365)  # Get full year data
            
            if df.empty:
                return 0.0
            
            # Calculate cumulative P&L
            df_sorted = df.sort_values('entry_time')
            df_sorted['cumulative_pnl'] = df_sorted['pnl'].cumsum()
            
            # Calculate running maximum
            df_sorted['running_max'] = df_sorted['cumulative_pnl'].expanding().max()
            
            # Calculate drawdown
            df_sorted['drawdown'] = df_sorted['cumulative_pnl'] - df_sorted['running_max']
            
            # Return maximum drawdown (most negative value)
            return df_sorted['drawdown'].min()
            
        except Exception as e:
            print(f"Error calculating max drawdown: {e}")
            return 0.0
    
    def get_daily_performance(self, days: int = 30) -> pd.DataFrame:
        """Get daily performance metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = '''
                SELECT 
                    DATE(entry_time) as trade_date,
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                    SUM(pnl) as daily_pnl,
                    AVG(confidence) as avg_confidence
                FROM trades 
                WHERE action = 'ENTRY' 
                AND entry_time >= date('now', '-{} days')
                AND status = 'closed'
                GROUP BY DATE(entry_time)
                ORDER BY trade_date DESC
            '''.format(days)
            
            df = pd.read_sql_query(query, conn)
            
            if not df.empty:
                df['trade_date'] = pd.to_datetime(df['trade_date'])
                df['win_rate'] = (df['winning_trades'] / df['total_trades'] * 100).round(2)
                df['profit_factor'] = np.where(
                    df['losing_trades'] > 0,
                    abs(df[df['daily_pnl'] > 0]['daily_pnl'].sum()) / abs(df[df['daily_pnl'] < 0]['daily_pnl'].sum()),
                    np.inf
                )
            
            conn.close()
            return df
            
        except Exception as e:
            print(f"Error getting daily performance: {e}")
            return pd.DataFrame()
    
    def get_symbol_performance(self) -> pd.DataFrame:
        """Get performance by symbol"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = '''
                SELECT 
                    symbol,
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(pnl) as total_pnl,
                    AVG(pnl) as avg_pnl,
                    MAX(pnl) as best_trade,
                    MIN(pnl) as worst_trade,
                    AVG(confidence) as avg_confidence
                FROM trades 
                WHERE action = 'ENTRY' AND status = 'closed'
                GROUP BY symbol
                ORDER BY total_pnl DESC
            '''
            
            df = pd.read_sql_query(query, conn)
            
            if not df.empty:
                df['win_rate'] = (df['winning_trades'] / df['total_trades'] * 100).round(2)
            
            conn.close()
            return df
            
        except Exception as e:
            print(f"Error getting symbol performance: {e}")
            return pd.DataFrame()
    
    def get_trade_analysis(self) -> Dict:
        """Get comprehensive trade analysis"""
        try:
            df = self.get_trade_history(days=365)
            
            if df.empty:
                return {}
            
            closed_trades = df[df['status'] == 'closed']
            
            if closed_trades.empty:
                return {}
            
            analysis = {
                'total_trades': len(closed_trades),
                'winning_trades': len(closed_trades[closed_trades['pnl'] > 0]),
                'losing_trades': len(closed_trades[closed_trades['pnl'] < 0]),
                'breakeven_trades': len(closed_trades[closed_trades['pnl'] == 0]),
                'total_pnl': closed_trades['pnl'].sum(),
                'average_pnl': closed_trades['pnl'].mean(),
                'win_rate': (len(closed_trades[closed_trades['pnl'] > 0]) / len(closed_trades)) * 100,
                'best_trade': closed_trades['pnl'].max(),
                'worst_trade': closed_trades['pnl'].min(),
                'average_winner': closed_trades[closed_trades['pnl'] > 0]['pnl'].mean() if len(closed_trades[closed_trades['pnl'] > 0]) > 0 else 0,
                'average_loser': closed_trades[closed_trades['pnl'] < 0]['pnl'].mean() if len(closed_trades[closed_trades['pnl'] < 0]) > 0 else 0,
                'largest_winning_streak': self._calculate_largest_streak(closed_trades, 'win'),
                'largest_losing_streak': self._calculate_largest_streak(closed_trades, 'loss'),
                'avg_confidence': closed_trades['confidence'].mean(),
                'max_drawdown': self.get_max_drawdown()
            }
            
            # Calculate profit factor
            total_wins = closed_trades[closed_trades['pnl'] > 0]['pnl'].sum()
            total_losses = abs(closed_trades[closed_trades['pnl'] < 0]['pnl'].sum())
            analysis['profit_factor'] = total_wins / total_losses if total_losses > 0 else float('inf')
            
            # Calculate Sharpe ratio (simplified)
            if closed_trades['pnl'].std() > 0:
                analysis['sharpe_ratio'] = closed_trades['pnl'].mean() / closed_trades['pnl'].std()
            else:
                analysis['sharpe_ratio'] = 0
            
            return analysis
            
        except Exception as e:
            print(f"Error in trade analysis: {e}")
            return {}
    
    def _calculate_largest_streak(self, df: pd.DataFrame, streak_type: str) -> int:
        """Calculate largest winning/losing streak"""
        if df.empty:
            return 0
        
        df_sorted = df.sort_values('entry_time')
        
        if streak_type == 'win':
            wins = (df_sorted['pnl'] > 0).astype(int)
        else:
            wins = (df_sorted['pnl'] < 0).astype(int)
        
        # Find consecutive streaks
        streaks = []
        current_streak = 0
        
        for win in wins:
            if win:
                current_streak += 1
            else:
                if current_streak > 0:
                    streaks.append(current_streak)
                current_streak = 0
        
        if current_streak > 0:
            streaks.append(current_streak)
        
        return max(streaks) if streaks else 0
    
    def log_ai_learning(self, signal_id: str, predicted_confidence: float, 
                       actual_outcome: str, actual_pnl: float, parameters: Dict,
                       symbol: str, action: str) -> bool:
        """Log AI learning data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO ai_learning (
                    signal_id, predicted_confidence, actual_outcome,
                    actual_pnl, parameters, symbol, action
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                signal_id,
                predicted_confidence,
                actual_outcome,
                actual_pnl,
                json.dumps(parameters),
                symbol,
                action
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error logging AI learning data: {e}")
            return False
    
    def get_ai_learning_data(self) -> pd.DataFrame:
        """Get AI learning data for model training"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            df = pd.read_sql_query('''
                SELECT * FROM ai_learning
                ORDER BY timestamp DESC
                LIMIT 1000
            ''', conn)
            
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['parameters'] = df['parameters'].apply(
                    lambda x: json.loads(x) if x else {}
                )
            
            conn.close()
            return df
            
        except Exception as e:
            print(f"Error getting AI learning data: {e}")
            return pd.DataFrame()
    
    def cleanup_old_data(self, days: int = 365):
        """Clean up old data beyond specified days"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Delete old trades
            cursor.execute('''
                DELETE FROM trades 
                WHERE entry_time < date('now', '-{} days')
            '''.format(days))
            
            # Delete old AI learning data
            cursor.execute('''
                DELETE FROM ai_learning 
                WHERE timestamp < date('now', '-{} days')
            '''.format(days))
            
            conn.commit()
            conn.close()
            
            print(f"Cleaned up data older than {days} days")
            return True
            
        except Exception as e:
            print(f"Error cleaning up old data: {e}")
            return False
    
    def export_trades_csv(self, filename: str = None) -> str:
        """Export trade history to CSV"""
        try:
            df = self.get_trade_history(days=365)
            
            if df.empty:
                return None
            
            if not filename:
                filename = f"trades_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            filepath = os.path.join('data', filename)
            df.to_csv(filepath, index=False)
            
            return filepath
            
        except Exception as e:
            print(f"Error exporting trades to CSV: {e}")
            return None

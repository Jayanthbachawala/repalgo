import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import re
import json

def format_currency(amount: float, symbol: str = "₹") -> str:
    """Format currency with Indian rupee symbol and proper formatting"""
    if pd.isna(amount) or amount is None:
        return f"{symbol}0.00"
    
    if abs(amount) >= 10000000:  # 1 crore
        return f"{symbol}{amount/10000000:.2f}Cr"
    elif abs(amount) >= 100000:  # 1 lakh
        return f"{symbol}{amount/100000:.2f}L"
    else:
        return f"{symbol}{amount:,.2f}"

def format_percentage(value: float, decimals: int = 2) -> str:
    """Format percentage with proper sign and decimals"""
    if pd.isna(value) or value is None:
        return "0.00%"
    
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.{decimals}f}%"

def format_number(number: Union[int, float], decimals: int = 0) -> str:
    """Format numbers with Indian number system (lakhs, crores)"""
    if pd.isna(number) or number is None:
        return "0"
    
    if abs(number) >= 10000000:  # 1 crore
        return f"{number/10000000:.1f}Cr"
    elif abs(number) >= 100000:  # 1 lakh
        return f"{number/100000:.1f}L"
    elif abs(number) >= 1000:  # 1 thousand
        return f"{number/1000:.1f}K"
    else:
        return f"{number:.{decimals}f}"

def get_color_for_pnl(pnl: float) -> str:
    """Get color code for P&L display"""
    if pd.isna(pnl) or pnl == 0:
        return "gray"
    elif pnl > 0:
        return "green"
    else:
        return "red"

def get_color_for_change(change: float) -> str:
    """Get color code for price change"""
    if pd.isna(change) or change == 0:
        return "gray"
    elif change > 0:
        return "#00C851"  # Green
    else:
        return "#FF4444"  # Red

def calculate_strike_distance(underlying_price: float, strike: float) -> float:
    """Calculate distance of strike from underlying price"""
    if underlying_price == 0:
        return 0
    return ((strike - underlying_price) / underlying_price) * 100

def get_option_moneyness(underlying_price: float, strike: float, option_type: str) -> str:
    """Determine if option is ITM, ATM, or OTM"""
    if option_type.upper() in ['CE', 'CALL']:
        if underlying_price > strike:
            return "ITM"
        elif abs(underlying_price - strike) < 50:  # Within 50 points
            return "ATM"
        else:
            return "OTM"
    else:  # PUT
        if underlying_price < strike:
            return "ITM"
        elif abs(underlying_price - strike) < 50:
            return "ATM"
        else:
            return "OTM"

def calculate_breakeven(strike: float, premium: float, option_type: str) -> float:
    """Calculate breakeven point for option"""
    if option_type.upper() in ['CE', 'CALL']:
        return strike + premium
    else:  # PUT
        return strike - premium

def time_until_expiry(expiry_date: str) -> Dict[str, int]:
    """Calculate time until expiry in days, hours, minutes"""
    try:
        if isinstance(expiry_date, str):
            expiry = datetime.strptime(expiry_date, "%Y-%m-%d")
        else:
            expiry = expiry_date
        
        # Set expiry time to 3:30 PM
        expiry = expiry.replace(hour=15, minute=30, second=0, microsecond=0)
        
        now = datetime.now()
        time_diff = expiry - now
        
        if time_diff.total_seconds() <= 0:
            return {"days": 0, "hours": 0, "minutes": 0, "expired": True}
        
        days = time_diff.days
        hours, remainder = divmod(time_diff.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        return {"days": days, "hours": hours, "minutes": minutes, "expired": False}
        
    except Exception as e:
        return {"days": 0, "hours": 0, "minutes": 0, "expired": True}

def format_time_until_expiry(expiry_date: str) -> str:
    """Format time until expiry as human readable string"""
    time_info = time_until_expiry(expiry_date)
    
    if time_info["expired"]:
        return "Expired"
    
    if time_info["days"] > 0:
        return f"{time_info['days']}d {time_info['hours']}h"
    elif time_info["hours"] > 0:
        return f"{time_info['hours']}h {time_info['minutes']}m"
    else:
        return f"{time_info['minutes']}m"

def validate_strike_price(strike: float, underlying_price: float) -> bool:
    """Validate if strike price is reasonable"""
    if strike <= 0 or underlying_price <= 0:
        return False
    
    # Strike should be within reasonable range (50% to 150% of underlying)
    ratio = strike / underlying_price
    return 0.5 <= ratio <= 1.5

def calculate_option_value_at_expiry(underlying_price: float, strike: float, option_type: str) -> float:
    """Calculate intrinsic value of option at expiry"""
    if option_type.upper() in ['CE', 'CALL']:
        return max(0, underlying_price - strike)
    else:  # PUT
        return max(0, strike - underlying_price)

def get_next_expiry_date(current_date: datetime = None) -> str:
    """Get next Thursday (weekly expiry) date"""
    if current_date is None:
        current_date = datetime.now()
    
    # Find next Thursday
    days_ahead = 3 - current_date.weekday()  # Thursday is 3
    if days_ahead <= 0:  # Today is Thursday or later in week
        days_ahead += 7
    
    next_thursday = current_date + timedelta(days=days_ahead)
    return next_thursday.strftime("%Y-%m-%d")

def get_monthly_expiry_date(year: int, month: int) -> str:
    """Get last Thursday of the month (monthly expiry)"""
    # Last day of the month
    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)
    
    # Find last Thursday
    while last_day.weekday() != 3:  # Thursday is 3
        last_day -= timedelta(days=1)
    
    return last_day.strftime("%Y-%m-%d")

def calculate_portfolio_greeks(positions: List[Dict]) -> Dict[str, float]:
    """Calculate portfolio-level Greeks from individual positions"""
    portfolio_greeks = {
        'delta': 0,
        'gamma': 0,
        'theta': 0,
        'vega': 0,
        'rho': 0
    }
    
    for position in positions:
        quantity = position.get('quantity', 0)
        lot_size = position.get('lot_size', 75)
        total_quantity = quantity * lot_size
        
        # Multiply Greeks by position size
        portfolio_greeks['delta'] += position.get('delta', 0) * total_quantity
        portfolio_greeks['gamma'] += position.get('gamma', 0) * total_quantity
        portfolio_greeks['theta'] += position.get('theta', 0) * total_quantity
        portfolio_greeks['vega'] += position.get('vega', 0) * total_quantity
        portfolio_greeks['rho'] += position.get('rho', 0) * total_quantity
    
    return portfolio_greeks

def clean_text(text: str, max_length: int = 100) -> str:
    """Clean and truncate text for display"""
    if not text:
        return ""
    
    # Remove extra whitespace
    cleaned = re.sub(r'\s+', ' ', text.strip())
    
    # Truncate if too long
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length-3] + "..."
    
    return cleaned

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if division by zero"""
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return default

def parse_json_safely(json_string: str, default: Dict = None) -> Dict:
    """Safely parse JSON string, returning default on error"""
    if default is None:
        default = {}
    
    try:
        if not json_string or json_string == "{}":
            return default
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return default

def get_trading_session() -> str:
    """Get current trading session"""
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    current_time = hour * 100 + minute
    
    # Pre-market: 9:00 - 9:15
    if 900 <= current_time < 915:
        return "Pre-Market"
    # Regular session: 9:15 - 15:30
    elif 915 <= current_time <= 1530:
        return "Regular"
    # After market: 15:30 - 16:00
    elif 1530 < current_time <= 1600:
        return "After-Market"
    else:
        return "Closed"

def is_market_open() -> bool:
    """Check if market is currently open"""
    now = datetime.now()
    
    # Check if it's a weekday (Monday=0 to Friday=4)
    if now.weekday() >= 5:  # Weekend
        return False
    
    # Check time (9:15 AM to 3:30 PM)
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    return market_open <= now <= market_close

def calculate_days_to_expiry(expiry_date: str) -> float:
    """Calculate days to expiry as decimal for option pricing"""
    try:
        if isinstance(expiry_date, str):
            expiry = datetime.strptime(expiry_date, "%Y-%m-%d")
        else:
            expiry = expiry_date
        
        # Set expiry time to 3:30 PM
        expiry = expiry.replace(hour=15, minute=30, second=0, microsecond=0)
        
        now = datetime.now()
        time_diff = expiry - now
        
        # Return days as decimal (including fractional day)
        return max(0, time_diff.total_seconds() / (24 * 3600))
        
    except Exception:
        return 0

def get_lot_size(symbol: str) -> int:
    """Get lot size for different symbols"""
    lot_sizes = {
        'NIFTY': 75,
        'BANKNIFTY': 15,
        'FINNIFTY': 40,
        'SENSEX': 10,
        'RELIANCE': 250,
        'TCS': 150,
        'HDFCBANK': 550,
        'INFY': 300,
        'HINDUNILVR': 300
    }
    
    return lot_sizes.get(symbol.upper(), 75)  # Default to NIFTY lot size

def format_strike_price(strike: float) -> str:
    """Format strike price for display"""
    if strike >= 10000:
        return f"{strike:,.0f}"
    else:
        return f"{strike:.0f}"

def calculate_premium_decay(days_to_expiry: float, theta: float) -> float:
    """Calculate expected premium decay over time"""
    if days_to_expiry <= 0:
        return 0
    
    # Theta is daily decay, so multiply by days
    return theta * days_to_expiry

def get_volatility_percentile(current_iv: float, symbol: str) -> str:
    """Get volatility percentile description"""
    # These would typically come from historical data
    volatility_ranges = {
        'NIFTY': {'low': 12, 'high': 25},
        'BANKNIFTY': {'low': 15, 'high': 30},
        'FINNIFTY': {'low': 14, 'high': 28},
        'SENSEX': {'low': 11, 'high': 24}
    }
    
    ranges = volatility_ranges.get(symbol, {'low': 12, 'high': 25})
    
    if current_iv < ranges['low']:
        return "Very Low"
    elif current_iv < (ranges['low'] + ranges['high']) / 2:
        return "Low"
    elif current_iv < ranges['high']:
        return "High"
    else:
        return "Very High"

def validate_option_data(option_data: Dict) -> bool:
    """Validate option data completeness"""
    required_fields = ['strike', 'ltp', 'type']
    
    for field in required_fields:
        if field not in option_data or option_data[field] is None:
            return False
    
    # Check if values are reasonable
    if option_data['ltp'] < 0 or option_data['strike'] <= 0:
        return False
    
    return True

def get_signal_strength(confidence: float) -> str:
    """Convert confidence score to signal strength description"""
    if confidence >= 85:
        return "Very Strong"
    elif confidence >= 75:
        return "Strong"
    elif confidence >= 65:
        return "Moderate"
    elif confidence >= 55:
        return "Weak"
    else:
        return "Very Weak"

def calculate_risk_reward_ratio(entry_price: float, stop_loss: float, target_price: float) -> float:
    """Calculate risk-reward ratio"""
    if entry_price == 0 or stop_loss == entry_price:
        return 0
    
    risk = abs(entry_price - stop_loss)
    reward = abs(target_price - entry_price)
    
    return safe_divide(reward, risk, 0)

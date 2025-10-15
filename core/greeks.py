import numpy as np
import pandas as pd
from scipy.stats import norm
from datetime import datetime, timedelta
import math

class GreeksCalculator:
    def __init__(self):
        self.risk_free_rate = 0.06  # 6% risk-free rate
        
    def black_scholes_price(self, S, K, T, r, sigma, option_type='call'):
        """
        Calculate Black-Scholes option price
        
        Parameters:
        S: Current stock price
        K: Strike price
        T: Time to expiration (in years)
        r: Risk-free rate
        sigma: Volatility
        option_type: 'call' or 'put'
        """
        if T <= 0:
            if option_type == 'call':
                return max(0, S - K)
            else:
                return max(0, K - S)
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if option_type == 'call':
            price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        
        return max(0, price)
    
    def calculate_delta(self, S, K, T, r, sigma, option_type='call'):
        """Calculate Delta - price sensitivity to underlying price change"""
        if T <= 0:
            if option_type == 'call':
                return 1 if S > K else 0
            else:
                return -1 if S < K else 0
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        
        if option_type == 'call':
            return norm.cdf(d1)
        else:
            return -norm.cdf(-d1)
    
    def calculate_gamma(self, S, K, T, r, sigma):
        """Calculate Gamma - rate of change of Delta"""
        if T <= 0:
            return 0
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        return norm.pdf(d1) / (S * sigma * np.sqrt(T))
    
    def calculate_theta(self, S, K, T, r, sigma, option_type='call'):
        """Calculate Theta - time decay"""
        if T <= 0:
            return 0
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        theta1 = (-S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
        
        if option_type == 'call':
            theta2 = r * K * np.exp(-r * T) * norm.cdf(d2)
            theta = (theta1 - theta2) / 365  # Convert to daily theta
        else:
            theta2 = r * K * np.exp(-r * T) * norm.cdf(-d2)
            theta = (theta1 + theta2) / 365  # Convert to daily theta
        
        return theta
    
    def calculate_vega(self, S, K, T, r, sigma):
        """Calculate Vega - sensitivity to volatility"""
        if T <= 0:
            return 0
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        return S * norm.pdf(d1) * np.sqrt(T) / 100  # Divide by 100 for 1% vol change
    
    def calculate_rho(self, S, K, T, r, sigma, option_type='call'):
        """Calculate Rho - sensitivity to interest rate"""
        if T <= 0:
            return 0
        
        d2 = (np.log(S / K) + (r - 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        
        if option_type == 'call':
            return K * T * np.exp(-r * T) * norm.cdf(d2) / 100
        else:
            return -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100
    
    def calculate_implied_volatility(self, market_price, S, K, T, r, option_type='call', 
                                   max_iterations=100, tolerance=1e-6):
        """Calculate implied volatility using Newton-Raphson method"""
        if T <= 0:
            return 0
        
        # Initial guess
        sigma = 0.3
        
        for i in range(max_iterations):
            # Calculate price and vega with current sigma
            price = self.black_scholes_price(S, K, T, r, sigma, option_type)
            vega = self.calculate_vega(S, K, T, r, sigma) * 100  # Convert back for calculation
            
            # Check convergence
            price_diff = price - market_price
            if abs(price_diff) < tolerance:
                return sigma
            
            # Newton-Raphson update
            if vega != 0:
                sigma = sigma - price_diff / vega
                sigma = max(0.01, min(5.0, sigma))  # Keep sigma within reasonable bounds
            else:
                break
        
        return sigma
    
    def get_time_to_expiry(self, expiry_date):
        """Calculate time to expiry in years"""
        if isinstance(expiry_date, str):
            expiry = datetime.strptime(expiry_date, "%Y-%m-%d")
        else:
            expiry = expiry_date
        
        now = datetime.now()
        time_diff = expiry - now
        
        # Convert to years (assuming 365 days per year)
        return max(0, time_diff.total_seconds() / (365 * 24 * 3600))
    
    def calculate_all_greeks(self, option_data, underlying_price, expiry_date):
        """
        Calculate all Greeks for option data
        
        Parameters:
        option_data: DataFrame with option information
        underlying_price: Current underlying asset price
        expiry_date: Option expiry date
        """
        if option_data.empty:
            return option_data
        
        # Calculate time to expiry
        T = self.get_time_to_expiry(expiry_date)
        
        greeks_data = []
        
        for _, option in option_data.iterrows():
            K = option['strike']
            market_price = option['ltp']
            option_type = 'call' if option['type'] == 'CE' else 'put'
            
            # Calculate implied volatility first
            if market_price > 0 and T > 0:
                iv = self.calculate_implied_volatility(
                    market_price, underlying_price, K, T, 
                    self.risk_free_rate, option_type
                )
            else:
                iv = 0.3  # Default volatility
            
            # Calculate all Greeks
            delta = self.calculate_delta(underlying_price, K, T, self.risk_free_rate, iv, option_type)
            gamma = self.calculate_gamma(underlying_price, K, T, self.risk_free_rate, iv)
            theta = self.calculate_theta(underlying_price, K, T, self.risk_free_rate, iv, option_type)
            vega = self.calculate_vega(underlying_price, K, T, self.risk_free_rate, iv)
            rho = self.calculate_rho(underlying_price, K, T, self.risk_free_rate, iv, option_type)
            
            # Theoretical price using Black-Scholes
            theoretical_price = self.black_scholes_price(
                underlying_price, K, T, self.risk_free_rate, iv, option_type
            )
            
            greeks_data.append({
                'strike': K,
                'type': option['type'],
                'ltp': market_price,
                'theoretical_price': theoretical_price,
                'delta': delta,
                'gamma': gamma,
                'theta': theta,
                'vega': vega,
                'rho': rho,
                'iv': iv * 100,  # Convert to percentage
                'volume': option.get('volume', 0),
                'oi': option.get('oi', 0),
                'oi_change': option.get('oi_change', 0),
                'bid': option.get('bid', 0),
                'ask': option.get('ask', 0)
            })
        
        return pd.DataFrame(greeks_data)
    
    def calculate_portfolio_greeks(self, positions):
        """Calculate portfolio-level Greeks"""
        if not positions:
            return {
                'portfolio_delta': 0,
                'portfolio_gamma': 0,
                'portfolio_theta': 0,
                'portfolio_vega': 0,
                'portfolio_rho': 0
            }
        
        portfolio_delta = sum(pos['quantity'] * pos['delta'] for pos in positions)
        portfolio_gamma = sum(pos['quantity'] * pos['gamma'] for pos in positions)
        portfolio_theta = sum(pos['quantity'] * pos['theta'] for pos in positions)
        portfolio_vega = sum(pos['quantity'] * pos['vega'] for pos in positions)
        portfolio_rho = sum(pos['quantity'] * pos['rho'] for pos in positions)
        
        return {
            'portfolio_delta': portfolio_delta,
            'portfolio_gamma': portfolio_gamma,
            'portfolio_theta': portfolio_theta,
            'portfolio_vega': portfolio_vega,
            'portfolio_rho': portfolio_rho
        }
    
    def get_greeks_explanation(self, greek_name):
        """Get explanation of what each Greek represents"""
        explanations = {
            'delta': "Delta measures how much the option price changes for every ₹1 change in the underlying asset price. Range: 0 to 1 for calls, -1 to 0 for puts.",
            'gamma': "Gamma measures the rate of change of Delta. Higher Gamma means Delta changes more rapidly with underlying price movements.",
            'theta': "Theta measures time decay - how much option value decreases each day, all else being equal. Always negative for long options.",
            'vega': "Vega measures sensitivity to volatility changes. Higher Vega means option price is more sensitive to volatility changes.",
            'rho': "Rho measures sensitivity to interest rate changes. Generally less important for short-term options.",
            'iv': "Implied Volatility represents the market's expectation of future volatility. Higher IV generally means higher option prices."
        }
        
        return explanations.get(greek_name.lower(), "Greek explanation not available.")

# AI Options Trader Agent

## Overview

An AI-powered options trading platform for Indian markets with 75+ stocks and 4 indices. Features intelligent signal generation, paper trading for AI learning, and live trading via OpenAlgo (20+ broker support). The AI uses Gradient Boosting and pattern recognition to analyze Delta, OI, Volume, IV, Spread, and Liquidity, continuously learning from outcomes to improve accuracy.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Updates (Oct 2024)

### Stock Trading Enhancement
- **Expanded Coverage**: 75+ stocks added (RELIANCE, TCS, HDFCBANK, INFY, ZOMATO, PAYTM, etc.)
- **Stock Fundamentals**: P/E Ratio, Market Cap, Delivery%, OI, OI Change tracking
- **Option Chain**: Full option chains for all stocks with 21 strikes per symbol

### UI/UX Improvements
- **Modern Design**: High-tech gradient UI with Orbitron/Rajdhani fonts, glassmorphism effects
- **Interactive Charts**: 4 chart styles (Candlestick/Line/Area/OHLC), 5 timeframes (1min-1day)
- **Asset Selector**: Switch between Indices and Stocks across Dashboard and Option Chain

### AI Enhancement
- **Dual Models**: Gradient Boosting (200 estimators) + Pattern Recognition (Random Forest 150)
- **Adaptive Learning**: Dynamic weight optimization based on historical performance
- **Improved Accuracy**: Weighted confidence scoring, train/test validation

### Custom Broker Integration ✅ NEW
- **Direct API Integration**: Built custom broker system - no middleware dependency
- **Supported Brokers** (5 major Indian brokers): 
  - Zerodha (Kite Connect API v3)
  - Upstox (API v2 with public historical data)
  - AngelOne (SmartAPI with TOTP authentication)
  - Nubra (OTP + MPIN authentication)
  - Dhan (Direct access token, 24-hour validity)
- **Unified Interface**: Single BrokerInterface for all broker operations
- **Historical Data**: Direct OHLC, Volume, OI data from broker APIs
- **Live Trading**: OAuth + TOTP + OTP authentication, order placement, position tracking
- **Full Control**: No external dependencies, better performance, complete customization

## Latest Updates (Oct 14, 2024)

### Complete OpenAlgo Replacement ✅ NEW
- **Removed OpenAlgo Dependency**: Completely replaced OpenAlgo middleware with custom broker system
- **Direct Broker Integration**: All 5 brokers (Zerodha, Upstox, AngelOne, Nubra, Dhan) now work directly
- **Unified MarketData Class**: Single interface supporting both mock and real broker data
- **Live Trading Engine**: Updated to use custom brokers instead of OpenAlgo
- **Broker Settings UI**: New dedicated settings module (app_settings.py) with broker-specific authentication flows
- **No External Dependencies**: Fully independent platform with complete control over data and execution

## Latest Updates (Oct 14, 2024)

### Market Coverage Expansion ✅ NEW
- **10 Major Indices**: NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY, SENSEX, BANKEX, NIFTYIT, NIFTYPHARMA, NIFTYAUTO, NIFTYMETAL
- **200+ NSE Stocks**: Comprehensive coverage across all sectors (Nifty 50, Next 50, IT, Pharma, Auto, Banks, FMCG, Metals, Cement, Telecom, Retail, Real Estate, Infrastructure)
- **All symbols available**: AI scanner monitors all indices and stocks

### Broker Data Transparency System ✅ NEW
- **Data Source Tracking**: All market data tagged with source ('live', 'broker_unsupported', 'broker_error', 'mock')
- **Visual Warnings**: Dashboard shows clear alerts when using mock data or broker errors
- **Smart Fallback**: Automatically uses mock data when broker doesn't support live quotes
- **Safety Controls**: Live trading automatically disabled when using non-live data
- **Trading Mode Protection**: Cannot switch to Live mode without confirmed broker live data
- **Analytics Continuity**: Option chains and historical data fall back to mock when broker lacks support

### Automated AI Signal Scanner ✅
- **Auto-Scan System**: Monitors ALL 200+ stocks & 10 indices every 5 minutes automatically
- **Scan Modes**: All Symbols, Indices Only, Stocks Only
- **Progress Tracking**: Real-time progress indicator during scans
- **Smart Scheduling**: 5-minute auto-refresh with countdown timer
- **Manual Override**: "Scan Now" button for immediate analysis

### Exit Signal Detection ✅
- **Automated Monitoring**: Tracks all open positions for exit opportunities
- **Multi-Factor Analysis**: 
  - Profit target (20% achieved)
  - Stop loss (-10% triggered)
  - Time decay (Theta > 5)
  - IV drop (<15%)
  - Low liquidity (Volume < 100)
- **Exit Confidence**: Weighted scoring system for exit recommendations
- **One-Click Exit**: Instant position closure with P&L tracking

### Auto Paper Trading ✅
- **Automatic Execution**: Auto-trades ALL buy signals above confidence threshold
- **Configurable Threshold**: Adjustable min confidence (60-90%)
- **Duplicate Prevention**: Session state tracking prevents re-execution
- **Visual Indicators**: Auto-executed badges on signals
- **Learning Mode**: AI learns from every executed trade

### Enhanced Signal Display ✅
- **Detailed Reasoning**: AI explains why BUY/SELL recommendation
- **Parameter Breakdown**: Visual progress bars for each analysis factor
  - Delta Analysis, OI Change, Volume, Momentum, IV, Spread, Liquidity
- **Action Buttons**: Quick Paper Trade / Live Trade execution
- **Filter Controls**: By symbol, action, confidence, count

### Advanced Charting System ✅
- **Price vs Time Charts**: Candlestick charts with OHLC data (framework ready for real data)
- **OI Trend Analysis**: Open Interest tracking over time with gradient visualization
- **AI Signal Timeline**: Visual markers showing BUY/SELL entry/exit points on price chart
- **Multi-Factor Dashboard**: Combined 2x2 subplot showing Price, Volume, OI Change, IV Trend
- **Interactive Features**: Zoom, hover tooltips, dark theme, symbol selection
- **Note**: Charts currently use placeholder data - ready for real historical data integration via OpenAlgo /api/v1/history

## Pending Features (Roadmap)

### Trading Modes
- [ ] Live Trading: AI Auto-trading mode (single stock/index selection)
- [ ] TradingView-style advanced chart interface

### Multi-User Platform
- [ ] Admin Panel: User management, subscription control, analytics
- [ ] User Panel: Signal access, trade history, subscription status
- [ ] Authentication system (user login/registration)
- [ ] Subscription tiers and payment integration

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit with wide layout configuration
- **Visualization**: Plotly for interactive charts (candlesticks, P&L curves, performance metrics)
- **State Management**: Streamlit session state for trading mode, authentication, and settings
- **Theme Support**: Dark/Light theme toggle capability

### Backend Architecture

**Core Trading System**:
- **Market Data Layer** (`core/market.py`): Handles real-time and mock market data with intelligent fallback mechanism. Supports 10 major indices and 200+ NSE stocks. All data tagged with source ('live'/'mock'/'broker_unsupported'/'broker_error') for transparency. Generates option chains with Greeks and falls back to mock when broker lacks support.
- **Signal Generation** (`core/signals.py`): AI-powered signal engine using ensemble ML models (GradientBoostingRegressor, RandomForestRegressor). Implements adaptive parameter weighting and pattern recognition with 60% confidence threshold.
- **Trading Engines**: Dual-mode architecture with `PaperTradingEngine` for simulation/learning and `LiveTradingEngine` for real execution via broker APIs. Live trading automatically disabled when using non-live data sources.
- **Risk Management** (`core/risk.py`): Multi-layered risk controls including position limits, daily loss caps, liquidity checks, spread validation, and time-based restrictions.

**AI/ML Components**:
- **Learning System** (`core/ai_learn.py`): Implements supervised learning with RandomForest and GradientBoosting models. Tracks profitability, direction prediction, and confidence scoring. Uses StandardScaler for feature normalization.
- **Feature Engineering**: Extracts 12+ features including Greeks (delta, gamma, theta, vega), OI changes, volume ratios, IV, spread, time decay, and moneyness.
- **Model Persistence**: Sklearn joblib for saving/loading trained models and scalers.

**Data Management**:
- **Trade Journal** (`core/journal.py`): SQLite database for persistent storage of trades, positions, and performance metrics with CRUD operations.
- **Report Generation** (`core/reports.py`): Automated PDF (ReportLab) and Excel (xlsxwriter) report generation for daily/weekly/monthly summaries.

### External Dependencies

**Custom Broker System** (`core/brokers/`):
- **Unified Architecture**: 
  - `BrokerInterface` base class with standardized methods for all brokers
  - Factory pattern (`BrokerFactory`) for easy broker selection
  - No external middleware - direct broker API integration

- **Zerodha Integration** (`core/brokers/zerodha.py`):
  - Kite Connect API v3 with OAuth 2.0 flow
  - SHA-256 checksum for secure token exchange
  - Historical OHLC data via instrument tokens
  - Live quotes, orders, positions, and funds management
  
- **Upstox Integration** (`core/brokers/upstox.py`):
  - API v2 with OAuth 2.0 authentication
  - Public historical data (no auth required)
  - Rate-limited but efficient API calls
  - Bearer token for trading operations

- **AngelOne Integration** (`core/brokers/angelone.py`):
  - SmartAPI with TOTP authentication (pyotp)
  - Direct login without OAuth complexity
  - Symbol token search for historical data
  - JWT + feed token for API/WebSocket access

- **Key Benefits**:
  - ✅ Full control over broker connections
  - ✅ No middleware dependency or subscription costs
  - ✅ Better performance with direct API calls
  - ✅ Easily extensible for more brokers
  - ✅ Secure credential management

**Market Data**:
- Live option chains with strike prices, premiums, Greeks, OI, and volume
- Historical data for backtesting and pattern recognition
- Mock data system for development/testing without API access

**Third-Party Libraries**:
- **Scientific Computing**: numpy, pandas, scipy for numerical operations and statistical functions
- **Machine Learning**: scikit-learn for ML models, preprocessing, and evaluation
- **Visualization**: plotly for interactive charts, reportlab for PDF generation
- **Web Framework**: streamlit for UI, requests for API calls
- **Data Storage**: sqlite3 for relational data, json for configuration/serialization

**Key Design Patterns**:
- **Facade Pattern**: Simplified interfaces for complex subsystems (MarketData, AISignalEngine)
- **Strategy Pattern**: Interchangeable broker implementations via BrokerInterface
- **Factory Pattern**: Broker creation (BrokerFactory) and ML model initialization
- **Observer Pattern**: Real-time updates for market data and position changes
- **Interface Segregation**: Clean broker abstraction with unified methods

**Risk Controls Architecture**:
- Position-level: Stop loss (10%), take profit (20%), max loss per trade (₹5000)
- Portfolio-level: Daily loss limit (₹15000), total portfolio risk cap (₹50,000)
- Symbol-level: Max 3 positions per symbol, 10 total positions
- Market-level: Trading hours enforcement (9:20 AM - 3:15 PM), liquidity thresholds (min volume, OI, max spread)
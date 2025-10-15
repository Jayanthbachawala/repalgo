# 🤖 AI Options Trader Agent

A next-generation, AI-powered options trading platform that integrates with Upstox API for live data and trade execution. The system uses artificial intelligence to learn from paper trades, recognize market patterns, and evolve daily to suggest high-confidence entry and exit points.

## 🌟 Features

### 🎯 Core Functionality
- **Paper Trading Mode**: AI learning and testing with simulated trades
- **Live Trading Mode**: Real trade execution with strict risk controls
- **Multi-Parameter AI Analysis**: Delta, OI, Volume, IV, Spread, and Liquidity checks
- **Real-time Option Chain**: Live CE/PE data with Greeks and signals
- **Risk Management**: Comprehensive position and portfolio risk controls
- **Trade Journal**: Complete trade logging and analysis
- **Performance Reports**: PDF and Excel report generation

### 🧠 AI Features
- **Pattern Recognition**: Learns from historical trade outcomes
- **Confidence Scoring**: Multi-parameter aggregation with 60%+ threshold
- **Auto Paper Trading**: Trades top 5 gainers/losers across major indices
- **Daily Learning**: Improves accuracy targeting 99.9% over 30 days
- **Parameter Optimization**: Adjusts weights based on performance

### 📊 Supported Instruments
- **Indices**: NIFTY, BANKNIFTY, FINNIFTY, SENSEX
- **Options**: CE/PE with ATM, ITM, OTM strikes
- **Expiries**: Weekly and monthly options

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Streamlit
- Required Python packages (see requirements)

### Installation

1. **Clone or download the project files**

2. **Install dependencies**:
```bash
pip install streamlit pandas numpy plotly scikit-learn reportlab xlsxwriter requests python-dotenv scipy

3. **Run the application**:
```bash
streamlit run app.py --server.port 5000
```

## 🔌 Broker Integration Options

### Option 1: OpenAlgo (Recommended)

OpenAlgo is a self-hosted trading platform that connects to 20+ Indian brokers including Upstox, Zerodha, AngelOne, and more.

**Why OpenAlgo?**
- ✅ Unified API for multiple brokers
- ✅ Self-hosted and open source
- ✅ No vendor lock-in
- ✅ Complete data privacy

**Setup Steps:**

1. **Install OpenAlgo** (on your computer or server):
   ```bash
   git clone https://github.com/marketcalls/openalgo.git
   cd openalgo
   # Follow installation guide for your platform
   ```

2. **Connect your broker** to OpenAlgo:
   - Login to OpenAlgo web interface
   - Connect your broker (Upstox/Zerodha/etc.)
   - Generate API key from Settings

3. **Configure in AI Trader**:
   - Go to Settings page
   - Select "OpenAlgo (Recommended)"
   - Enter your OpenAlgo API key
   - Enter OpenAlgo host URL (default: http://127.0.0.1:5000)
   - Click "Connect to OpenAlgo"

4. **Enable Live Trading**:
   - Once connected, enable live trading from Settings
   - Your AI signals will now execute real trades!

**Supported Brokers via OpenAlgo (25+ Brokers):**
- ✅ Zerodha | ✅ AngelOne | ✅ Upstox | ✅ Fyers | ✅ Dhan
- ✅ Flattrade | ✅ Shoonya | ✅ AliceBlue | ✅ 5Paisa | ✅ IIFL
- ✅ Kotak Securities | ✅ Paytm | ✅ Groww | ✅ Firstock
- ✅ Motilal Oswal | ✅ Tradejini | ✅ IndMoney | ✅ Zebu
- ✅ Wisdom | ✅ Pocketful | ✅ Definedge | ✅ Compositedge
- ✅ Ibulls | ✅ Fivepaisaxts | ✅ Dhan Sandbox | ✅ & More...

**Resources:**
- OpenAlgo Website: https://www.openalgo.in/
- Documentation: https://docs.openalgo.in/
- GitHub: https://github.com/marketcalls/openalgo

### Option 2: Direct Upstox API

Connect directly to Upstox (requires API credentials):

1. Create Upstox API app: https://upstox.com/developer/apps/
2. Get API Key and Secret
3. Configure in Settings → "Direct Upstox API"

### Option 3: Mock Data Mode

Test the platform without any broker connection:
- Select "Mock Data (Testing)" in Settings
- Uses simulated market data
- Perfect for learning and testing strategies

## 🎯 Trading Modes

### Paper Trading Mode
- Default mode for AI learning
- Auto-trades top 5 gainers/losers
- Zero risk, real learning
- Generates performance reports

### Live Trading Mode  
- Requires OpenAlgo or Upstox connection
- User-confirmed trades
- Strict risk controls
- Real money, real profits/losses

⚠️ **Important**: Always test strategies in paper trading mode first!

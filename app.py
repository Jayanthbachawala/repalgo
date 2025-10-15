import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import datetime
import json
import os
from streamlit_autorefresh import st_autorefresh
from core.market import MarketData
from core.signals import AISignalEngine
from core.paper_trade import PaperTradingEngine
from core.journal import TradeJournal
from core.reports import ReportGenerator
from core.risk import RiskManager
from core.brokers.factory import BrokerFactory
from core.live_trade import LiveTradingEngine
from utils.helpers import format_currency, get_color_for_pnl

# Page configuration
st.set_page_config(
    page_title="AI Options Trader Agent",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'trading_mode' not in st.session_state:
    st.session_state.trading_mode = 'Paper'
if 'risk_enabled' not in st.session_state:
    st.session_state.risk_enabled = True
if 'theme' not in st.session_state:
    st.session_state.theme = 'Dark'
if 'auth_token' not in st.session_state:
    st.session_state.auth_token = None
if 'broker_connected' not in st.session_state:
    st.session_state.broker_connected = False
if 'selected_broker' not in st.session_state:
    st.session_state.selected_broker = None
if 'current_broker' not in st.session_state:
    st.session_state.current_broker = None
if 'broker_client_id' not in st.session_state:
    st.session_state.broker_client_id = None
if 'live_trading_enabled' not in st.session_state:
    st.session_state.live_trading_enabled = False

# Initialize core components
@st.cache_resource
def get_components():
    market_data = MarketData()
    signal_engine = AISignalEngine()
    paper_engine = PaperTradingEngine()
    journal = TradeJournal()
    report_gen = ReportGenerator()
    risk_manager = RiskManager()
    live_engine = LiveTradingEngine()
    return market_data, signal_engine, paper_engine, journal, report_gen, risk_manager, live_engine

market_data, signal_engine, paper_engine, journal, report_gen, risk_manager, live_engine = get_components()

# Restore broker from session state if exists
if st.session_state.broker_connected and st.session_state.current_broker:
    market_data.set_broker_instance(st.session_state.current_broker)
    live_engine.set_broker(st.session_state.current_broker)

def main():
    # Custom CSS for modern high-tech look
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;500;600;700&display=swap');
    
    .main-header {
        font-family: 'Orbitron', sans-serif;
        font-size: 3rem;
        font-weight: 900;
        background: linear-gradient(135deg, #00d4aa 0%, #00a8e8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 0 0 30px rgba(0, 212, 170, 0.5);
    }
    .metric-card {
        background: linear-gradient(145deg, #1e1e2e, #2a2a3e);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 4px solid #00d4aa;
        box-shadow: 0 8px 32px rgba(0, 212, 170, 0.15);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 48px rgba(0, 212, 170, 0.3);
    }
    .signal-card {
        background: linear-gradient(145deg, #1e1e2e, #2a2a3e);
        padding: 1.2rem;
        border-radius: 12px;
        margin: 0.8rem 0;
        border: 1px solid rgba(0, 212, 170, 0.2);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }
    .signal-card:hover {
        border-color: #00d4aa;
        box-shadow: 0 8px 32px rgba(0, 212, 170, 0.4);
    }
    .trade-button {
        width: 100%;
        margin: 0.25rem 0;
        background: linear-gradient(135deg, #00d4aa 0%, #00a8e8 100%);
        border: none;
        border-radius: 8px;
        padding: 0.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .trade-button:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 20px rgba(0, 212, 170, 0.4);
    }
    .stSelectbox, .stButton {
        font-family: 'Rajdhani', sans-serif;
    }
    h1, h2, h3, h4 {
        font-family: 'Rajdhani', sans-serif;
        font-weight: 700;
    }
    .element-container {
        font-family: 'Rajdhani', sans-serif;
    }
    [data-testid="stMetricValue"] {
        font-family: 'Orbitron', monospace;
        font-size: 1.8rem;
        font-weight: 700;
    }
    </style>
    """, unsafe_allow_html=True)

    # Main header
    st.markdown('<div class="main-header">🤖 AI Options Trader Agent</div>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80/00d4aa/ffffff?text=AI+TRADER", width=200)
        
        st.markdown("### 🎛️ Control Panel")
        
        # Mode toggle
        # Check if live data is available before allowing Live mode
        has_live_data = False
        if st.session_state.broker_connected and st.session_state.current_broker:
            test_quote = market_data.get_live_price("NIFTY")
            has_live_data = test_quote.get('data_source') == 'live'
        
        if has_live_data:
            trading_mode = st.selectbox(
                "Trading Mode",
                ["Paper", "Live"],
                index=0 if st.session_state.trading_mode == 'Paper' else 1
            )
            if trading_mode != st.session_state.trading_mode:
                st.session_state.trading_mode = trading_mode
                st.rerun()
        else:
            st.selectbox(
                "Trading Mode",
                ["Paper"],
                index=0,
                disabled=True,
                help="Live mode requires broker with live market data"
            )
            if st.session_state.trading_mode != "Paper":
                st.session_state.trading_mode = "Paper"

        # Risk management toggle
        risk_enabled = st.toggle("Risk Management", value=st.session_state.risk_enabled)
        if risk_enabled != st.session_state.risk_enabled:
            st.session_state.risk_enabled = risk_enabled

        # Theme toggle
        theme = st.selectbox("Theme", ["Dark", "Light"], index=0)
        st.session_state.theme = theme

        st.markdown("---")

        # Navigation
        page = st.radio(
            "Navigation",
            ["Dashboard", "Option Chain", "AI Signals", "Journal", "Reports", "Settings"]
        )

        st.markdown("---")

        # Quick stats
        st.markdown("### 📊 Quick Stats")
        portfolio_value = paper_engine.get_portfolio_value()
        daily_pnl = paper_engine.get_daily_pnl()
        total_trades = journal.get_total_trades()
        win_rate = journal.get_win_rate()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Portfolio", format_currency(portfolio_value))
            st.metric("Total Trades", total_trades)
        with col2:
            st.metric("Daily P&L", format_currency(daily_pnl), delta=format_currency(daily_pnl))
            st.metric("Win Rate", f"{win_rate:.1f}%")

    # Main content area
    if page == "Dashboard":
        show_dashboard()
    elif page == "Option Chain":
        show_option_chain()
    elif page == "AI Signals":
        show_ai_signals()
    elif page == "Journal":
        show_journal()
    elif page == "Reports":
        show_reports()
    elif page == "Settings":
        show_settings()

def show_dashboard():
    # Show broker connection status and account info
    if st.session_state.broker_connected and st.session_state.current_broker:
        st.markdown("### 🔗 Broker Connection Status")
        broker_name = st.session_state.selected_broker.upper() if st.session_state.selected_broker else "Connected"
        
        broker_col1, broker_col2, broker_col3, broker_col4 = st.columns(4)
        with broker_col1:
            st.success(f"✅ Connected to **{broker_name}**")
            # Check if broker supports live quotes
            test_quote = market_data.get_live_price("NIFTY")
            data_source = test_quote.get('data_source', 'mock')
            
            if data_source != 'live':
                # Show warning for any non-live data
                if data_source == 'broker_unsupported':
                    st.error("⚠️ Live quotes not available from this broker - using mock data")
                elif data_source == 'broker_error':
                    st.error("⚠️ Broker quote error - using mock data")
                else:
                    st.warning("⚠️ Using mock data")
                
                # Disable live trading when using mock data
                if st.session_state.live_trading_enabled:
                    st.session_state.live_trading_enabled = False
                    st.error("🛑 Live trading DISABLED - cannot trade with mock data")
        with broker_col2:
            if st.session_state.broker_client_id:
                st.info(f"👤 Client: **{st.session_state.broker_client_id}**")
        with broker_col3:
            # Try to get account funds
            try:
                if hasattr(st.session_state.current_broker, 'get_funds'):
                    funds = st.session_state.current_broker.get_funds()
                    if funds and 'available_balance' in funds:
                        st.metric("💰 Available", format_currency(funds['available_balance']))
                    else:
                        st.info("💰 Funds: N/A")
                else:
                    st.info("💰 Funds: N/A")
            except Exception as e:
                st.info(f"💰 Funds: Error ({str(e)[:20]}...)")
        with broker_col4:
            if st.button("🔌 Disconnect", key="disconnect_broker"):
                st.session_state.broker_connected = False
                st.session_state.current_broker = None
                st.session_state.selected_broker = None
                st.session_state.broker_client_id = None
                st.session_state.live_trading_enabled = False
                # Clear broker from all components
                market_data.broker = None
                market_data.mock_mode = True
                live_engine.set_broker(None)
                st.success("Disconnected from broker")
                st.rerun()
        
        st.markdown("---")
    
    # Enhanced controls for symbol and chart type
    st.markdown("### 🎯 Trading Control Center")
    
    control_col1, control_col2, control_col3, control_col4 = st.columns(4)
    
    with control_col1:
        symbol_type = st.selectbox("Asset Type", ["Indices", "Stocks"], key="symbol_type")
    
    with control_col2:
        if symbol_type == "Indices":
            available_symbols = market_data.get_available_symbols("indices")
        else:
            available_symbols = market_data.get_available_symbols("stocks")
        
        selected_symbol = st.selectbox("Symbol", available_symbols, key="selected_symbol")
    
    with control_col3:
        chart_style = st.selectbox("Chart Style", ["Candlestick", "Line", "Area", "OHLC"], key="chart_style")
    
    with control_col4:
        timeframe = st.selectbox("Timeframe", ["1min", "5min", "15min", "1hour", "1day"], 
                                index=1, key="timeframe")
    
    st.markdown("---")
    
    # Create three columns for the main layout
    col1, col2, col3 = st.columns([2, 3, 2])
    
    with col1:
        st.markdown("### 📈 Market Overview")
        
        # Show selected symbol details
        symbol_data = market_data.get_live_price(selected_symbol)
        
        st.markdown(f"#### {selected_symbol}")
        metric_col1, metric_col2 = st.columns(2)
        with metric_col1:
            st.metric("LTP", format_currency(symbol_data.get('ltp', 0)))
            st.metric("Volume", f"{symbol_data.get('volume', 0):,}")
        with metric_col2:
            change_pct = symbol_data.get('change_percent', 0)
            st.metric("Change%", f"{change_pct:+.2f}%", delta=f"{change_pct:+.2f}%")
            st.metric("OI", f"{symbol_data.get('oi', 0):,}")
        
        # Show stock fundamentals if selected
        if symbol_type == "Stocks":
            st.markdown("#### 📊 Stock Fundamentals")
            fundamentals = market_data.get_stock_fundamentals(selected_symbol)
            
            fund_col1, fund_col2 = st.columns(2)
            with fund_col1:
                st.metric("P/E Ratio", f"{fundamentals.get('pe_ratio', 0):.2f}")
                st.metric("Delivery %", f"{fundamentals.get('delivery_pct', 0):.1f}%")
            with fund_col2:
                st.metric("Market Cap (Cr)", f"₹{fundamentals.get('market_cap', 0):,.0f}")
                oi_change = fundamentals.get('oi_change', 0)
                st.metric("OI Change", f"{oi_change:+,}")
        
        st.markdown("---")
        
        # Top gainers/losers
        gainers_losers = market_data.get_top_gainers_losers()
        
        st.markdown("#### 🔥 Top 5 Gainers")
        for symbol, change in gainers_losers['gainers']:
            color = "green" if change > 0 else "red"
            st.markdown(f"**{symbol}**: <span style='color:{color}'>{change:+.2f}%</span>", unsafe_allow_html=True)
        
        st.markdown("#### 🔻 Top 5 Losers")
        for symbol, change in gainers_losers['losers']:
            color = "green" if change > 0 else "red"
            st.markdown(f"**{symbol}**: <span style='color:{color}'>{change:+.2f}%</span>", unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"### 📊 {selected_symbol} Chart ({timeframe})")
        
        # Main chart with price and signals
        chart_data = market_data.get_chart_data(selected_symbol)
        signals = signal_engine.get_recent_signals(selected_symbol)
        
        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.7, 0.3],
            subplot_titles=(f'{selected_symbol} Price & Signals', 'Open Interest'),
            vertical_spacing=0.1
        )
        
        # Chart based on selected style
        if chart_style == "Candlestick":
            fig.add_trace(
                go.Candlestick(
                    x=chart_data['timestamp'],
                    open=chart_data['open'],
                    high=chart_data['high'],
                    low=chart_data['low'],
                    close=chart_data['close'],
                    name=selected_symbol
                ),
                row=1, col=1
            )
        elif chart_style == "Line":
            fig.add_trace(
                go.Scatter(
                    x=chart_data['timestamp'],
                    y=chart_data['close'],
                    mode='lines',
                    name=selected_symbol,
                    line=dict(color='#00d4aa', width=2)
                ),
                row=1, col=1
            )
        elif chart_style == "Area":
            fig.add_trace(
                go.Scatter(
                    x=chart_data['timestamp'],
                    y=chart_data['close'],
                    fill='tozeroy',
                    name=selected_symbol,
                    line=dict(color='#00d4aa', width=2),
                    fillcolor='rgba(0, 212, 170, 0.3)'
                ),
                row=1, col=1
            )
        elif chart_style == "OHLC":
            fig.add_trace(
                go.Ohlc(
                    x=chart_data['timestamp'],
                    open=chart_data['open'],
                    high=chart_data['high'],
                    low=chart_data['low'],
                    close=chart_data['close'],
                    name=selected_symbol
                ),
                row=1, col=1
            )
        
        # Add signal markers
        for signal in signals:
            if signal['action'] == 'BUY':
                fig.add_trace(
                    go.Scatter(
                        x=[signal['timestamp']],
                        y=[signal['price']],
                        mode='markers',
                        marker=dict(symbol='triangle-up', size=15, color='green'),
                        name='Buy Signal',
                        showlegend=False
                    ),
                    row=1, col=1
                )
            elif signal['action'] == 'SELL':
                fig.add_trace(
                    go.Scatter(
                        x=[signal['timestamp']],
                        y=[signal['price']],
                        mode='markers',
                        marker=dict(symbol='triangle-down', size=15, color='red'),
                        name='Sell Signal',
                        showlegend=False
                    ),
                    row=1, col=1
                )
        
        # OI chart
        fig.add_trace(
            go.Bar(
                x=chart_data['timestamp'],
                y=chart_data['oi'],
                name='Open Interest',
                marker_color='orange'
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            height=600,
            showlegend=True,
            xaxis_rangeslider_visible=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    with col3:
        st.markdown("### 🎯 Live Signals")
        
        # Get current signals
        current_signals = signal_engine.get_current_signals()
        
        for signal in current_signals:
            with st.container():
                st.markdown(f"""
                <div class="signal-card">
                    <h4 style="margin:0;">{signal['symbol']} {signal['strike']}</h4>
                    <p><strong>Action:</strong> <span style="color:{'green' if signal['action']=='BUY' else 'red'}">{signal['action']}</span></p>
                    <p><strong>Confidence:</strong> {signal['confidence']:.1f}%</p>
                    <p><strong>Reason:</strong> {signal['reason']}</p>
                    <p><strong>Time:</strong> {signal['timestamp'].strftime('%H:%M:%S')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button(f"📋 Paper Trade", key=f"paper_{signal['id']}", help="Execute paper trade"):
                        paper_engine.execute_trade(signal, 'paper')
                        st.success("Paper trade executed!")
                        st.rerun()
                with col_b:
                    if st.session_state.trading_mode == 'Live':
                        if st.button(f"💰 Live Trade", key=f"live_{signal['id']}", help="Execute live trade"):
                            if risk_manager.validate_trade(signal):
                                paper_engine.execute_trade(signal, 'live')
                                st.success("Live trade executed!")
                                st.rerun()
                            else:
                                st.error("Trade rejected by risk manager")
        
        # Portfolio summary
        st.markdown("### 💼 Portfolio Summary")
        positions = paper_engine.get_current_positions()
        
        if positions:
            for pos in positions:
                pnl_color = get_color_for_pnl(pos['pnl'])
                st.markdown(f"""
                **{pos['symbol']}**  
                Qty: {pos['quantity']} | P&L: <span style='color:{pnl_color}'>{format_currency(pos['pnl'])}</span>
                """, unsafe_allow_html=True)
        else:
            st.info("No open positions")

def show_option_chain():
    st.markdown("### 📋 Live Option Chain")
    
    # Symbol selection with asset type
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        asset_type = st.selectbox("Asset Type", ["Indices", "Stocks"], key="oc_asset_type")
    
    with col2:
        if asset_type == "Indices":
            available_symbols = market_data.get_available_symbols("indices")
        else:
            available_symbols = market_data.get_available_symbols("stocks")
        
        symbol = st.selectbox("Select Symbol", available_symbols, key="oc_symbol")
    
    with col3:
        expiry_dates = market_data.get_expiry_dates(symbol)
        expiry = st.selectbox("Expiry Date", expiry_dates)
    
    with col4:
        if st.button("🔄 Refresh Now"):
            st.rerun()
    
    # Get option chain data
    option_chain = market_data.get_option_chain(symbol, expiry)
    
    if not option_chain.empty:
        # Add signal indicators
        option_chain = signal_engine.add_signal_indicators(option_chain)
        
        # Format the dataframe for display
        display_df = option_chain.copy()
        
        # Apply styling
        def style_option_chain(df):
            def color_pnl(val):
                if pd.isna(val):
                    return ''
                color = 'color: green' if val > 0 else 'color: red' if val < 0 else ''
                return color
            
            def highlight_signals(row):
                if row['Signal'] == '🔵 BUY':
                    return ['background-color: rgba(0, 255, 0, 0.2)'] * len(row)
                elif row['Signal'] == '🔴 SELL':
                    return ['background-color: rgba(255, 0, 0, 0.2)'] * len(row)
                else:
                    return [''] * len(row)
            
            return df.style.apply(highlight_signals, axis=1).format({
                'LTP': '₹{:.2f}',
                'Delta': '{:.3f}',
                'Gamma': '{:.4f}',
                'Theta': '{:.4f}',
                'Vega': '{:.4f}',
                'IV': '{:.2f}%',
                'Bid': '₹{:.2f}',
                'Ask': '₹{:.2f}',
                'Confidence': '{:.1f}%'
            })
        
        styled_df = style_option_chain(display_df)
        st.dataframe(styled_df, use_container_width=True, height=600)
        
        # Option chain summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_ce_oi = option_chain[option_chain['type'] == 'CE']['oi'].sum()
            st.metric("Total CE OI", f"{total_ce_oi:,.0f}")
        
        with col2:
            total_pe_oi = option_chain[option_chain['type'] == 'PE']['oi'].sum()
            st.metric("Total PE OI", f"{total_pe_oi:,.0f}")
        
        with col3:
            pcr = total_pe_oi / total_ce_oi if total_ce_oi > 0 else 0
            st.metric("PCR", f"{pcr:.2f}")
        
        with col4:
            max_pain = market_data.calculate_max_pain(option_chain)
            st.metric("Max Pain", f"₹{max_pain:.0f}")
    
    else:
        st.warning("No option chain data available for selected parameters")

def show_ai_signals():
    st.markdown("### 🤖 AI Signal Scanner - Auto Market Analysis")
    
    # Auto-refresh every 5 minutes (300000 ms) when auto-scan is enabled
    # This needs to be at the top before any conditionals
    refresh_interval = 300000  # 5 minutes in milliseconds
    
    # Auto-scan control panel
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        st.markdown("**🔄 Auto-Scanning All Markets**")
        st.caption("Monitors 75+ stocks & 4 indices every 5 minutes")
    
    with col2:
        scan_mode = st.selectbox("Scan Mode", ["All Symbols", "Indices Only", "Stocks Only"], key="scan_mode")
    
    with col3:
        auto_scan = st.toggle("🔄 Auto-Scan", value=True, key="auto_scan_toggle")
        if auto_scan:
            st.caption("Updates every 5 min")
            # Enable auto-refresh when auto-scan is on
            st_autorefresh(interval=refresh_interval, key="ai_signals_autorefresh")
    
    with col4:
        if st.button("🔍 Scan Now", type="primary"):
            st.session_state.force_scan = True
    
    # Determine which symbols to scan
    if scan_mode == "Indices Only":
        symbols_to_scan = market_data.get_available_symbols("indices")
    elif scan_mode == "Stocks Only":
        symbols_to_scan = market_data.get_available_symbols("stocks")
    else:  # All Symbols
        symbols_to_scan = market_data.get_available_symbols("indices") + market_data.get_available_symbols("stocks")
    
    # Initialize scan timestamp in session state
    if 'last_scan_time' not in st.session_state:
        st.session_state.last_scan_time = datetime.datetime.now() - datetime.timedelta(minutes=6)
    
    # Check if we need to scan (5 minute interval or force scan)
    current_time = datetime.datetime.now()
    time_since_scan = (current_time - st.session_state.last_scan_time).total_seconds()
    should_scan = time_since_scan >= 300 or st.session_state.get('force_scan', False)  # 300 seconds = 5 minutes
    
    # Auto-scan all symbols
    if (auto_scan and should_scan) or st.session_state.get('force_scan', False):
        st.session_state.force_scan = False
        st.session_state.last_scan_time = current_time
        
        scan_progress = st.progress(0, text="Starting market scan...")
        scan_results = []
        
        for idx, symbol in enumerate(symbols_to_scan):
            progress = int(((idx + 1) / len(symbols_to_scan)) * 100)
            scan_progress.progress(progress, text=f"Scanning {symbol}... ({idx+1}/{len(symbols_to_scan)})")
            
            try:
                symbol_data = market_data.get_live_price(symbol)
                option_chain = market_data.get_option_chain(symbol, "")
                
                if not option_chain.empty:
                    new_signals = signal_engine.generate_signals(
                        symbol, 
                        option_chain, 
                        symbol_data.get('ltp', 0),
                        symbol_data
                    )
                    
                    if new_signals:
                        scan_results.append({
                            'symbol': symbol,
                            'signal_count': len(new_signals),
                            'best_confidence': max([s['confidence'] for s in new_signals])
                        })
            except Exception as e:
                continue
        
        scan_progress.empty()
        
        if scan_results:
            st.success(f"✅ Scan Complete! Found opportunities in {len(scan_results)} symbols")
            
            # Show scan summary
            summary_df = pd.DataFrame(scan_results).sort_values('best_confidence', ascending=False)
            st.dataframe(summary_df.head(10), use_container_width=True, hide_index=True)
        else:
            st.info("📊 Scan complete - No high-confidence signals found in current market conditions")
    
    # Show next scan countdown if auto-scan is enabled
    if auto_scan and not should_scan:
        time_until_next = 300 - time_since_scan
        minutes = int(time_until_next // 60)
        seconds = int(time_until_next % 60)
        st.info(f"⏰ Next auto-scan in {minutes}m {seconds}s")
    
    st.markdown("---")
    
    # Exit Signal Detection for Open Positions
    st.markdown("### 🚪 Exit Signals - Open Positions")
    open_positions = paper_engine.get_current_positions()
    
    if open_positions:
        exit_signals = []
        
        for pos in open_positions:
            # Get current option data for the position
            option_chain = market_data.get_option_chain(pos['symbol'], "")
            
            if not option_chain.empty:
                # Find matching option in chain
                matching_option = option_chain[
                    (option_chain['strike'] == pos['strike']) & 
                    (option_chain['type'] == pos['type'])
                ]
                
                if not matching_option.empty:
                    current_ltp = matching_option.iloc[0]['ltp']
                    entry_price = pos['entry_price']
                    pnl_percent = ((current_ltp - entry_price) / entry_price) * 100
                    
                    # Exit signal logic
                    exit_reason = []
                    exit_confidence = 0
                    
                    # Profit target hit (20%)
                    if pnl_percent >= 20:
                        exit_reason.append("✅ Profit target (20%) achieved")
                        exit_confidence += 0.4
                    
                    # Stop loss hit (-10%)
                    if pnl_percent <= -10:
                        exit_reason.append("⛔ Stop loss (-10%) triggered")
                        exit_confidence += 0.5
                    
                    # Time decay (theta) threshold
                    theta = matching_option.iloc[0].get('theta', 0)
                    if abs(theta) > 5:
                        exit_reason.append(f"⏰ High time decay (Theta: {theta:.2f})")
                        exit_confidence += 0.2
                    
                    # IV drop
                    iv = matching_option.iloc[0].get('iv', 0)
                    if iv < 15:
                        exit_reason.append(f"📉 Low IV ({iv:.1f}%)")
                        exit_confidence += 0.15
                    
                    # Liquidity concerns
                    volume = matching_option.iloc[0].get('volume', 0)
                    if volume < 100:
                        exit_reason.append(f"💧 Low liquidity (Vol: {volume})")
                        exit_confidence += 0.1
                    
                    if exit_reason and exit_confidence >= 0.3:
                        exit_signals.append({
                            'symbol': pos['symbol'],
                            'strike': pos['strike'],
                            'type': pos['type'],
                            'entry_price': entry_price,
                            'current_price': current_ltp,
                            'pnl': pos['pnl'],
                            'pnl_percent': pnl_percent,
                            'quantity': pos['quantity'],
                            'exit_confidence': exit_confidence * 100,
                            'reasons': exit_reason,
                            'position_id': pos.get('id', '')
                        })
        
        if exit_signals:
            st.markdown(f"**⚠️ {len(exit_signals)} Position(s) Ready to Exit**")
            
            for i, exit_sig in enumerate(exit_signals):
                pnl_color = "green" if exit_sig['pnl'] > 0 else "red"
                
                with st.expander(f"🚪 EXIT: {exit_sig['symbol']} {exit_sig['strike']} {exit_sig['type']} - P&L: {exit_sig['pnl_percent']:.1f}%", expanded=True):
                    col_exit1, col_exit2 = st.columns([3, 1])
                    
                    with col_exit1:
                        st.markdown("**Position Details:**")
                        exit_col1, exit_col2, exit_col3 = st.columns(3)
                        
                        with exit_col1:
                            st.metric("Entry Price", f"₹{exit_sig['entry_price']:.2f}")
                            st.metric("Current Price", f"₹{exit_sig['current_price']:.2f}")
                        
                        with exit_col2:
                            st.metric("P&L", f"₹{exit_sig['pnl']:.2f}", delta=f"{exit_sig['pnl_percent']:.1f}%")
                            st.metric("Quantity", exit_sig['quantity'])
                        
                        with exit_col3:
                            st.metric("Exit Confidence", f"{exit_sig['exit_confidence']:.0f}%")
                        
                        st.markdown("**Exit Reasons:**")
                        for reason in exit_sig['reasons']:
                            st.warning(reason)
                    
                    with col_exit2:
                        st.markdown("### 🚪 Exit")
                        if st.button(f"Exit Position", key=f"exit_{i}", type="primary", use_container_width=True):
                            # Execute exit trade
                            result = paper_engine.close_position(exit_sig['position_id'])
                            if result.get('success'):
                                st.success("✅ Position closed!")
                                st.rerun()
                            else:
                                st.error(f"❌ {result.get('message', 'Error')}")
        else:
            st.info("✅ All positions are healthy - No exit signals")
    else:
        st.info("📭 No open positions to monitor")
    
    st.markdown("---")
    
    # Advanced Charts Section
    st.markdown("---")
    st.markdown("### 📊 Advanced Market Analytics")
    
    chart_tab1, chart_tab2, chart_tab3 = st.tabs(["📈 Price & OI Chart", "🎯 AI Signal Chart", "📉 Combined Analysis"])
    
    with chart_tab1:
        # Price vs Time (Candlestick) and OI Chart
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("**Price Chart (Candlestick)**")
            chart_symbol = st.selectbox("Select Symbol for Chart", 
                                        market_data.get_available_symbols("indices") + market_data.get_available_symbols("stocks")[:10],
                                        key="price_chart_symbol")
            
            # Try to get real historical data from broker
            if not market_data.mock_mode and market_data.broker:
                hist_df = market_data.get_historical_data(
                    symbol=chart_symbol, 
                    exchange="NSE", 
                    interval="1d", 
                    days=30
                )
                
                if not hist_df.empty and all(col in hist_df.columns for col in ['open', 'high', 'low', 'close']):
                    # Use real OHLC data from broker
                    time_col = 'timestamp' if 'timestamp' in hist_df.columns else 'date'
                    fig_candlestick = go.Figure(data=[go.Candlestick(
                        x=hist_df[time_col],
                        open=hist_df['open'],
                        high=hist_df['high'],
                        low=hist_df['low'],
                        close=hist_df['close'],
                        name=chart_symbol
                    )])
                    
                    st.success(f"✅ Real data from {market_data.broker_name}")
                else:
                    # Fallback to mock data
                    dates = pd.date_range(end=datetime.datetime.now(), periods=30, freq='D')
                    symbol_price = market_data.get_live_price(chart_symbol).get('ltp', 20000)
                    np.random.seed(42)
                    opens = symbol_price + np.random.randn(30) * 100
                    highs = opens + np.abs(np.random.randn(30) * 150)
                    lows = opens - np.abs(np.random.randn(30) * 150)
                    closes = opens + np.random.randn(30) * 100
                    
                    fig_candlestick = go.Figure(data=[go.Candlestick(
                        x=dates, open=opens, high=highs, low=lows, close=closes,
                        name=chart_symbol
                    )])
                    # Check if broker is connected
                    if st.session_state.broker_connected:
                        st.warning("⚠️ Mock data (Broker doesn't support historical data)")
                    else:
                        st.info("📊 Mock data (Connect broker for real data)")
            else:
                # Fallback to mock data
                dates = pd.date_range(end=datetime.datetime.now(), periods=30, freq='D')
                symbol_price = market_data.get_live_price(chart_symbol).get('ltp', 20000)
                np.random.seed(42)
                opens = symbol_price + np.random.randn(30) * 100
                highs = opens + np.abs(np.random.randn(30) * 150)
                lows = opens - np.abs(np.random.randn(30) * 150)
                closes = opens + np.random.randn(30) * 100
                
                fig_candlestick = go.Figure(data=[go.Candlestick(
                    x=dates, open=opens, high=highs, low=lows, close=closes,
                    name=chart_symbol
                )])
                st.info("📊 Mock data (Connect broker for real data)")
            
            fig_candlestick.update_layout(
                title=f"{chart_symbol} Price Movement (30 Days)",
                xaxis_title="Date",
                yaxis_title="Price (₹)",
                height=400,
                template="plotly_dark"
            )
            
            st.plotly_chart(fig_candlestick, use_container_width=True)
        
        with col_chart2:
            st.markdown("**Open Interest Trend**")
            
            # Try to get real OI data from broker
            if not market_data.mock_mode and market_data.broker:
                hist_df = market_data.get_historical_data(
                    symbol=chart_symbol, 
                    exchange="NFO", 
                    interval="1d", 
                    days=30
                )
                
                if not hist_df.empty and 'oi' in hist_df.columns:
                    # Use real OI data
                    time_col = 'timestamp' if 'timestamp' in hist_df.columns else 'date'
                    fig_oi = go.Figure()
                    fig_oi.add_trace(go.Scatter(
                        x=hist_df[time_col],
                        y=hist_df['oi'],
                        mode='lines+markers',
                        name='Total OI',
                        line=dict(color='#00d4aa', width=3),
                        fill='tozeroy',
                        fillcolor='rgba(0, 212, 170, 0.2)'
                    ))
                    st.success(f"✅ Real OI data from {market_data.broker_name}")
                else:
                    # Fallback to mock OI data
                    dates = pd.date_range(end=datetime.datetime.now(), periods=30, freq='D')
                    oi_data = np.abs(np.random.randn(30) * 1000000) + 5000000
                    fig_oi = go.Figure()
                    fig_oi.add_trace(go.Scatter(
                        x=dates, y=oi_data,
                        mode='lines+markers', name='Total OI',
                        line=dict(color='#00d4aa', width=3),
                        fill='tozeroy', fillcolor='rgba(0, 212, 170, 0.2)'
                    ))
                    # Check if broker is connected
                    if st.session_state.broker_connected:
                        st.warning("⚠️ Mock OI data (Broker doesn't support historical data)")
                    else:
                        st.info("📊 Mock OI data (Connect broker for real data)")
            else:
                # Fallback to mock OI data
                dates = pd.date_range(end=datetime.datetime.now(), periods=30, freq='D')
                oi_data = np.abs(np.random.randn(30) * 1000000) + 5000000
                fig_oi = go.Figure()
                fig_oi.add_trace(go.Scatter(
                    x=dates, y=oi_data,
                    mode='lines+markers', name='Total OI',
                    line=dict(color='#00d4aa', width=3),
                    fill='tozeroy', fillcolor='rgba(0, 212, 170, 0.2)'
                ))
                st.info("📊 Mock OI data (Connect broker for real data)")
            
            fig_oi.update_layout(
                title=f"{chart_symbol} Open Interest Trend",
                xaxis_title="Date",
                yaxis_title="Open Interest",
                height=400,
                template="plotly_dark"
            )
            
            st.plotly_chart(fig_oi, use_container_width=True)
    
    with chart_tab2:
        # AI Signal Chart with Entry/Exit Markers
        st.markdown("**AI Signal Timeline - Entry & Exit Points**")
        
        # Get recent signals for chart
        recent_signals = signal_engine.signals_history[-50:] if len(signal_engine.signals_history) > 0 else []
        
        if recent_signals:
            signal_df = pd.DataFrame(recent_signals)
            
            # Create price line with signal markers
            fig_signals = go.Figure()
            
            # Add price line (simulated)
            if 'timestamp' in signal_df.columns:
                signal_df['timestamp'] = pd.to_datetime(signal_df['timestamp'])
                signal_df = signal_df.sort_values('timestamp')
                
                # Simulated price line
                fig_signals.add_trace(go.Scatter(
                    x=signal_df['timestamp'],
                    y=signal_df['price'],
                    mode='lines',
                    name='Option Price',
                    line=dict(color='gray', width=2)
                ))
                
                # Add BUY signals
                buy_signals = signal_df[signal_df['action'] == 'BUY']
                fig_signals.add_trace(go.Scatter(
                    x=buy_signals['timestamp'],
                    y=buy_signals['price'],
                    mode='markers',
                    name='BUY Signal',
                    marker=dict(
                        size=15,
                        color='green',
                        symbol='triangle-up',
                        line=dict(width=2, color='white')
                    )
                ))
                
                # Add SELL signals
                sell_signals = signal_df[signal_df['action'] == 'SELL']
                fig_signals.add_trace(go.Scatter(
                    x=sell_signals['timestamp'],
                    y=sell_signals['price'],
                    mode='markers',
                    name='SELL Signal',
                    marker=dict(
                        size=15,
                        color='red',
                        symbol='triangle-down',
                        line=dict(width=2, color='white')
                    )
                ))
                
                fig_signals.update_layout(
                    title="AI Entry & Exit Signal Timeline",
                    xaxis_title="Time",
                    yaxis_title="Option Price (₹)",
                    height=500,
                    template="plotly_dark",
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig_signals, use_container_width=True)
                
                # Signal summary
                col_sum1, col_sum2, col_sum3 = st.columns(3)
                with col_sum1:
                    st.metric("Total Signals", len(signal_df))
                with col_sum2:
                    st.metric("Buy Signals", len(buy_signals), delta="Entry Points")
                with col_sum3:
                    st.metric("Sell Signals", len(sell_signals), delta="Exit Points")
        else:
            st.info("📊 No signals generated yet. Use 'Scan Now' to generate signals.")
    
    with chart_tab3:
        # Combined Analysis Chart
        st.markdown("**Multi-Factor Analysis Dashboard**")
        
        # Create subplots for comprehensive view
        from plotly.subplots import make_subplots
        
        fig_combined = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Price Movement", "Volume Analysis", "OI Change", "IV Trend"),
            specs=[[{"type": "candlestick"}, {"type": "bar"}],
                   [{"type": "scatter"}, {"type": "scatter"}]]
        )
        
        # Get real data from broker or use mock
        data_status_msg = ""
        if not market_data.mock_mode and market_data.broker:
            hist_df = market_data.get_historical_data(
                symbol=chart_symbol, interval="1d", days=30
            )
            
            if not hist_df.empty and all(col in hist_df.columns for col in ['open', 'high', 'low', 'close']):
                time_col = 'timestamp' if 'timestamp' in hist_df.columns else 'date'
                x_data = hist_df[time_col]
                opens = hist_df['open']
                highs = hist_df['high']
                lows = hist_df['low']
                closes = hist_df['close']
                
                # Check which additional columns exist
                has_volume = 'volume' in hist_df.columns
                has_oi = 'oi_change' in hist_df.columns or 'oi' in hist_df.columns
                has_iv = 'iv' in hist_df.columns
                
                if has_volume:
                    volumes = hist_df['volume']
                else:
                    volumes = np.abs(np.random.randn(len(x_data)) * 50000) + 100000
                
                if has_oi:
                    oi_change = hist_df.get('oi_change', hist_df.get('oi', np.random.randn(len(x_data)) * 100000))
                else:
                    oi_change = np.random.randn(len(x_data)) * 100000
                
                if has_iv:
                    iv_data = hist_df['iv']
                else:
                    iv_data = 20 + np.random.randn(len(x_data)) * 5
                
                # Determine status
                real_cols = []
                mock_cols = []
                if has_volume: real_cols.append("Volume")
                else: mock_cols.append("Volume")
                if has_oi: real_cols.append("OI")
                else: mock_cols.append("OI")
                if has_iv: real_cols.append("IV")
                else: mock_cols.append("IV")
                
                is_real = has_volume and has_oi and has_iv
                data_status_msg = f"✅ Price + {', '.join(real_cols)} (real)" + (f" | ⚠️ {', '.join(mock_cols)} (mock)" if mock_cols else "")
            else:
                # Fallback to mock
                x_data = pd.date_range(end=datetime.datetime.now(), periods=30, freq='D')
                base_price = market_data.get_live_price(chart_symbol).get('ltp', 20000)
                np.random.seed(42)
                opens = base_price + np.random.randn(30) * 100
                highs = opens + np.abs(np.random.randn(30) * 150)
                lows = opens - np.abs(np.random.randn(30) * 150)
                closes = opens + np.random.randn(30) * 100
                volumes = np.abs(np.random.randn(30) * 50000) + 100000
                oi_change = np.random.randn(30) * 100000
                iv_data = 20 + np.random.randn(30) * 5
                is_real = False
        else:
            # Fallback to mock
            x_data = pd.date_range(end=datetime.datetime.now(), periods=30, freq='D')
            base_price = market_data.get_live_price(chart_symbol).get('ltp', 20000)
            np.random.seed(42)
            opens = base_price + np.random.randn(30) * 100
            highs = opens + np.abs(np.random.randn(30) * 150)
            lows = opens - np.abs(np.random.randn(30) * 150)
            closes = opens + np.random.randn(30) * 100
            volumes = np.abs(np.random.randn(30) * 50000) + 100000
            oi_change = np.random.randn(30) * 100000
            iv_data = 20 + np.random.randn(30) * 5
            is_real = False
        
        # Price candlestick
        fig_combined.add_trace(
            go.Candlestick(
                x=x_data, open=opens, high=highs, low=lows, close=closes,
                name="Price"
            ),
            row=1, col=1
        )
        
        # Volume bars
        fig_combined.add_trace(
            go.Bar(x=x_data, y=volumes, name="Volume", marker_color='#00d4aa'),
            row=1, col=2
        )
        
        # OI Change
        colors = ['green' if x > 0 else 'red' for x in oi_change]
        fig_combined.add_trace(
            go.Bar(x=x_data, y=oi_change, name="OI Change", marker_color=colors),
            row=2, col=1
        )
        
        # IV Trend
        fig_combined.add_trace(
            go.Scatter(x=x_data, y=iv_data, name="IV %", line=dict(color='orange', width=2)),
            row=2, col=2
        )
        
        fig_combined.update_layout(
            height=800,
            showlegend=True,
            template="plotly_dark",
            title_text="Comprehensive Market Analysis Dashboard"
        )
        
        if data_status_msg:
            st.info(data_status_msg)
        
        st.plotly_chart(fig_combined, use_container_width=True)
    
    st.markdown("---")
    
    # Entry Signal filters
    st.markdown("### 🎯 Entry Signals - Best Opportunities")
    
    # Auto Paper Trading Control
    col_auto1, col_auto2, col_auto3 = st.columns([2, 1, 1])
    
    with col_auto1:
        auto_paper_trade = st.toggle("🤖 Auto Paper Trade ALL Buy Signals", value=False, key="auto_paper_trade")
        if auto_paper_trade:
            st.caption("⚠️ Will automatically execute paper trades for ALL buy signals above confidence threshold")
    
    with col_auto2:
        auto_paper_min_conf = st.slider("Auto Trade Min Confidence", 60, 90, 70, key="auto_paper_conf")
    
    with col_auto3:
        if auto_paper_trade:
            st.success("✅ Auto Trading ON")
        else:
            st.info("⏸️ Auto Trading OFF")
    
    # Signal filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Get all unique symbols from signals history
        all_symbols = ["All"] + list(set([s['symbol'] for s in signal_engine.signals_history]))
        symbol_filter = st.selectbox("Filter by Symbol", all_symbols)
    
    with col2:
        action_filter = st.selectbox("Filter by Action", ["All", "BUY", "SELL", "HOLD"])
    
    with col3:
        min_confidence = st.slider("Min Confidence %", 0, 100, 60)
    
    with col4:
        show_count = st.selectbox("Show", [10, 25, 50, 100], index=1)
    
    # Get signals with filters
    signals = signal_engine.get_signals_with_filters(
        symbol=None if symbol_filter == "All" else symbol_filter,
        action=None if action_filter == "All" else action_filter,
        min_confidence=min_confidence/100
    )[:show_count]
    
    if signals:
        st.markdown(f"**Showing {len(signals)} Signals**")
        
        # Auto paper trade execution
        if auto_paper_trade:
            auto_executed = 0
            for signal in signals:
                if signal['action'] == 'BUY' and signal['confidence'] >= auto_paper_min_conf:
                    # Check if already executed
                    if not st.session_state.get(f"auto_executed_{signal.get('id', '')}", False):
                        result = paper_engine.execute_trade(signal, 'paper')
                        if result.get('success'):
                            st.session_state[f"auto_executed_{signal.get('id', '')}"] = True
                            auto_executed += 1
            
            if auto_executed > 0:
                st.success(f"🤖 Auto-executed {auto_executed} paper trades")
        
        for i, signal in enumerate(signals):
            action_color = "green" if signal['action'] == 'BUY' else "red" if signal['action'] == 'SELL' else "gray"
            action_emoji = "🟢" if signal['action'] == 'BUY' else "🔴" if signal['action'] == 'SELL' else "⚪"
            
            # Check if auto-executed
            is_auto_executed = st.session_state.get(f"auto_executed_{signal.get('id', '')}", False)
            auto_badge = " [🤖 AUTO-EXECUTED]" if is_auto_executed else ""
            
            with st.expander(f"{action_emoji} {signal['symbol']} {signal['strike']} {signal['type']} - {signal['action']} @ ₹{signal['price']:.2f} (Confidence: {signal['confidence']:.1f}%){auto_badge}", expanded=i<3):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Trade Details
                    st.markdown(f"### 📊 Trade Details")
                    detail_col1, detail_col2, detail_col3 = st.columns(3)
                    
                    with detail_col1:
                        st.metric("Symbol", signal['symbol'])
                        st.metric("Strike", f"₹{signal['strike']}")
                    with detail_col2:
                        st.metric("Type", signal['type'])
                        st.metric("Action", signal['action'])
                    with detail_col3:
                        st.metric("LTP", f"₹{signal['price']:.2f}")
                        st.metric("Confidence", f"{signal['confidence']:.1f}%")
                    
                    # AI Reasoning
                    st.markdown(f"### 🧠 AI Analysis & Reasoning")
                    st.markdown(f"**Why {signal['action']} this option:**")
                    st.info(signal.get('reasoning', 'Analysis based on multiple market parameters'))
                    
                    # Parameter Breakdown
                    st.markdown("### 📈 Parameter Scores")
                    params = signal.get('parameters', {})
                    
                    param_col1, param_col2 = st.columns(2)
                    
                    param_names = {
                        'delta_score': '📊 Delta Analysis',
                        'oi_score': '📦 Open Interest',
                        'volume_score': '📈 Volume Analysis',
                        'momentum_score': '🚀 Price Momentum',
                        'iv_score': '💫 Implied Volatility',
                        'spread_score': '💰 Bid-Ask Spread',
                        'liquidity_score': '💧 Liquidity Depth'
                    }
                    
                    param_idx = 0
                    for param_key, param_name in param_names.items():
                        if param_key in params:
                            score = params[param_key] * 100
                            
                            with param_col1 if param_idx % 2 == 0 else param_col2:
                                st.progress(params[param_key], text=f"{param_name}: {score:.0f}%")
                            
                            param_idx += 1
                    
                    st.caption(f"🕐 Generated: {signal['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                
                with col2:
                    st.markdown("### ⚡ Quick Actions")
                    
                    # Show if already auto-executed
                    if is_auto_executed:
                        st.success("✅ Auto-executed")
                    else:
                        if st.button(f"📋 Paper Trade", key=f"exec_paper_{i}", use_container_width=True):
                            result = paper_engine.execute_trade(signal, 'paper')
                            if result.get('success'):
                                st.success("✅ Paper trade executed!")
                                st.rerun()
                            else:
                                st.error(f"❌ {result.get('message', 'Error')}")
                    
                    if st.session_state.trading_mode == 'Live' and st.session_state.live_trading_enabled:
                        if st.button(f"💰 Live Trade", key=f"exec_live_{i}", use_container_width=True):
                            if risk_manager.validate_trade(signal):
                                result = live_engine.execute_live_trade(signal, risk_manager)
                                if result.get('success'):
                                    st.success("✅ Live trade executed!")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {result.get('message', 'Error')}")
                            else:
                                st.error("❌ Risk check failed")
        
        # Auto-refresh handled by auto-scan
        if auto_scan:
            st.info("🔄 Signals auto-refresh every 5 minutes with auto-scan enabled")
    else:
        st.info("🔍 No signals match the current filters. Try generating signals for a specific symbol or adjusting filter criteria.")

def show_journal():
    st.markdown("### 📓 Trade Journal")
    
    # Get trade history
    trades = journal.get_trade_history()
    
    if not trades.empty:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_pnl = trades['pnl'].sum()
            st.metric("Total P&L", format_currency(total_pnl), delta=format_currency(total_pnl))
        
        with col2:
            win_rate = (trades['pnl'] > 0).sum() / len(trades) * 100
            st.metric("Win Rate", f"{win_rate:.1f}%")
        
        with col3:
            avg_trade = trades['pnl'].mean()
            st.metric("Avg Trade P&L", format_currency(avg_trade))
        
        with col4:
            max_drawdown = journal.get_max_drawdown()
            st.metric("Max Drawdown", format_currency(max_drawdown))
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            date_range = st.date_input(
                "Date Range",
                value=(datetime.date.today() - datetime.timedelta(days=30), datetime.date.today()),
                max_value=datetime.date.today()
            )
        
        with col2:
            symbol_filter = st.multiselect("Symbols", trades['symbol'].unique(), default=trades['symbol'].unique())
        
        with col3:
            trade_type = st.selectbox("Trade Type", ["All", "Paper", "Live"])
        
        # Filter trades
        filtered_trades = trades.copy()
        if len(date_range) == 2:
            filtered_trades = filtered_trades[
                (filtered_trades['entry_time'].dt.date >= date_range[0]) &
                (filtered_trades['entry_time'].dt.date <= date_range[1])
            ]
        
        if symbol_filter:
            filtered_trades = filtered_trades[filtered_trades['symbol'].isin(symbol_filter)]
        
        if trade_type != "All":
            filtered_trades = filtered_trades[filtered_trades['trade_type'] == trade_type.lower()]
        
        # Display trades table
        if not filtered_trades.empty:
            st.dataframe(
                filtered_trades.style.format({
                    'entry_price': '₹{:.2f}',
                    'exit_price': '₹{:.2f}',
                    'pnl': '₹{:.2f}',
                    'confidence': '{:.1f}%'
                }).apply(lambda x: ['background-color: rgba(0,255,0,0.2)' if v > 0 else 'background-color: rgba(255,0,0,0.2)' if v < 0 else '' for v in x] if x.name == 'pnl' else [''] * len(x), axis=0),
                use_container_width=True
            )
            
            # P&L Chart
            st.markdown("### 📈 P&L Curve")
            filtered_trades['cumulative_pnl'] = filtered_trades['pnl'].cumsum()
            
            fig = px.line(
                filtered_trades,
                x='entry_time',
                y='cumulative_pnl',
                title='Cumulative P&L Over Time',
                labels={'cumulative_pnl': 'Cumulative P&L (₹)', 'entry_time': 'Date'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No trades found for the selected filters")
    else:
        st.info("No trades recorded yet")

def show_reports():
    st.markdown("### 📊 Reports & Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📄 Generate Reports")
        
        report_type = st.selectbox("Report Type", ["Daily Summary", "Weekly Report", "Monthly Report", "Custom Range"])
        
        if report_type == "Custom Range":
            start_date = st.date_input("Start Date", value=datetime.date.today() - datetime.timedelta(days=30))
            end_date = st.date_input("End Date", value=datetime.date.today())
        else:
            start_date = end_date = None
        
        report_format = st.selectbox("Format", ["PDF", "Excel", "Both"])
        
        if st.button("Generate Report", type="primary"):
            with st.spinner("Generating report..."):
                if report_format in ["PDF", "Both"]:
                    pdf_path = report_gen.generate_pdf_report(report_type, start_date, end_date)
                    with open(pdf_path, "rb") as file:
                        st.download_button(
                            label="📄 Download PDF Report",
                            data=file.read(),
                            file_name=f"trading_report_{datetime.date.today()}.pdf",
                            mime="application/pdf"
                        )
                
                if report_format in ["Excel", "Both"]:
                    excel_path = report_gen.generate_excel_report(report_type, start_date, end_date)
                    with open(excel_path, "rb") as file:
                        st.download_button(
                            label="📊 Download Excel Report",
                            data=file.read(),
                            file_name=f"trading_report_{datetime.date.today()}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
            
            st.success("Report generated successfully!")
    
    with col2:
        st.markdown("#### 📈 Performance Analytics")
        
        # AI Learning Progress
        learning_data = signal_engine.get_learning_progress()
        
        if learning_data:
            fig = px.line(
                x=range(len(learning_data)),
                y=learning_data,
                title="AI Learning Progress (Accuracy %)",
                labels={'x': 'Days', 'y': 'Accuracy %'}
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        # Risk Metrics
        st.markdown("#### ⚠️ Risk Metrics")
        risk_metrics = risk_manager.get_risk_metrics()
        
        for metric, value in risk_metrics.items():
            st.metric(metric.replace('_', ' ').title(), f"{value:.2f}")

def show_settings():
    st.markdown("### ⚙️ Settings")
    
    # Import broker settings module
    from app_settings import show_broker_settings, show_live_trading_controls
    
    # Show broker configuration
    show_broker_settings(market_data, live_engine)
    
    # Show live trading controls
    show_live_trading_controls(live_engine)
    
    # Trading Settings
    st.markdown("#### 💰 Trading Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        default_quantity = st.number_input("Default Lot Size", min_value=1, max_value=100, value=1)
        max_daily_trades = st.number_input("Max Daily Trades", min_value=1, max_value=20, value=5)
        
    with col2:
        auto_paper_trade = st.toggle("Auto Paper Trading", value=True)
        notifications_enabled = st.toggle("Push Notifications", value=True)
    
    # Risk Management Settings
    st.markdown("#### ⚠️ Risk Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_loss_per_trade = st.number_input("Max Loss per Trade (₹)", min_value=100, max_value=50000, value=5000)
        max_daily_loss = st.number_input("Max Daily Loss (₹)", min_value=500, max_value=100000, value=15000)
    
    with col2:
        stop_loss_percent = st.slider("Default Stop Loss %", 1, 20, 10)
        take_profit_percent = st.slider("Default Take Profit %", 5, 50, 20)
    
    # AI Settings
    st.markdown("#### 🤖 AI Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        min_confidence_threshold = st.slider("Minimum Confidence Threshold", 0.1, 0.9, 0.6)
        learning_rate = st.slider("Learning Rate", 0.001, 0.1, 0.01)
    
    with col2:
        lookback_days = st.number_input("Learning Lookback Days", min_value=7, max_value=90, value=30)
        retrain_frequency = st.selectbox("Model Retrain Frequency", ["Daily", "Weekly", "Manual"])
    
    # Save settings
    if st.button("💾 Save Settings", type="primary"):
        # Here you would save settings to database or config file
        settings = {
            'default_quantity': default_quantity,
            'max_daily_trades': max_daily_trades,
            'auto_paper_trade': auto_paper_trade,
            'notifications_enabled': notifications_enabled,
            'max_loss_per_trade': max_loss_per_trade,
            'max_daily_loss': max_daily_loss,
            'stop_loss_percent': stop_loss_percent,
            'take_profit_percent': take_profit_percent,
            'min_confidence_threshold': min_confidence_threshold,
            'learning_rate': learning_rate,
            'lookback_days': lookback_days,
            'retrain_frequency': retrain_frequency
        }
        
        # Save to session state for now
        st.session_state.settings = settings
        st.success("Settings saved successfully!")
    
    # Reset to defaults
    if st.button("🔄 Reset to Defaults"):
        st.rerun()

if __name__ == "__main__":
    main()

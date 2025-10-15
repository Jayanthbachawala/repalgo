import streamlit as st
from core.brokers.factory import BrokerFactory

def show_broker_settings(market_data, live_engine):
    """Show broker configuration UI"""
    
    st.markdown("#### 🔐 Broker Connection")
    
    # Get available brokers
    available_brokers = BrokerFactory.get_supported_brokers()
    broker_names = BrokerFactory.get_broker_display_names()
    
    # Broker selection
    broker_choice = st.selectbox(
        "Select Broker:",
        ["Mock Data (Testing)"] + [broker_names[b] for b in available_brokers],
        index=0
    )
    
    if broker_choice == "Mock Data (Testing)":
        st.info("🔒 Using Mock Data Mode for testing. No broker connection required.")
        st.session_state.broker_connected = False
        return
    
    # Find broker code
    broker_code = None
    for code, name in broker_names.items():
        if name == broker_choice:
            broker_code = code
            break
    
    if not broker_code:
        return
    
    st.markdown(f"### Connect to {broker_choice}")
    
    # Broker-specific authentication
    if broker_code == "zerodha":
        show_zerodha_auth(market_data, live_engine)
    elif broker_code == "upstox":
        show_upstox_auth(market_data, live_engine)
    elif broker_code == "angelone":
        show_angelone_auth(market_data, live_engine)
    elif broker_code == "nubra":
        show_nubra_auth(market_data, live_engine)
    elif broker_code == "dhan":
        show_dhan_auth(market_data, live_engine)

def show_zerodha_auth(market_data, live_engine):
    """Zerodha Kite Connect authentication"""
    st.info("Zerodha Kite Connect API v3 - OAuth 2.0")
    
    # Initialize session state
    if 'zerodha_broker' not in st.session_state:
        st.session_state.zerodha_broker = None
    if 'zerodha_login_url' not in st.session_state:
        st.session_state.zerodha_login_url = None
    
    api_key = st.text_input("API Key", type="password", key="zerodha_api_key")
    api_secret = st.text_input("API Secret", type="password", key="zerodha_api_secret")
    
    if st.button("Get Login URL", key="zerodha_get_url"):
        if api_key and api_secret:
            credentials = {
                'api_key': api_key,
                'api_secret': api_secret
            }
            
            broker = BrokerFactory.create_broker('zerodha')
            result = broker.authenticate(credentials)
            
            if result.get('success'):
                st.session_state.zerodha_broker = broker
                st.session_state.zerodha_login_url = result.get('login_url', '')
                st.session_state.zerodha_credentials = credentials
                st.rerun()
    
    if st.session_state.zerodha_login_url:
        st.success(f"✅ Login URL generated!")
        st.code(st.session_state.zerodha_login_url, language="text")
        
        request_token = st.text_input("Enter Request Token from browser:", key="zerodha_request_token")
        
        if st.button("Complete Authentication", key="zerodha_complete"):
            if request_token and st.session_state.zerodha_broker:
                broker = st.session_state.zerodha_broker
                token_result = broker.get_access_token(request_token, st.session_state.zerodha_credentials)
                
                if token_result.get('success'):
                    # Save broker to session state
                    st.session_state.current_broker = broker
                    st.session_state.broker_client_id = st.session_state.zerodha_credentials.get('api_key', 'N/A')
                    
                    market_data.set_broker_instance(broker)
                    live_engine.set_broker(broker)
                    st.session_state.broker_connected = True
                    st.session_state.selected_broker = 'zerodha'
                    st.success("✅ Connected to Zerodha!")
                    st.rerun()
                else:
                    st.error(token_result.get('message'))

def show_upstox_auth(market_data, live_engine):
    """Upstox API v2 authentication"""
    st.info("Upstox API v2 - OAuth 2.0")
    
    # Initialize session state
    if 'upstox_broker' not in st.session_state:
        st.session_state.upstox_broker = None
    if 'upstox_login_url' not in st.session_state:
        st.session_state.upstox_login_url = None
    
    api_key = st.text_input("API Key", type="password", key="upstox_api_key")
    api_secret = st.text_input("API Secret", type="password", key="upstox_api_secret")
    redirect_uri = st.text_input("Redirect URI", value="http://localhost", key="upstox_redirect")
    
    if st.button("Get Login URL", key="upstox_get_url"):
        if api_key and api_secret:
            credentials = {
                'api_key': api_key,
                'api_secret': api_secret,
                'redirect_uri': redirect_uri
            }
            
            broker = BrokerFactory.create_broker('upstox')
            result = broker.authenticate(credentials)
            
            if result.get('success'):
                st.session_state.upstox_broker = broker
                st.session_state.upstox_login_url = result.get('login_url', '')
                st.session_state.upstox_credentials = credentials
                st.rerun()
    
    if st.session_state.upstox_login_url:
        st.success(f"✅ Login URL generated!")
        st.code(st.session_state.upstox_login_url, language="text")
        
        auth_code = st.text_input("Enter Authorization Code from redirect URL:", key="upstox_auth_code")
        
        if st.button("Complete Authentication", key="upstox_complete"):
            if auth_code and st.session_state.upstox_broker:
                broker = st.session_state.upstox_broker
                token_result = broker.get_access_token(auth_code, st.session_state.upstox_credentials)
                
                if token_result.get('success'):
                    # Save broker to session state
                    st.session_state.current_broker = broker
                    st.session_state.broker_client_id = st.session_state.upstox_credentials.get('api_key', 'N/A')
                    
                    market_data.set_broker_instance(broker)
                    live_engine.set_broker(broker)
                    st.session_state.broker_connected = True
                    st.session_state.selected_broker = 'upstox'
                    st.success("✅ Connected to Upstox!")
                    st.rerun()
                else:
                    st.error(token_result.get('message'))

def show_angelone_auth(market_data, live_engine):
    """AngelOne SmartAPI authentication"""
    st.info("AngelOne SmartAPI - TOTP Authentication")
    
    api_key = st.text_input("API Key", type="password", key="angel_api_key")
    client_id = st.text_input("Client ID", key="angel_client_id")
    password = st.text_input("Password", type="password", key="angel_password")
    totp_token = st.text_input("TOTP Secret", type="password", key="angel_totp",
                               help="Your TOTP secret from authenticator app")
    
    if st.button("Connect to AngelOne", key="connect_angelone"):
        if all([api_key, client_id, password, totp_token]):
            credentials = {
                'api_key': api_key,
                'client_id': client_id,
                'password': password,
                'totp_token': totp_token
            }
            
            broker = BrokerFactory.create_broker('angelone')
            result = broker.authenticate(credentials)
            
            if result.get('success'):
                # Save broker to session state
                st.session_state.current_broker = broker
                st.session_state.broker_client_id = client_id
                
                market_data.set_broker_instance(broker)
                live_engine.set_broker(broker)
                st.session_state.broker_connected = True
                st.session_state.selected_broker = 'angelone'
                st.success("✅ Connected to AngelOne!")
                st.rerun()
            else:
                st.error(result.get('message'))
        else:
            st.error("Please provide all required fields")

def show_nubra_auth(market_data, live_engine):
    """Nubra OTP + MPIN authentication"""
    st.info("Nubra - OTP + MPIN Authentication")
    
    # Initialize session state
    if 'nubra_broker' not in st.session_state:
        st.session_state.nubra_broker = None
    if 'nubra_temp_token' not in st.session_state:
        st.session_state.nubra_temp_token = None
    if 'nubra_auth_token' not in st.session_state:
        st.session_state.nubra_auth_token = None
    if 'nubra_phone' not in st.session_state:
        st.session_state.nubra_phone = ""
    
    phone = st.text_input("Phone Number", value=st.session_state.nubra_phone, key="nubra_phone_input")
    device_id = st.text_input("Device ID", value="AI_TRADER_001", key="nubra_device")
    
    # Step 1: Send OTP
    if not st.session_state.nubra_temp_token:
        if st.button("Send OTP", key="nubra_send_otp"):
            if phone:
                credentials = {
                    'phone': phone,
                    'device_id': device_id,
                    'env': 'PROD'
                }
                
                broker = BrokerFactory.create_broker('nubra')
                result = broker.authenticate(credentials)
                
                if result.get('success'):
                    st.success(result['message'])
                    st.session_state.nubra_temp_token = result.get('temp_token')
                    st.session_state.nubra_broker = broker
                    st.session_state.nubra_phone = phone
                    st.rerun()
                else:
                    st.error(result.get('message'))
            else:
                st.error("Please provide phone number")
    
    # Step 2: Verify OTP
    if st.session_state.nubra_temp_token and not st.session_state.nubra_auth_token:
        st.success("✅ OTP sent!")
        otp = st.text_input("Enter OTP", key="nubra_otp")
        
        if st.button("Verify OTP", key="nubra_verify_otp"):
            if otp:
                broker = st.session_state.nubra_broker
                otp_result = broker.verify_otp(st.session_state.nubra_phone, otp, st.session_state.nubra_temp_token)
                
                if otp_result.get('success'):
                    st.session_state.nubra_auth_token = otp_result['auth_token']
                    st.rerun()
                else:
                    st.error(otp_result.get('message'))
            else:
                st.error("Please enter OTP")
    
    # Step 3: Verify PIN
    if st.session_state.nubra_auth_token:
        st.success("✅ OTP verified!")
        pin = st.text_input("Enter MPIN", type="password", key="nubra_pin")
        
        if st.button("Complete Authentication", key="nubra_verify_pin"):
            if pin:
                broker = st.session_state.nubra_broker
                pin_result = broker.verify_pin(pin, st.session_state.nubra_auth_token)
                
                if pin_result.get('success'):
                    # Save broker to session state
                    st.session_state.current_broker = broker
                    st.session_state.broker_client_id = st.session_state.nubra_phone
                    
                    market_data.set_broker_instance(broker)
                    live_engine.set_broker(broker)
                    st.session_state.broker_connected = True
                    st.session_state.selected_broker = 'nubra'
                    # Clear nubra session state
                    st.session_state.nubra_temp_token = None
                    st.session_state.nubra_auth_token = None
                    st.success("✅ Connected to Nubra!")
                    st.rerun()
                else:
                    st.error(pin_result.get('message'))
            else:
                st.error("Please enter MPIN")

def show_dhan_auth(market_data, live_engine):
    """Dhan direct access token authentication"""
    st.info("Dhan - Direct Access Token (24-hour validity)")
    st.markdown("Get your access token from **web.dhan.co → Profile → DhanHQ APIs**")
    
    access_token = st.text_input("Access Token", type="password", key="dhan_token")
    client_id = st.text_input("Client ID", key="dhan_client_id")
    
    if st.button("Connect to Dhan", key="connect_dhan"):
        if access_token and client_id:
            credentials = {
                'access_token': access_token,
                'client_id': client_id
            }
            
            broker = BrokerFactory.create_broker('dhan')
            result = broker.authenticate(credentials)
            
            if result.get('success'):
                # Save broker instance to session state for persistence
                st.session_state.current_broker = broker
                st.session_state.broker_client_id = client_id
                
                market_data.set_broker_instance(broker)
                live_engine.set_broker(broker)
                st.session_state.broker_connected = True
                st.session_state.selected_broker = 'dhan'
                st.success("✅ Connected to Dhan!")
                st.rerun()
            else:
                st.error(result.get('message'))
        else:
            st.error("Please provide Access Token and Client ID")

def show_live_trading_controls(live_engine):
    """Show live trading enable/disable controls"""
    st.markdown("---")
    st.markdown("##### 🔴 Live Trading Control")
    
    if st.session_state.broker_connected:
        # Check if broker provides live data
        from core.market import MarketData
        market_data = MarketData()
        if st.session_state.current_broker:
            market_data.set_broker_instance(st.session_state.current_broker)
        
        test_quote = market_data.get_live_price("NIFTY")
        has_live_data = test_quote.get('data_source') == 'live'
        
        if not has_live_data:
            st.error("🚫 Live trading unavailable: Broker does not provide live market data")
            if st.session_state.live_trading_enabled:
                st.session_state.live_trading_enabled = False
                live_engine.disable_live_trading()
        elif st.session_state.live_trading_enabled:
            if st.button("🛑 Disable Live Trading", type="secondary"):
                result = live_engine.disable_live_trading()
                st.session_state.live_trading_enabled = False
                st.success(result['message'])
                st.rerun()
            
            st.warning("⚠️ Live trading is ENABLED. Real orders will be placed!")
        else:
            if st.button("✅ Enable Live Trading", type="primary"):
                result = live_engine.enable_live_trading()
                if result['success']:
                    st.session_state.live_trading_enabled = True
                    st.success(result['message'])
                    st.rerun()
                else:
                    st.error(result['message'])
            
            st.info("Live trading is disabled. Only paper trades will execute.")
    else:
        st.info("🔒 Connect to a broker first to enable live trading")

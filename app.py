import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
from dateutil.relativedelta import relativedelta
from jugaad_data.nse import stock_df

# --- Page Configuration ---
st.set_page_config(page_title="NSE Stock & Sector Tracker", layout="wide")

# --- Default Data ---
DEFAULT_SECTORS = {
    "My Watchlist": ["ASTRAL", "TATAMOTORS", "BANKBARODA", "PFC", "RECLTD", "HUDCO", "RVNL", "GODREJIND"],
    "Nifty 50": ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "BHARTIARTL", "ITC", "L&T"],
    "Nifty Bank": ["HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK", "PNB", "INDUSINDBK"],
    "Nifty IT": ["TCS", "INFY", "HCLTECH", "WIPRO", "TECHM", "LTIM", "PERSISTENT"]
}

# --- Core Calculation Function ---
@st.cache_data(ttl=900) # Caches data for 15 minutes
def fetch_and_calculate(ticker_symbol):
    try:
        # Clean the symbol (jugaad-data doesn't use the .NS extension)
        clean_symbol = ticker_symbol.replace('.NS', '').strip()
        
        # Set timeframe: Today going back exactly 2 years
        end_date = date.today()
        start_date = end_date - relativedelta(years=2)
        
        # Pull historical dataframe directly from NSE India
        df_raw = stock_df(symbol=clean_symbol, from_date=start_date, to_date=end_date, series="EQ")
        
        if df_raw.empty:
            return None
            
        # jugaad-data returns dates in descending order, so reverse it to ascending
        df_raw = df_raw.iloc[::-1].reset_index(drop=True)
        
        # Extract exact columns for math
        close = df_raw['CLOSE']
        current_price = close.iloc[-1]
        
        # Trading day approximations
        periods = {
            '1D %': 1, '3D %': 3, '1W %': 5, '2W %': 10, 
            '1M %': 21, '2M %': 42, '3M %': 63, '6M %': 126, '1Y %': 252
        }
        
        returns = {}
        for label, days in periods.items():
            if len(close) > days:
                past_price = close.iloc[-(days+1)]
                returns[label] = ((current_price - past_price) / past_price) * 100
            else:
                returns[label] = np.nan
                
        # Exponential Moving Averages
        ema4 = close.ewm(span=4, adjust=False).mean().iloc[-1]
        ema10 = close.ewm(span=10, adjust=False).mean().iloc[-1]
        ema20 = close.ewm(span=20, adjust=False).mean().iloc[-1]
        
        # 52 Week High/Low (last 252 trading days)
        last_252 = df_raw.tail(252)
        high_52w = last_252['HIGH'].max()
        low_52w = last_252['LOW'].min()
        
        pct_below_high = ((current_price - high_52w) / high_52w) * 100
        pct_above_low = ((current_price - low_52w) / low_52w) * 100
        
        return {
            "Symbol": clean_symbol,
            "LTP": current_price,
            **returns,
            "4 EMA": ema4,
            "10 EMA": ema10,
            "20 EMA": ema20,
            "52W High": high_52w,
            "% Below 52W H": pct_below_high, 
            "52W Low": low_52w,
            "% Above 52W L": pct_above_low   
        }
    except Exception as e:
        return None

# --- UI and Layout ---
st.title("📈 NSE Dynamic Sector & Stock Tracker")
st.markdown("Track absolute returns, EMAs, and 52-week extremes for custom baskets.")

# Sidebar Configuration
st.sidebar.header("⚙️ Dashboard Controls")

selected_sector = st.sidebar.selectbox("Choose a Sector / Basket", list(DEFAULT_SECTORS.keys()) + ["Custom Basket"])

if selected_sector == "Custom Basket":
    default_stocks = []
else:
    default_stocks = DEFAULT_SECTORS[selected_sector]

# Multiselect for modifying stocks in the chosen basket
selected_stocks = st.sidebar.multiselect(
    "Modify Stocks in Basket", 
    options=list(set(default_stocks + ["RELIANCE", "TCS", "INFY"])), 
    default=default_stocks
)

# Text input for adding brand new stocks not in the dropdown
new_stock = st.sidebar.text_input("Add Custom Stock (e.g., ZOMATO)").upper()
if st.sidebar.button("Add Stock") and new_stock:
    if new_stock not in selected_stocks:
        selected_stocks.append(new_stock)

# --- Data Fetching and Table Rendering ---
if selected_stocks:
    with st.spinner('Fetching market data and calculating indicators...'):
        results = []
        for stock in selected_stocks:
            data = fetch_and_calculate(stock)
            if data:
                results.append(data)
            else:
                st.sidebar.error(f"Failed to fetch data for {stock}. Check symbol.")

        if results:
            df_results = pd.DataFrame(results)
            
            # --- Styling the DataFrame ---
            color_cols = ['1D %', '3D %', '1W %', '2W %', '1M %', '2M %', '3M %', '6M %', '1Y %', '% Below 52W H', '% Above 52W L']
            
            def color_negative_red(val):
                if pd.isna(val):
                    return ''
                color = '#ff4b4b' if val < 0 else '#09ab3b'
                return f'color: {color}; font-weight: bold;'

            styled_df = df_results.style.format({
                col: "{:.2f}" for col in df_results.columns if col != 'Symbol'
            }).map(color_negative_red, subset=color_cols) # updated from applymap to map to avoid deprecation warnings

            st.dataframe(styled_df, use_container_width=True, height=600)
else:
    st.info("Please select or add stocks from the sidebar to view data.")

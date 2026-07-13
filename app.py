import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

# --- Page Configuration ---
st.set_page_config(page_title="NSE Historical EOD Tracker", layout="wide")

# --- Default Data ---
DEFAULT_SECTORS = {
    "My Watchlist": ["ASTRAL", "TATAMOTORS", "BANKBARODA", "PFC", "RECLTD", "HUDCO", "RVNL", "GODREJIND"],
    "Nifty 50": ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "BHARTIARTL", "ITC", "L&T"],
    "Nifty Bank": ["HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK", "PNB", "INDUSINDBK"],
    "Nifty IT": ["TCS", "INFY", "HCLTECH", "WIPRO", "TECHM", "LTIM", "PERSISTENT"]
}

# --- Core Calculation Function ---
@st.cache_data(show_spinner=False, ttl=86400) # Caches for 24 hours for EOD data
def fetch_and_calculate(ticker_symbol):
    try:
        # Clean symbol and append .NS for Indian stocks
        clean_symbol = ticker_symbol.replace('.NS', '').strip().upper()
        yf_symbol = f"{clean_symbol}.NS"
        
        # Fetch exactly 1 year of daily EOD data (approx 252 trading days)
        ticker = yf.Ticker(yf_symbol)
        df_raw = ticker.history(period="1y", interval="1d")
        
        if df_raw.empty:
            return {"Symbol": clean_symbol, "Error": "No data found"}
            
        close = df_raw['Close']
        high = df_raw['High']
        low = df_raw['Low']
        
        current_price = close.iloc[-1]
        
        # Trading day approximations for Indian Markets
        periods = {
            '1D %': 1, '3D %': 3, '1W %': 5, '2W %': 10, 
            '1M %': 21, '2M %': 42, '3M %': 63, '6M %': 126
        }
        
        returns = {}
        for label, days in periods.items():
            if len(close) > days:
                past_price = close.iloc[-(days+1)]
                returns[label] = ((current_price - past_price) / past_price) * 100
            else:
                returns[label] = np.nan
                
        # 1 Year return is just the first day in our 1y dataset vs today
        returns['1Y %'] = ((current_price - close.iloc[0]) / close.iloc[0]) * 100
                
        # Exponential Moving Averages
        ema4 = close.ewm(span=4, adjust=False).mean().iloc[-1]
        ema10 = close.ewm(span=10, adjust=False).mean().iloc[-1]
        ema20 = close.ewm(span=20, adjust=False).mean().iloc[-1]
        
        # 52 Week High/Low
        high_52w = high.max()
        low_52w = low.min()
        
        pct_below_high = ((current_price - high_52w) / high_52w) * 100
        pct_above_low = ((current_price - low_52w) / low_52w) * 100
        
        return {
            "Symbol": clean_symbol,
            "LTP (EOD)": current_price,
            **returns,
            "4 EMA": ema4,
            "10 EMA": ema10,
            "20 EMA": ema20,
            "52W High": high_52w,
            "% Below 52W H": pct_below_high, 
            "52W Low": low_52w,
            "% Above 52W L": pct_above_low,
            "Error": None
        }
    except Exception as e:
        return {"Symbol": ticker_symbol, "Error": str(e)}

# --- UI and Layout ---
st.title("📈 NSE Historical EOD Tracker")
st.markdown("Track absolute returns, EMAs, and 52-week extremes using reliable closing data.")

# Sidebar Configuration
st.sidebar.header("⚙️ Dashboard Controls")

selected_sector = st.sidebar.selectbox("Choose a Sector / Basket", list(DEFAULT_SECTORS.keys()) + ["Custom Basket"])

if selected_sector == "Custom Basket":
    default_stocks = []
else:
    default_stocks = DEFAULT_SECTORS[selected_sector]

selected_stocks = st.sidebar.multiselect(
    "Modify Stocks in Basket", 
    options=list(set(default_stocks + ["RELIANCE", "TCS", "INFY"])), 
    default=default_stocks
)

new_stock = st.sidebar.text_input("Add Custom Stock (e.g., ZOMATO)").upper()
if st.sidebar.button("Add Stock") and new_stock:
    if new_stock not in selected_stocks:
        selected_stocks.append(new_stock)

# --- Data Fetching with Progress Bar ---
if selected_stocks:
    results = []
    errors = []
    
    progress_text = st.empty()
    progress_bar = st.progress(0)
    total_stocks = len(selected_stocks)
    
    for index, stock in enumerate(selected_stocks):
        progress_text.text(f"Fetching reliable EOD data for: {stock} ({index + 1}/{total_stocks})...")
        
        data = fetch_and_calculate(stock)
        
        if data and data.get("Error") is None:
            data.pop("Error", None)
            results.append(data)
        elif data and data.get("Error"):
            errors.append(f"**{stock}**: {data['Error']}")
            
        progress_bar.progress((index + 1) / total_stocks)
        
    progress_text.empty()
    progress_bar.empty()

    if errors:
        st.error("⚠️ **Some stocks failed to load:**")
        for err in errors:
            st.write(err)

    if results:
        df_results = pd.DataFrame(results)
        
        color_cols = ['1D %', '3D %', '1W %', '2W %', '1M %', '2M %', '3M %', '6M %', '1Y %', '% Below 52W H', '% Above 52W L']
        existing_color_cols = [col for col in color_cols if col in df_results.columns]
        
        def color_negative_red(val):
            if pd.isna(val):
                return ''
            color = '#ff4b4b' if val < 0 else '#09ab3b'
            return f'color: {color}; font-weight: bold;'

        format_dict = {col: "{:.2f}" for col in df_results.columns if col != 'Symbol'}
        
        # Modern Pandas styling map
        if hasattr(df_results.style, 'map'):
            styled_df = df_results.style.format(format_dict).map(color_negative_red, subset=existing_color_cols)
        else:
            styled_df = df_results.style.format(format_dict).applymap(color_negative_red, subset=existing_color_cols)

        st.dataframe(styled_df, use_container_width=True, height=600)
else:
    st.info("Please select or add stocks from the sidebar to view data.")

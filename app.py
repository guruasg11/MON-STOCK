import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta
from jugaad_data.nse import stock_df

# --- Configuration ---
st.set_page_config(layout="wide")
st.title("📊 NSE Historical EOD Data Dashboard")

# --- Function: Fetch EOD Data ---
@st.cache_data(ttl=86400) # Caches data for 24 hours
def get_eod_data(symbol):
    try:
        # Fetch data for the last 1 year (252 trading days)
        end = date.today()
        start = end - timedelta(days=365)
        
        # Pulling only necessary columns
        df = stock_df(symbol=symbol.upper(), from_date=start, to_date=end, series="EQ")
        
        if df is None or df.empty:
            return None
            
        # Standardize columns
        df = df.rename(columns={'DATE': 'Date', 'CLOSE': 'Close', 'HIGH': 'High', 'LOW': 'Low'})
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        return df[['Date', 'Close', 'High', 'Low']]
    except:
        return None

# --- UI ---
ticker = st.text_input("Enter NSE Symbol (e.g. RELIANCE):", "RELIANCE").upper()

if st.button("Fetch Data"):
    with st.spinner(f"Downloading EOD data for {ticker}..."):
        df = get_eod_data(ticker)
        
        if df is not None:
            st.success("Data Retrieved Successfully")
            
            # Simple Calculations
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['52W High'] = df['High'].rolling(window=252).max()
            
            # Display
            st.dataframe(df.tail(30)) # Show last 30 days
            
            st.line_chart(df.set_index('Date')['Close'])
        else:
            st.error("Could not fetch data. Please check the symbol or try again later.")

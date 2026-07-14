import time
import random
from datetime import date

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="NSE EOD Tracker", layout="wide", page_icon="📈")

st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    .stDataFrame { border-radius: 8px; }
    h1 { font-size: 1.5rem !important; }
    h2 { font-size: 1.2rem !important; }
    .metric-box {
        background: #1e1e2e; border-radius: 8px; padding: 12px 16px;
        text-align: center; border: 1px solid #333;
    }
    .metric-box .val { font-size: 1.6rem; font-weight: 700; }
    .metric-box .lbl { font-size: 0.75rem; color: #aaa; margin-top: 2px; }
    .green { color: #00c853; }
    .red   { color: #ff1744; }
    .white { color: #ffffff; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECTOR UNIVERSE
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_SECTORS = {
    "My Watchlist":    ["ASTRAL","TATAMOTORS","BANKBARODA","PFC","RECLTD","HUDCO","RVNL","GODREJIND"],
    "Nifty 50":        ["RELIANCE","TCS","HDFCBANK","INFY","ICICIBANK","BHARTIARTL","ITC","LT",
                        "HINDUNILVR","SBIN","BAJFINANCE","KOTAKBANK","AXISBANK","ASIANPAINT",
                        "MARUTI","HCLTECH","SUNPHARMA","TITAN","WIPRO","ONGC","NTPC","POWERGRID",
                        "ULTRACEMCO","NESTLEIND","TECHM","INDUSINDBK","ADANIENT","ADANIPORTS",
                        "BAJAJFINSV","DRREDDY","DIVISLAB","CIPLA","BPCL","COALINDIA","HEROMOTOCO",
                        "M&M","TATASTEEL","JSWSTEEL","EICHERMOT","GRASIM"],
    "Nifty Bank":      ["HDFCBANK","ICICIBANK","SBIN","KOTAKBANK","AXISBANK","PNB","INDUSINDBK",
                        "BANDHANBNK","FEDERALBNK","IDFCFIRSTB","AUBANK","BANKBARODA"],
    "Nifty IT":        ["TCS","INFY","HCLTECH","WIPRO","TECHM","LTIM","PERSISTENT","MPHASIS","COFORGE","OFSS"],
    "Nifty Auto":      ["MARUTI","TATAMOTORS","M&M","BAJAJ-AUTO","HEROMOTOCO","EICHERMOT",
                        "BOSCHLTD","MRF","BALKRISIND","MOTHERSON","BHARATFORG","APOLLOTYRE"],
    "Nifty FMCG":      ["HINDUNILVR","ITC","NESTLEIND","BRITANNIA","DABUR","MARICO",
                        "COLPAL","GODREJCP","EMAMILTD","TATACONSUM","UBL","MCDOWELL-N"],
    "Nifty Pharma":    ["SUNPHARMA","DRREDDY","CIPLA","DIVISLAB","APOLLOHOSP","TORNTPHARM",
                        "ALKEM","AUROPHARMA","LUPIN","BIOCON","IPCALAB","GLENMARK"],
    "Nifty Metal":     ["TATASTEEL","JSWSTEEL","HINDALCO","COALINDIA","VEDL","SAIL",
                        "NMDC","APLAPOLLO","NATIONALUM","HINDCOPPER","MOIL","WELCORP"],
    "Nifty Realty":    ["DLF","GODREJPROP","OBEROIRLTY","PHOENIXLTD","PRESTIGE",
                        "BRIGADE","SOBHA","SUNTECK","KOLTEPATIL","MAHLIFE"],
    "Nifty Energy":    ["RELIANCE","ONGC","NTPC","POWERGRID","BPCL","IOC","GAIL",
                        "TATAPOWER","ADANIGREEN","ADANIPOWER","ADANITRANS","CESC"],
    "Nifty Infra":     ["LT","ADANIPORTS","POWERGRID","NTPC","BHARTIARTL","RVNL","IRFC",
                        "PFC","RECLTD","HUDCO","NBCC","IRB"],
    "Nifty PSU Bank":  ["SBIN","PNB","BANKBARODA","CANARABANK","UNIONBANK","BANKINDIA",
                        "CENTRALBK","UCOBANK","MAHABANK","INDIANB","IOB","J&KBANK"],
    "Nifty Midcap":    ["PERSISTENT","POLYCAB","INDIANB","FEDERALBNK","LTTS","MPHASIS",
                        "COFORGE","ABCAPITAL","SUNDARMFIN","VOLTAS","ASTRAL","PIIND",
                        "ZYDUSLIFE","MAXHEALTH","STARHEALTH","CAMS","ANGELONE","BSE","MCX","DIXON"],
    "Nifty Fin Svcs":  ["HDFCBANK","ICICIBANK","BAJFINANCE","KOTAKBANK","AXISBANK","SBIN",
                        "BAJAJFINSV","HDFCAMC","MUTHOOTFIN","CHOLAFIN","M&MFIN","LICHSGFIN"],
    "Nifty Oil & Gas": ["RELIANCE","ONGC","BPCL","IOC","GAIL","HINDPETRO","MGL","IGL",
                        "PETRONET","GSPL","CASTROLIND","AEGISCHEM"],
    "Custom Basket":   [],
}

SECTOR_INDEX = {
    "Nifty 50":       "^NSEI",
    "Nifty Bank":     "^NSEBANK",
    "Nifty IT":       "^CNXIT",
    "Nifty Auto":     "^CNXAUTO",
    "Nifty FMCG":     "^CNXFMCG",
    "Nifty Pharma":   "^CNXPHARMA",
    "Nifty Metal":    "^CNXMETAL",
    "Nifty Realty":   "^CNXREALTY",
    "Nifty Energy":   "^CNXENERGY",
    "Nifty Infra":    "^CNXINFRA",
    "Nifty PSU Bank": "^CNXPSUBANK",
    "Nifty Fin Svcs": "^CNXFIN",
    "Nifty Oil & Gas":"^CNXOILGAS",
}

# Large-cap NSE universe for Advance/Decline (~200 liquid stocks ≥ ₹1000 Cr mcap)
AD_UNIVERSE = [
    "RELIANCE","TCS","HDFCBANK","INFY","ICICIBANK","BHARTIARTL","ITC","LT",
    "HINDUNILVR","SBIN","BAJFINANCE","KOTAKBANK","AXISBANK","ASIANPAINT",
    "MARUTI","HCLTECH","SUNPHARMA","TITAN","WIPRO","ONGC","NTPC","POWERGRID",
    "ULTRACEMCO","NESTLEIND","TECHM","INDUSINDBK","ADANIENT","ADANIPORTS",
    "BAJAJFINSV","DRREDDY","DIVISLAB","CIPLA","BPCL","COALINDIA","HEROMOTOCO",
    "M&M","TATASTEEL","JSWSTEEL","EICHERMOT","GRASIM",
    "DMART","SIEMENS","HAVELLS","PIDILITIND","DABUR","MARICO","COLPAL",
    "GODREJCP","TATACONSUM","BRITANNIA","MUTHOOTFIN","CHOLAFIN",
    "SHREECEM","BERGEPAINT","TORNTPHARM","LUPIN","BIOCON","ALKEM","AUROPHARMA",
    "AMBUJACEM","GAIL","HINDPETRO","IOC","PETRONET","MGL","IGL",
    "DLF","GODREJPROP","OBEROIRLTY","PHOENIXLTD","PRESTIGE",
    "APOLLOHOSP","MAXHEALTH","FORTIS","LALPATHLAB","METROPOLIS",
    "PERSISTENT","POLYCAB","LTTS","MPHASIS","COFORGE","ZYDUSLIFE",
    "CAMS","ANGELONE","BSE","MCX","VOLTAS","ASTRAL","PIIND",
    "STARHEALTH","ABCAPITAL","SUNDARMFIN","FEDERALBNK",
    "IDFCFIRSTB","AUBANK","BANDHANBNK","PNB","BANKBARODA","CANARABANK",
    "UNIONBANK","BANKINDIA","CENTRALBK","INDIANB",
    "TATAMOTORS","PFC","RECLTD","HUDCO","RVNL","IRFC","RAILTEL","IRCON",
    "RITES","NBCC","HFCL","SUZLON","NHPC","SJVN","TATAPOWER",
    "ADANIGREEN","ADANIPOWER","CESC","JSWENERGY","TORNTPOWER",
    "BAJAJ-AUTO","BOSCHLTD","MRF","BALKRISIND","MOTHERSON","BHARATFORG","APOLLOTYRE",
    "VEDL","NMDC","APLAPOLLO","NATIONALUM","HINDCOPPER","MOIL","SAIL",
    "HDFCAMC","ICICIGI","HDFCLIFE","SBILIFE","M&MFIN","LICHSGFIN",
    "DIXON","AMBER","WHIRLPOOL","BLUESTAR","CROMPTON","VGUARD",
    "DELHIVERY","ZOMATO","NYKAA","PAYTM",
    "ABFRL","TRENT","RAYMOND","VEDANT",
    "UPL","COROMANDEL","CHAMBLFERT","DEEPAKNTR",
    "OFSS","KPITTECH","TATAELXSI","HAPPYMNDS","MASTEK","LTIM",
    "VARUNBEV","RADICO","UBL","MCDOWELL-N",
    "JUBLFOOD","DEVYANI",
    "KAJARIACER","CERA","GRINDWELL",
    "GODREJIND","EMAMILTD","IPCALAB","GLENMARK","BRIGADE","SOBHA",
    "WELCORP","ADANITRANS","IRB","GSPL","CASTROLIND","PIIND",
    "ZYDUSLIFE","MEDANTA","MAHABANK","IOB",
]
AD_UNIVERSE = list(dict.fromkeys(AD_UNIVERSE))   # deduplicate, preserve order


# ─────────────────────────────────────────────────────────────────────────────
# SESSION  (curl_cffi, created once)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_session():
    try:
        from curl_cffi import requests as cr
        return cr.Session(impersonate="chrome")
    except ImportError:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# FETCH + CALCULATE  (cached 24 h)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=86400)
def fetch_data(symbol, _session, is_index=False):
    """
    Returns dict with all metrics, or {"Symbol":..., "Error":...} on failure.

    Return-calculation fix
    ──────────────────────
    yfinance's daily history sometimes includes today as a partial (intraday)
    bar when the market is open.  We always drop any bar whose date == today
    so every calculation uses only fully-closed EOD candles.

    Correct indexing after the drop:
        iloc[-1]          → last closed EOD (yesterday if market open today)
        iloc[-2]          → one trading day before that  → 1D return
        iloc[-(N+1)]      → N trading days before last closed → ND return
    """
    yf_symbol = symbol if is_index else f"{symbol.replace('.NS','').upper()}.NS"
    try:
        t = yf.Ticker(yf_symbol, session=_session) if _session else yf.Ticker(yf_symbol)
        raw = t.history(period="1y", interval="1d", auto_adjust=True)
    except Exception as e:
        return {"Symbol": symbol, "Error": str(e)}

    if raw.empty:
        return {"Symbol": symbol, "Error": "No data"}

    # Drop today's partial bar
    today_str = date.today().isoformat()
    raw.index  = pd.to_datetime(raw.index)
    if str(raw.index[-1].date()) == today_str:
        raw = raw.iloc[:-1]

    if len(raw) < 10:
        return {"Symbol": symbol, "Error": "Insufficient history"}

    close = raw["Close"].astype(float)
    high  = raw["High"].astype(float)
    low   = raw["Low"].astype(float)

    ltp   = float(close.iloc[-1])         # last EOD close
    prev  = float(close.iloc[-2])         # previous EOD close

    # ── Returns ──────────────────────────────────────────────────────────────
    # N-day return = (ltp - close N trading days ago) / close N trading days ago
    # "N trading days ago" = iloc[-(N+1)] because iloc[-1] is ltp itself.
    def ret(n):
        if len(close) <= n:
            return np.nan
        return ((ltp - float(close.iloc[-(n + 1)])) / float(close.iloc[-(n + 1)])) * 100

    # ── EMAs ─────────────────────────────────────────────────────────────────
    def ema(span):
        return float(close.ewm(span=span, adjust=False).mean().iloc[-1])

    e4, e10, e20, e50, e100 = ema(4), ema(10), ema(20), ema(50), ema(100)

    # ── 52-week extremes ─────────────────────────────────────────────────────
    h52 = float(high.max())
    l52 = float(low.min())

    # % vs 52W High:  positive → above high (breakout), negative → below high
    pct_vs_h52 = ((ltp - h52) / h52) * 100
    # % vs 52W Low:   positive → above low (safe), negative → below low (rare)
    pct_vs_l52 = ((ltp - l52) / l52) * 100

    label = symbol if is_index else symbol.replace(".NS","").upper()

    return {
        "Symbol":       label,
        "LTP":          ltp,
        "1D %":         ret(1),
        "3D %":         ret(3),
        "1W %":         ret(5),
        "2W %":         ret(10),
        "1M %":         ret(21),
        "2M %":         ret(42),
        "3M %":         ret(63),
        "6M %":         ret(126),
        "1Y %":         ret(251),
        "4 EMA":        e4,
        "10 EMA":       e10,
        "20 EMA":       e20,
        "50 EMA":       e50,
        "100 EMA":      e100,
        "52W High":     h52,
        "vs 52W H %":   pct_vs_h52,   # + above high (green), - below high (red)
        "52W Low":      l52,
        "vs 52W L %":   pct_vs_l52,   # + above low  (green), - below low  (red)
        "Error":        None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# COLOUR HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def cell_bg(val, cap=20):
    """White at 0, deep green at +cap, deep red at -cap. Background only."""
    if pd.isna(val):
        return ""
    i = min(abs(val) / cap, 1.0)
    if val >= 0:
        r = int(255 - i * 195); g = int(255 - i * 55);  b = int(255 - i * 195)
    else:
        r = int(255 - i * 35);  g = int(255 - i * 205); b = int(255 - i * 205)
    return f"background-color: rgb({r},{g},{b}); color: #000; font-weight: 600;"


def style_df(df, pct_cols, cap=20):
    fmt = {c: "{:.2f}" for c in df.columns if c not in ("Symbol",)}
    existing = [c for c in pct_cols if c in df.columns]
    styler = df.style.format(fmt, na_rep="—")
    fn = styler.map if hasattr(styler, "map") else styler.applymap
    return fn(lambda v: cell_bg(v, cap), subset=existing)


# ─────────────────────────────────────────────────────────────────────────────
# ADVANCE / DECLINE FETCH  (light – only needs 110 days of daily data)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=3600)
def fetch_ad_stock(symbol, _session):
    """Returns (ltp, prev_close, e4, e10, e20, e50, e100, h52, l52) or None."""
    yf_sym = f"{symbol.upper()}.NS"
    try:
        t   = yf.Ticker(yf_sym, session=_session) if _session else yf.Ticker(yf_sym)
        raw = t.history(period="1y", interval="1d", auto_adjust=True)
    except Exception:
        return None

    if raw.empty or len(raw) < 10:
        return None

    raw.index = pd.to_datetime(raw.index)
    if str(raw.index[-1].date()) == date.today().isoformat():
        raw = raw.iloc[:-1]

    if len(raw) < 10:
        return None

    close = raw["Close"].astype(float)
    high  = raw["High"].astype(float)
    low   = raw["Low"].astype(float)

    def ema(s): return float(close.ewm(span=s, adjust=False).mean().iloc[-1])

    ltp  = float(close.iloc[-1])
    prev = float(close.iloc[-2]) if len(close) > 1 else ltp

    return {
        "ltp":   ltp,
        "prev":  prev,
        "e4":    ema(4),
        "e10":   ema(10),
        "e20":   ema(20),
        "e50":   ema(50),
        "e100":  ema(100),
        "h52":   float(high.max()),
        "l52":   float(low.min()),
    }


# ─────────────────────────────────────────────────────────────────────────────
# UI – SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
if "custom_stocks" not in st.session_state:
    st.session_state.custom_stocks = []

st.sidebar.title("⚙️ Settings")
page = st.sidebar.radio("View", ["📊 Sector Tracker", "📈 Advance / Decline"])

st.title("📈 NSE EOD Tracker")

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 1 – SECTOR TRACKER
# ─────────────────────────────────────────────────────────────────────────────
if page == "📊 Sector Tracker":

    sector_names = [s for s in DEFAULT_SECTORS if s != "Custom Basket"] + ["Custom Basket"]
    sel_sector   = st.sidebar.selectbox("Sector / Basket", sector_names)
    def_stocks   = DEFAULT_SECTORS.get(sel_sector, [])

    all_opts = sorted(set(def_stocks + st.session_state.custom_stocks + ["RELIANCE","TCS","INFY"]))
    ms_def   = st.session_state.custom_stocks if sel_sector == "Custom Basket" else def_stocks

    sel_stocks = st.sidebar.multiselect("Stocks", options=all_opts, default=ms_def)

    new_s = st.sidebar.text_input("Add stock (e.g. ZOMATO)").upper().strip()
    c1, c2 = st.sidebar.columns(2)
    with c1:
        if st.button("➕ Add") and new_s:
            if new_s not in st.session_state.custom_stocks:
                st.session_state.custom_stocks.append(new_s)
                st.rerun()
    with c2:
        if st.button("🗑 Clear"):
            st.session_state.custom_stocks = []
            st.rerun()

    final = list(dict.fromkeys(sel_stocks + st.session_state.custom_stocks))

    if not final:
        st.info("Select stocks from the sidebar.")
        st.stop()

    session = get_session()

    # Sector index row
    idx_sym  = SECTOR_INDEX.get(sel_sector)
    idx_row  = None
    if idx_sym:
        with st.spinner("Fetching sector index…"):
            d = fetch_data(idx_sym, session, is_index=True)
            if d and not d.get("Error"):
                d.pop("Error", None)
                d["Symbol"] = f"▶ {sel_sector} INDEX"
                idx_row = d

    # Stock rows
    results, errors = [], []
    bar  = st.progress(0)
    info = st.empty()
    for i, sym in enumerate(final):
        info.text(f"Fetching {sym}  ({i+1}/{len(final)})")
        try:
            d = fetch_data(sym, session)
        except Exception as e:
            d = {"Symbol": sym, "Error": str(e)}
        if d and not d.get("Error"):
            d.pop("Error", None)
            results.append(d)
        else:
            errors.append(f"**{sym}**: {d.get('Error','unknown')}")
        bar.progress((i + 1) / len(final))
        if i < len(final) - 1:
            time.sleep(0.12 + random.random() * 0.1)
    bar.empty(); info.empty()

    if errors:
        with st.expander(f"⚠️ {len(errors)} stock(s) skipped"):
            for e in errors: st.write(e)

    if not results:
        st.warning("No data fetched.")
        st.stop()

    df = pd.DataFrame(results)
    num_cols = [c for c in df.columns if c != "Symbol"]

    # Sector average row
    avg = {"Symbol": f"📊 {sel_sector} AVG"}
    avg.update(df[num_cols].mean(numeric_only=True).to_dict())

    frames = []
    if idx_row:
        frames.append(pd.DataFrame([idx_row]))
    frames.append(pd.DataFrame([avg]))
    frames.append(df)
    df_all = pd.concat(frames, ignore_index=True)

    # Columns where positive = green, negative = red
    PCT_COLS = ["1D %","3D %","1W %","2W %","1M %","2M %","3M %","6M %","1Y %",
                "vs 52W H %","vs 52W L %"]

    st.subheader(f"{sel_sector} — {len(final)} stocks")
    st.dataframe(style_df(df_all, PCT_COLS), use_container_width=True, height=620)
    st.caption("🟢 green = positive / above  |  🔴 red = negative / below  |  EMA & 52W price columns shown for reference")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 2 – ADVANCE / DECLINE
# ─────────────────────────────────────────────────────────────────────────────
else:
    st.subheader("📈 Market Advance / Decline Dashboard")
    st.markdown("Universe: ~200 NSE stocks with market cap ≥ ₹1000 Cr")

    run = st.button("🔄 Fetch / Refresh  (takes ~2–3 min)")

    if "ad_data" not in st.session_state:
        st.session_state.ad_data = None

    if run:
        session = get_session()
        rows = []
        bar  = st.progress(0)
        info = st.empty()
        total = len(AD_UNIVERSE)
        for i, sym in enumerate(AD_UNIVERSE):
            info.text(f"A/D: fetching {sym}  ({i+1}/{total})")
            try:
                d = fetch_ad_stock(sym, session)
            except Exception:
                d = None
            if d:
                rows.append({"Symbol": sym, **d})
            bar.progress((i + 1) / total)
            time.sleep(0.10 + random.random() * 0.08)
        bar.empty(); info.empty()
        st.session_state.ad_data = rows

    if not st.session_state.ad_data:
        st.info("Click **Fetch / Refresh** to load market breadth data.")
        st.stop()

    rows = st.session_state.ad_data
    total = len(rows)

    # ── Summary metrics ───────────────────────────────────────────────────────
    def count_above(field, key):
        return sum(1 for r in rows if r.get(key) is not None and r["ltp"] > r[key])

    a4   = count_above("ltp","e4");   b4   = total - a4
    a10  = count_above("ltp","e10");  b10  = total - a10
    a20  = count_above("ltp","e20");  b20  = total - a20
    a50  = count_above("ltp","e50");  b50  = total - a50
    a100 = count_above("ltp","e100"); b100 = total - a100

    a52h = sum(1 for r in rows if r["ltp"] >= r["h52"] * 0.95)  # within 5% of 52W high
    near52l = sum(1 for r in rows if r["ltp"] <= r["l52"] * 1.05)  # within 5% of 52W low
    at52h = sum(1 for r in rows if r["ltp"] >= r["h52"])
    at52l = sum(1 for r in rows if r["ltp"] <= r["l52"])

    adv   = sum(1 for r in rows if r["ltp"] > r["prev"])
    dec   = sum(1 for r in rows if r["ltp"] < r["prev"])
    unch  = total - adv - dec

    def metric_html(val, label, pos_col="green"):
        col = pos_col if isinstance(val, int) else "white"
        return f'<div class="metric-box"><div class="val {pos_col}">{val}</div><div class="lbl">{label}</div></div>'

    # Row 1 – Adv / Dec
    st.markdown("#### Today's Breadth")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(metric_html(adv, "Advancing"), unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-box"><div class="val red">{dec}</div><div class="lbl">Declining</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-box"><div class="val white">{unch}</div><div class="lbl">Unchanged</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-box"><div class="val white">{total}</div><div class="lbl">Total Tracked</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    # Row 2 – EMA breadth
    st.markdown("#### Stocks Above EMA")
    cols = st.columns(5)
    for col, above, below, label in zip(
        cols,
        [a4,  a10,  a20,  a50,  a100],
        [b4,  b10,  b20,  b50,  b100],
        ["4-EMA","10-EMA","20-EMA","50-EMA","100-EMA"]
    ):
        pct = round(above / total * 100, 1) if total else 0
        col.markdown(f"""
        <div class="metric-box">
            <div class="val {'green' if above > below else 'red'}">{above} <span style="font-size:0.9rem">/ {total}</span></div>
            <div class="lbl">{label}  ({pct}%)</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Row 3 – 52W extremes
    st.markdown("#### 52-Week Extremes")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="metric-box"><div class="val green">{at52h}</div><div class="lbl">At / Above 52W High</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-box"><div class="val green">{a52h}</div><div class="lbl">Within 5% of 52W High</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-box"><div class="val red">{at52l}</div><div class="lbl">At / Below 52W Low</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-box"><div class="val red">{near52l}</div><div class="lbl">Within 5% of 52W Low</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Detailed table ────────────────────────────────────────────────────────
    st.markdown("#### Stock Detail")

    detail_rows = []
    for r in rows:
        ltp = r["ltp"]
        chg = ((ltp - r["prev"]) / r["prev"] * 100) if r["prev"] else 0
        detail_rows.append({
            "Symbol":       r["Symbol"],
            "LTP":          round(ltp, 2),
            "Day Chg %":    round(chg, 2),
            ">4EMA":        "✅" if ltp > r["e4"]   else "❌",
            "4EMA":         round(r["e4"],  2),
            ">10EMA":       "✅" if ltp > r["e10"]  else "❌",
            "10EMA":        round(r["e10"], 2),
            ">20EMA":       "✅" if ltp > r["e20"]  else "❌",
            "20EMA":        round(r["e20"], 2),
            ">50EMA":       "✅" if ltp > r["e50"]  else "❌",
            "50EMA":        round(r["e50"], 2),
            ">100EMA":      "✅" if ltp > r["e100"] else "❌",
            "100EMA":       round(r["e100"],2),
            "vs 52W H %":   round(((ltp - r["h52"]) / r["h52"]) * 100, 2),
            "vs 52W L %":   round(((ltp - r["l52"]) / r["l52"]) * 100, 2),
        })

    df_ad = pd.DataFrame(detail_rows)

    # colour only the numeric pct columns
    ad_pct_cols = ["Day Chg %", "vs 52W H %", "vs 52W L %"]
    fmt_ad = {c: "{:.2f}" for c in df_ad.columns if c not in ("Symbol",">4EMA",">10EMA",">20EMA",">50EMA",">100EMA","4EMA","10EMA","20EMA","50EMA","100EMA")}

    styler_ad = df_ad.style.format(fmt_ad)
    fn = styler_ad.map if hasattr(styler_ad, "map") else styler_ad.applymap
    styler_ad = fn(lambda v: cell_bg(v, 10), subset=[c for c in ad_pct_cols if c in df_ad.columns])

    st.dataframe(styler_ad, use_container_width=True, height=600)
    st.caption(f"Data cached for 1 hour. Fetched {total} stocks.  🟢 = above EMA  |  ❌ = below EMA")

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import io
import re
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, HRFlowable, 
                                KeepTogether, Image as RLImage)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY

# ── CONFIG & DESIGN TOKENS ──────────────────────────────────────────────────
API_KEY = "73d3049608e044f1a63182f51656c760"
BASE_URL = "https://api.roic.ai/v2"
SEC_HDRS = {"User-Agent": "compounder-app research@apple.com"}

STOCKS = {
    "Ryanair": "RYAAY", "Copart": "CPRT", "Constellation Software": "CSU.TO",
    "Fair Isaac": "FICO", "S&P Global": "SPGI", "Moody's": "MCO", "ASML": "ASML"
}

C = {"BG": "#FFFFFF", "TEXT": "#111111", "TEXT2": "#555555", "TEXT3": "#999999", 
     "BORDER": "#E8E8E8", "ACCENT": "#111111", "UP": "#1A7F4B", "DOWN": "#C0392B"}

# ── DATA UTILITIES ──────────────────────────────────────────────────────────

def fmt_money(v, ccy="$"):
    if pd.isna(v) or v is None: return "—"
    neg, v = ("-", abs(v)) if v < 0 else ("", abs(v))
    if v >= 1e12: return f"{neg}{ccy}{v/1e12:.1f}T"
    if v >= 1e9:  return f"{neg}{ccy}{v/1e9:.1f}B"
    if v >= 1e6:  return f"{neg}{ccy}{v/1e6:.0f}M"
    return f"{neg}{ccy}{v:,.0f}"

def get_ccy_sym(code):
    return {"USD":"$", "EUR":"€", "GBP":"£", "CAD":"C$", "JPY":"¥"}.get(str(code).upper(), f"{code} ")

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_data(endpoint, ticker):
    try:
        r = requests.get(f"{BASE_URL}/{endpoint}/{ticker}", 
                         params={"period": "annual", "limit": 20, "apikey": API_KEY}, timeout=15)
        res = r.json()
        rows = res if isinstance(res, list) else res.get("data", [])
        if not rows: return pd.DataFrame()
        df = pd.DataFrame(rows)
        for c in ["date", "Date", "period_end"]:
            if c in df.columns:
                df["Date"] = pd.to_datetime(df[c], errors="coerce")
                break
        numeric_cols = df.columns.difference({"Date", "ticker", "currency", "period"})
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
        return df.sort_values("Date").reset_index(drop=True)
    except: return pd.DataFrame()

# ── SEC FILING ENGINE ────────────────────────────────────────────────────────

@st.cache_data(ttl=86400)
def get_sec_filing(ticker):
    try:
        r = requests.get("https://www.sec.gov/files/company_tickers.json", headers=SEC_HDRS).json()
        cik = next((str(v["cik_str"]).zfill(10) for v in r.values() if v["ticker"] == ticker.upper()), None)
        if not cik: return None
        meta = requests.get(f"https://data.sec.gov/submissions/CIK{cik}.json", headers=SEC_HDRS).json()
        f = meta.get("filings", {}).get("recent", {})
        for i, form in enumerate(f.get("form", [])):
            if form in ["10-K", "20-F"]:
                acc = f["accessionNumber"][i].replace("-", "")
                idx_page = requests.get(f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/{f['accessionNumber'][i]}-index.htm", headers=SEC_HDRS).text
                doc = re.search(r'href="(/Archives/edgar/data/.*?\.htm)"', idx_page, re.I)
                if doc:
                    raw = requests.get(f"https://www.sec.gov{doc.group(1)}", headers=SEC_HDRS).text
                    return {"text": re.sub(r'<[^>]+>', ' ', raw)[5000:80000], "form": form, "date": f["filingDate"][i]}
    except: pass
    return None

# ── UI & STYLING ─────────────────────────────────────────────────────────────

st.set_page_config(page_title="Compounder", layout="wide")
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; background: {C['BG']}; }}
    .metric-card {{ padding: 1.5rem 0; border-bottom: 1px solid {C['BORDER']}; }}
    .stTabs [data-baseweb="tab"] {{ font-size: 0.85rem; font-weight: 600; color: {C['TEXT3']}; }}
    .stTabs [aria-selected="true"] {{ color: {C['TEXT']} !important; border-bottom: 2px solid {C['TEXT']} !important; }}
</style>
""", unsafe_allow_html=True)

# ── MAIN APP ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("Compounder")
    nav = st.radio("Nav", ["Overview", "Deep Dive"], label_visibility="collapsed")
    ticker = st.text_input("Ticker", value="ASML").upper()

if nav == "Overview":
    st.header("Watchlist Summary")
    # Vectorized summary logic
    data_list = []
    for name, t in STOCKS.items():
        df = fetch_data("fundamental/income-statement", t)
        if not df.empty:
            rev = df.get("is_sales_revenue_turnover", df.get("is_sales_and_services_revenues", pd.Series()))
            data_list.append({"Company": name, "Ticker": t, "Revenue": fmt_money(rev.iloc[-1]), "Margin": f"{(df['is_net_income'].iloc[-1]/rev.iloc[-1])*100:.1f}%"})
    st.table(pd.DataFrame(data_list))

else:
    inc, bs, cf = fetch_data("fundamental/income-statement", ticker), fetch_data("fundamental/balance-sheet", ticker), fetch_data("fundamental/cash-flow", ticker)
    
    if not inc.empty:
        rev = inc.get("is_sales_revenue_turnover", inc.get("is_sales_and_services_revenues", pd.Series()))
        ni = inc["is_net_income"]
        ccy = get_ccy_sym(inc["currency"].iloc[-1])

        st.subheader(f"{ticker} Deep Dive")
        k1, k2, k3, k4 = st.columns(4)
        
        # Metric Components
        def m_card(col, label, val, d=None):
            delta_html = f'<div style="color:{C["UP"] if d>0 else C["DOWN"]}; font-size:0.7rem">{"↑" if d>0 else "↓"} {abs(d):.1f}%</div>' if d else ""
            col.markdown(f'<div class="metric-card"><div style="color:{C["TEXT3"]}; font-size:0.6rem; text-transform:uppercase">{label}</div><div style="font-size:1.5rem; font-weight:600">{val}</div>{delta_html}</div>', unsafe_allow_html=True)

        m_card(k1, "Revenue", fmt_money(rev.iloc[-1], ccy), ((rev.iloc[-1]/rev.iloc[-2])-1)*100 if len(rev)>1 else None)
        m_card(k2, "Net Income", fmt_money(ni.iloc[-1], ccy))
        m_card(k3, "Net Margin", f"{(ni.iloc[-1]/rev.iloc[-1])*100:.1f}%")
        m_card(k4, "Free Cash Flow", fmt_money(cf["cf_free_cash_flow"].iloc[-1] if not cf.empty else 0, ccy))

        t1, t2 = st.tabs(["Charts", "Research Report"])
        with t1:
            fig = go.Figure(go.Scatter(x=inc["Date"], y=rev, mode='lines+markers', line=dict(color=C['ACCENT'], width=3)))
            fig.update_layout(height=400, template="plotly_white", title="Revenue Trend")
            st.plotly_chart(fig, use_container_width=True)
            
        with t2:
            if st.button("Generate Report"):
                sec = get_sec_filing(ticker)
                st.markdown(f"### Analyst Insight\nFound {sec['form'] if sec else 'Financial Statements'}. Processing...")
                st.write(sec["text"][:2000] if sec else "No filing found.")
    else:
        st.error("Ticker not found in database.")

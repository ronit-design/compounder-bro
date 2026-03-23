import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests

# ── Google Sheets Config ──────────────────────────────────────────────────────
SHEET_ID = "1zxw8jiuaeNDJelyUNrJ4H91NqOluwvJ7dl5p6MPKWRI"

def sheet_url(gid):
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"

SHEET_INCOME = sheet_url(0)
SHEET_BS     = sheet_url(1653631279)
SHEET_CF     = sheet_url(1757000096)

STOCKS = {
    "Ryanair":                "RYAAY",
    "Copart":                 "CPRT",
    "Constellation Software": "CSU.TO",
    "Fair Isaac (FICO)":      "FICO",
    "S&P Global":             "SPGI",
    "Moody's":                "MCO",
    "ASML":                   "ASML",
}

# roic.ai for live stock prices only
API_KEY  = "73d3049608e044f1a63182f51656c760"
BASE_URL = "https://api.roic.ai/v2"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Compounder Bro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background-color: #0e1117; }
    .metric-card {
        background: linear-gradient(135deg, #1e2433 0%, #252d40 100%);
        border: 1px solid #2e3a52;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 12px;
    }
    .metric-label { color: #8892a4; font-size: 12px; font-weight: 500;
        text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px; }
    .metric-value { color: #ffffff; font-size: 26px; font-weight: 700; line-height: 1.1; }
    .metric-delta-pos { color: #22c55e; font-size: 13px; font-weight: 500; }
    .metric-delta-neg { color: #ef4444; font-size: 13px; font-weight: 500; }
    .section-header { color: #e2e8f0; font-size: 18px; font-weight: 600;
        margin: 28px 0 16px 0; padding-bottom: 8px; border-bottom: 1px solid #2e3a52; }
    .company-header { background: linear-gradient(90deg, #1a237e 0%, #0d47a1 100%);
        border-radius: 12px; padding: 24px 32px; margin-bottom: 24px; }
    .company-name { color: #ffffff; font-size: 28px; font-weight: 700; }
    .company-ticker { display: inline-block; background: rgba(255,255,255,0.15);
        color: #90caf9; font-size: 14px; font-weight: 600; padding: 3px 10px;
        border-radius: 20px; margin-left: 10px; }
    div[data-testid="stSidebarContent"] { background-color: #131722; }
    .sidebar-title { color: #f0a500; font-size: 22px; font-weight: 700; margin-bottom: 4px; }
    .sidebar-sub { color: #8892a4; font-size: 12px; margin-bottom: 24px; }
    footer { visibility: hidden; }
    #MainMenu { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Data loaders ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def load_sheet(url):
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        df = df[df["Ticker"] != "Ticker"].reset_index(drop=True)
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        for col in df.columns:
            if col not in ["Ticker", "Date", "Period", "Period Label", "Currency"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    except Exception as e:
        st.error(f"Failed to load Google Sheet: {e}")
        return pd.DataFrame()

def get_ticker_data(df, ticker):
    if df.empty or "Ticker" not in df.columns:
        return pd.DataFrame()
    out = df[df["Ticker"] == ticker].copy()
    if "Date" in out.columns:
        out = out.sort_values("Date")
    return out.reset_index(drop=True)

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_prices(ticker):
    url = f"{BASE_URL}/stock-prices/{ticker}"
    params = {"limit": 100000, "order": "asc", "format": "json", "apikey": API_KEY}
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        df = pd.DataFrame(data if isinstance(data, list) else data.get("data", []))
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
        return df
    except:
        return pd.DataFrame()


# ── Helpers ───────────────────────────────────────────────────────────────────
def safe(df, *cols):
    for c in cols:
        if c in df.columns:
            return pd.to_numeric(df[c], errors="coerce")
    return pd.Series(dtype=float)

def latest(s):
    v = s.dropna()
    return float(v.iloc[-1]) if len(v) > 0 else None

def prev(s):
    v = s.dropna()
    return float(v.iloc[-2]) if len(v) > 1 else None

def yoy(l, p):
    if l is not None and p is not None and p != 0:
        return (l - p) / abs(p) * 100
    return None

def fmt_large(val):
    try:
        v = float(val)
        if pd.isna(v): return "—"
        if abs(v) >= 1e12: return f"${v/1e12:.2f}T"
        if abs(v) >= 1e9:  return f"${v/1e9:.2f}B"
        if abs(v) >= 1e6:  return f"${v/1e6:.2f}M"
        return f"${v:,.0f}"
    except: return "—"

def fmt_pct(val):
    try:
        v = float(val)
        if pd.isna(v): return "—"
        if abs(v) <= 1: v *= 100
        return f"{v:.1f}%"
    except: return "—"

def to_pct_list(s):
    out = []
    for v in s:
        try:
            v = float(v)
            out.append(v * 100 if abs(v) <= 1 else v)
        except:
            out.append(None)
    return out


# ── Chart helpers ─────────────────────────────────────────────────────────────
COLORS = ["#4a9eff", "#22c55e", "#f0a500", "#e879f9", "#fb923c", "#34d399", "#f87171"]

BASE_LAYOUT = dict(
    paper_bgcolor="#1e2433", plot_bgcolor="#1e2433",
    font=dict(color="#8892a4", family="Inter"),
    xaxis=dict(showgrid=False, color="#8892a4"),
    yaxis=dict(showgrid=True, gridcolor="#2e3a52", color="#8892a4"),
    margin=dict(l=10, r=10, t=40, b=10),
    hovermode="x unified",
    legend=dict(bgcolor="#1e2433", bordercolor="#2e3a52", borderwidth=1),
)

def bar_chart(x, y, title, color="#4a9eff", height=300):
    y_safe = [v if v is not None and not pd.isna(v) else 0 for v in y]
    colors = [color if v >= 0 else "#ef4444" for v in y_safe]
    fig = go.Figure(go.Bar(x=x, y=y_safe, marker_color=colors,
                           hovertemplate=f"%{{x}}<br>{title}: %{{y:,.2f}}<extra></extra>"))
    fig.update_layout(**BASE_LAYOUT,
                      title=dict(text=title, font=dict(color="#e2e8f0", size=14)),
                      height=height)
    return fig

def line_chart(x, ys, names, title, height=320):
    fig = go.Figure()
    for i, (y, name) in enumerate(zip(ys, names)):
        fig.add_trace(go.Scatter(
            x=x, y=y, name=name, mode="lines+markers",
            line=dict(color=COLORS[i % len(COLORS)], width=2),
            marker=dict(size=5),
        ))
    fig.update_layout(**BASE_LAYOUT,
                      title=dict(text=title, font=dict(color="#e2e8f0", size=14)),
                      height=height)
    return fig

def kpi(col, label, val_str, delta=None):
    if delta is not None:
        sign = "▲" if delta >= 0 else "▼"
        cls  = "metric-delta-pos" if delta >= 0 else "metric-delta-neg"
        d_html = f'<div class="{cls}">{sign} {abs(delta):.1f}% YoY</div>'
    else:
        d_html = ""
    col.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{val_str}</div>
        {d_html}
    </div>""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-title">📊 Compounder Bro</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-sub">7 High-Quality Compounders</div>', unsafe_allow_html=True)

    page = st.radio("Navigation", ["🏠 Dashboard", "🔍 Company Deep Dive"],
                    label_visibility="collapsed")

    if page == "🔍 Company Deep Dive":
        selected = st.selectbox("Select Company", list(STOCKS.keys()))

    st.markdown("---")
    st.markdown('<div style="color:#8892a4;font-size:11px;">Source: Your Google Sheet<br>Cached for 30 minutes</div>',
                unsafe_allow_html=True)
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()


# ── Load sheets ───────────────────────────────────────────────────────────────
with st.spinner("Loading from Google Sheets..."):
    inc_all = load_sheet(SHEET_INCOME)
    bs_all  = load_sheet(SHEET_BS)
    cf_all  = load_sheet(SHEET_CF)


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Dashboard":
    st.markdown("## 📊 Compounder Dashboard")
    st.markdown("*All 7 compounders at a glance — select Company Deep Dive to explore further*")
    st.markdown("---")

    rows = []
    for company, ticker in STOCKS.items():
        inc = get_ticker_data(inc_all, ticker)
        cf  = get_ticker_data(cf_all,  ticker)
        if inc.empty:
            rows.append({"Company": company, "Ticker": ticker}); continue

        rev_s = safe(inc, "Sales Revenue", "Revenue")
        rev_l = latest(rev_s); rev_p = prev(rev_s)
        rows.append({
            "Company":      company,
            "Ticker":       ticker,
            "Revenue":      rev_l,
            "Rev Growth":   yoy(rev_l, rev_p),
            "Gross Margin": latest(safe(inc, "Gross Margin")),
            "Op Margin":    latest(safe(inc, "Operating Margin")),
            "Net Margin":   latest(safe(inc, "Profit Margin")),
            "FCF":          latest(safe(cf, "Free Cash Flow")) if not cf.empty else None,
        })

    # At a glance table
    st.markdown('<div class="section-header">📋 At a Glance</div>', unsafe_allow_html=True)
    hcols = st.columns([2, 1, 1.3, 1.2, 1.2, 1.2, 1.2])
    for col, h in zip(hcols, ["Company", "Ticker", "Revenue", "Rev Growth",
                               "Gross Margin", "Op Margin", "Net Margin"]):
        col.markdown(f"**{h}**")
    st.markdown("---")

    for row in rows:
        c = st.columns([2, 1, 1.3, 1.2, 1.2, 1.2, 1.2])
        c[0].markdown(f"**{row['Company']}**")
        c[1].markdown(f"`{row['Ticker']}`")
        c[2].markdown(fmt_large(row.get("Revenue")))
        rg = row.get("Rev Growth")
        c[3].markdown(f"{'🟢' if rg and rg>=0 else '🔴'} {abs(rg):.1f}%" if rg is not None else "—")
        c[4].markdown(fmt_pct(row.get("Gross Margin")))
        c[5].markdown(fmt_pct(row.get("Op Margin")))
        c[6].markdown(fmt_pct(row.get("Net Margin")))

    # Revenue bar
    st.markdown('<div class="section-header">📈 Revenue Comparison (Latest Year)</div>', unsafe_allow_html=True)
    rev_data = [(r["Company"], r["Revenue"]) for r in rows if r.get("Revenue")]
    if rev_data:
        names_r, vals_r = zip(*rev_data)
        fig = go.Figure(go.Bar(
            x=list(names_r), y=[v/1e9 for v in vals_r],
            marker_color=COLORS[:len(names_r)],
            hovertemplate="%{x}<br>Revenue: $%{y:.2f}B<extra></extra>",
        ))
        fig.update_layout(**BASE_LAYOUT, height=320, showlegend=False,
                          yaxis=dict(title="Revenue ($B)", showgrid=True,
                                     gridcolor="#2e3a52", color="#8892a4"))
        st.plotly_chart(fig, use_container_width=True)

    # Margins comparison
    st.markdown('<div class="section-header">💰 Margin Comparison</div>', unsafe_allow_html=True)
    mcos = [r["Company"]    for r in rows if r.get("Gross Margin") is not None]
    gms  = [to_pct_list([r["Gross Margin"]])[0] for r in rows if r.get("Gross Margin") is not None]
    ops  = [to_pct_list([r["Op Margin"]])[0]    for r in rows if r.get("Op Margin")    is not None]
    nms  = [to_pct_list([r["Net Margin"]])[0]   for r in rows if r.get("Net Margin")   is not None]

    if mcos:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="Gross Margin",     x=mcos, y=gms, marker_color="#4a9eff"))
        fig2.add_trace(go.Bar(name="Operating Margin", x=mcos, y=ops, marker_color="#22c55e"))
        fig2.add_trace(go.Bar(name="Net Margin",       x=mcos, y=nms, marker_color="#f0a500"))
        fig2.update_layout(**BASE_LAYOUT, barmode="group", height=350,
                           yaxis=dict(title="Margin (%)", showgrid=True,
                                      gridcolor="#2e3a52", color="#8892a4"))
        st.plotly_chart(fig2, use_container_width=True)

    st.info("👈 Select **Company Deep Dive** in the sidebar to explore any company in detail.")


# ══════════════════════════════════════════════════════════════════════════════
# COMPANY DEEP DIVE
# ══════════════════════════════════════════════════════════════════════════════
else:
    ticker = STOCKS[selected]

    st.markdown(f"""
    <div class="company-header">
        <span class="company-name">{selected}</span>
        <span class="company-ticker">{ticker}</span>
    </div>""", unsafe_allow_html=True)

    inc = get_ticker_data(inc_all, ticker)
    bs  = get_ticker_data(bs_all,  ticker)
    cf  = get_ticker_data(cf_all,  ticker)

    if inc.empty:
        st.error(f"No data found for **{ticker}** in the Google Sheet. Check the ticker matches exactly.")
        st.stop()

    years    = inc["Date"].dt.year.astype(str).tolist() if "Date" in inc.columns else [str(i) for i in range(len(inc))]
    cf_years = cf["Date"].dt.year.astype(str).tolist()  if not cf.empty and "Date" in cf.columns else years

    rev_s    = safe(inc, "Sales Revenue", "Revenue")
    ni_s     = safe(inc, "Net Income")
    oi_s     = safe(inc, "Operating Income")
    gm_s     = safe(inc, "Gross Margin")
    opm_s    = safe(inc, "Operating Margin")
    npm_s    = safe(inc, "Profit Margin")
    eps_s    = safe(inc, "Diluted EPS", "Earnings Per Share")
    ebitda_s = safe(inc, "EBITDA")
    price_s  = safe(inc, "Stock Price")
    shares_s = safe(inc, "Diluted Shares Outstanding", "Average Shares Outstanding")
    fcf_s    = safe(cf,  "Free Cash Flow")       if not cf.empty else pd.Series(dtype=float)
    cfo_s    = safe(cf,  "Cash from Operations") if not cf.empty else pd.Series(dtype=float)
    nd_s     = safe(bs,  "Net Debt")             if not bs.empty else pd.Series(dtype=float)

    rev_list = rev_s.tolist()
    rev_growth = [None] + [
        (rev_list[i] - rev_list[i-1]) / abs(rev_list[i-1]) * 100
        if rev_list[i] and rev_list[i-1] and rev_list[i-1] != 0 and not pd.isna(rev_list[i]) and not pd.isna(rev_list[i-1])
        else None
        for i in range(1, len(rev_list))
    ]

    rev_l = latest(rev_s); rev_p = prev(rev_s)
    fcf_l = latest(fcf_s); fcf_p = prev(fcf_s)
    eps_l = latest(eps_s); eps_p = prev(eps_s)

    # ── KPI Cards ──────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">📌 Key Metrics (Latest Year)</div>', unsafe_allow_html=True)
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    kpi(k1, "Revenue",        fmt_large(rev_l),                         yoy(rev_l, rev_p))
    kpi(k2, "Free Cash Flow", fmt_large(fcf_l),                         yoy(fcf_l, fcf_p))
    kpi(k3, "Gross Margin",   fmt_pct(latest(gm_s)))
    kpi(k4, "Op Margin",      fmt_pct(latest(opm_s)))
    kpi(k5, "Net Margin",     fmt_pct(latest(npm_s)))
    kpi(k6, "Diluted EPS",    f"${eps_l:.2f}" if eps_l else "—",        yoy(eps_l, eps_p))

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Revenue & Growth", "💰 Margins", "💵 Cash Flow", "📊 Valuation"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(bar_chart(years, [v/1e9 if v and not pd.isna(v) else None for v in rev_s],
                                      "Annual Revenue ($B)", "#4a9eff"), use_container_width=True)
        with c2:
            st.plotly_chart(bar_chart(years, rev_growth,
                                      "Revenue Growth (%)", "#22c55e"), use_container_width=True)
        c3, c4 = st.columns(2)
        with c3:
            st.plotly_chart(bar_chart(years, [v/1e9 if v and not pd.isna(v) else None for v in ni_s],
                                      "Net Income ($B)", "#f0a500"), use_container_width=True)
        with c4:
            st.plotly_chart(bar_chart(years, eps_s.tolist(),
                                      "Diluted EPS ($)", "#e879f9"), use_container_width=True)

    with tab2:
        gm_pct  = to_pct_list(gm_s)
        opm_pct = to_pct_list(opm_s)
        npm_pct = to_pct_list(npm_s)

        st.plotly_chart(line_chart(years, [gm_pct, opm_pct, npm_pct],
                                   ["Gross Margin", "Operating Margin", "Net Margin"],
                                   "Profit Margins Over Time (%)", height=350),
                        use_container_width=True)
        st.markdown("**Historical Margin Table**")
        st.dataframe(pd.DataFrame({
            "Year":             years,
            "Gross Margin":     [f"{v:.1f}%" if v else "—" for v in gm_pct],
            "Operating Margin": [f"{v:.1f}%" if v else "—" for v in opm_pct],
            "Net Margin":       [f"{v:.1f}%" if v else "—" for v in npm_pct],
        }).set_index("Year").T, use_container_width=True)

    with tab3:
        c1, c2 = st.columns(2)
        with c1:
            if fcf_s.notna().any():
                st.plotly_chart(bar_chart(cf_years, [v/1e9 if v and not pd.isna(v) else None for v in fcf_s],
                                          "Free Cash Flow ($B)", "#22c55e"), use_container_width=True)
            else:
                st.info("Free Cash Flow data not available")
        with c2:
            if cfo_s.notna().any():
                st.plotly_chart(bar_chart(cf_years, [v/1e9 if v and not pd.isna(v) else None for v in cfo_s],
                                          "Operating Cash Flow ($B)", "#4a9eff"), use_container_width=True)

        if fcf_s.notna().any() and ni_s.notna().any():
            min_len = min(len(fcf_s), len(ni_s))
            st.plotly_chart(line_chart(
                years[-min_len:],
                [[v/1e9 if v and not pd.isna(v) else None for v in fcf_s.tolist()[-min_len:]],
                 [v/1e9 if v and not pd.isna(v) else None for v in ni_s.tolist()[-min_len:]]],
                ["Free Cash Flow", "Net Income"],
                "FCF vs Net Income ($B)"
            ), use_container_width=True)

    with tab4:
        # Stock price
        if price_s.notna().any():
            st.markdown("#### 📈 Year-End Stock Price")
            fig_p = go.Figure(go.Scatter(
                x=years, y=price_s.tolist(), mode="lines+markers",
                line=dict(color="#4a9eff", width=2),
                fill="tozeroy", fillcolor="rgba(74,158,255,0.08)",
                hovertemplate="%{x}<br>Price: $%{y:.2f}<extra></extra>",
            ))
            fig_p.update_layout(**BASE_LAYOUT, height=320,
                                title=dict(text="Year-End Stock Price ($)",
                                           font=dict(color="#e2e8f0", size=14)))
            st.plotly_chart(fig_p, use_container_width=True)
        else:
            st.markdown("#### 📈 Stock Price History (live from roic.ai)")
            with st.spinner("Loading price history..."):
                prices = fetch_prices(ticker)
            if not prices.empty:
                close_col = next((c for c in ["adj_close", "close", "adjusted_close"]
                                  if c in prices.columns), prices.columns[1])
                fig_p = go.Figure(go.Scatter(
                    x=prices["date"], y=prices[close_col], mode="lines",
                    line=dict(color="#4a9eff", width=2),
                    fill="tozeroy", fillcolor="rgba(74,158,255,0.08)",
                ))
                fig_p.update_layout(**BASE_LAYOUT, height=320)
                st.plotly_chart(fig_p, use_container_width=True)
            else:
                st.info("Price data not available")

        # Valuation multiples — calculated from sheet data
        st.markdown("#### 📊 Valuation Multiples")
        pe_list, pfcf_list, evebit_list = [], [], []

        for i in range(len(years)):
            def get(s): return float(s.iloc[i]) if i < len(s) and not pd.isna(s.iloc[i]) else None
            price  = get(price_s)
            eps    = get(eps_s)
            fcf    = get(fcf_s)
            ebit   = get(oi_s)
            nd     = get(nd_s)
            sh     = get(shares_s)

            # P/E
            try:    pe_list.append(price / eps if price and eps and eps != 0 else None)
            except: pe_list.append(None)

            # P/FCF
            try:
                mktcap = price * sh if price and sh else None
                pfcf_list.append(mktcap / fcf if mktcap and fcf and fcf > 0 else None)
            except: pfcf_list.append(None)

            # EV/EBIT
            try:
                mktcap = price * sh if price and sh else None
                ev = (mktcap + nd) if mktcap and nd else mktcap
                evebit_list.append(ev / ebit if ev and ebit and ebit > 0 else None)
            except: evebit_list.append(None)

        val_ys, val_names = [], []
        if any(v for v in pe_list     if v): val_ys.append(pe_list);     val_names.append("P/E Ratio")
        if any(v for v in pfcf_list   if v): val_ys.append(pfcf_list);   val_names.append("Price / FCF")
        if any(v for v in evebit_list if v): val_ys.append(evebit_list); val_names.append("EV / EBIT")

        if val_ys:
            st.plotly_chart(line_chart(years, val_ys, val_names,
                                       "Valuation Multiples Over Time"), use_container_width=True)
            val_df = pd.DataFrame({"Year": years})
            if any(v for v in pe_list     if v): val_df["P/E"]     = [f"{v:.1f}x" if v else "—" for v in pe_list]
            if any(v for v in pfcf_list   if v): val_df["P/FCF"]   = [f"{v:.1f}x" if v else "—" for v in pfcf_list]
            if any(v for v in evebit_list if v): val_df["EV/EBIT"] = [f"{v:.1f}x" if v else "—" for v in evebit_list]
            st.dataframe(val_df.set_index("Year").T, use_container_width=True)
        else:
            st.info("⚠️ Valuation multiples require a **Stock Price** column in your Google Sheet. "
                    "Make sure it's populated for this company.")

    # Raw data
    with st.expander("🗂️ Raw Data"):
        t1, t2, t3 = st.tabs(["Income Statement", "Balance Sheet", "Cash Flow"])
        with t1: st.dataframe(inc, use_container_width=True)
        with t2: st.dataframe(bs,  use_container_width=True) if not bs.empty else st.info("No data")
        with t3: st.dataframe(cf,  use_container_width=True) if not cf.empty else st.info("No data")

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests

# ── Config ────────────────────────────────────────────────────────────────────
SHEET_ID     = "1zxw8jiuaeNDJelyUNrJ4H91NqOluwvJ7dl5p6MPKWRI"
API_KEY      = "73d3049608e044f1a63182f51656c760"
BASE_URL     = "https://api.roic.ai/v2"

def sheet_url(gid):
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"

SHEET_INCOME = sheet_url(0)
SHEET_BS     = sheet_url(1653631279)
SHEET_CF     = sheet_url(1757000096)

STOCKS = {
    "Ryanair":                "RYAAY",
    "Copart":                 "CPRT",
    "Constellation Software": "CSU.TO",
    "Fair Isaac":             "FICO",
    "S&P Global":             "SPGI",
    "Moody's":                "MCO",
    "ASML":                   "ASML",
}

# ── Design tokens ─────────────────────────────────────────────────────────────
C_BG        = "#FFFFFF"
C_SURFACE   = "#FAFAFA"
C_BORDER    = "#E8E8E8"
C_BORDER2   = "#F0F0F0"
C_TEXT      = "#111111"
C_TEXT2     = "#555555"
C_TEXT3     = "#999999"
C_ACCENT    = "#111111"   # single accent — charcoal
C_UP        = "#1A7F4B"   # muted green — not neon
C_DOWN      = "#C0392B"   # muted red
C_SIDEBAR   = "#F7F7F7"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Compounder",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

*, *::before, *::after {{ box-sizing: border-box; }}

html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    -webkit-font-smoothing: antialiased;
    background-color: {C_BG};
    color: {C_TEXT};
}}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header {{ display: none !important; }}
.stDeployButton {{ display: none !important; }}
[data-testid="stToolbar"] {{ display: none !important; }}

/* ── Main container ── */
.block-container {{
    padding: 2.5rem 3rem 4rem 3rem !important;
    max-width: 1400px !important;
}}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {{
    background-color: {C_SIDEBAR} !important;
    border-right: 1px solid {C_BORDER} !important;
}}
section[data-testid="stSidebar"] .block-container {{
    padding: 2rem 1.5rem !important;
}}
[data-testid="stSidebarNav"] {{ display: none; }}

/* ── Sidebar radio ── */
.stRadio > label {{ display: none; }}
.stRadio [data-testid="stMarkdownContainer"] p {{
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    color: {C_TEXT2} !important;
    letter-spacing: 0.01em;
}}

/* ── Sidebar selectbox ── */
.stSelectbox > label {{
    font-size: 0.72rem !important;
    font-weight: 500 !important;
    color: {C_TEXT3} !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {{
    gap: 0;
    border-bottom: 1px solid {C_BORDER} !important;
    background: transparent !important;
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent !important;
    border: none !important;
    padding: 0.6rem 1.2rem !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    color: {C_TEXT3} !important;
    border-bottom: 2px solid transparent !important;
    margin-bottom: -1px;
}}
.stTabs [aria-selected="true"] {{
    color: {C_TEXT} !important;
    border-bottom: 2px solid {C_TEXT} !important;
    font-weight: 600 !important;
}}
.stTabs [data-baseweb="tab-panel"] {{
    padding-top: 1.5rem !important;
}}

/* ── Expander ── */
.streamlit-expanderHeader {{
    font-size: 0.8rem !important;
    color: {C_TEXT3} !important;
    font-weight: 500 !important;
    background: transparent !important;
    border: none !important;
    padding-left: 0 !important;
}}
.streamlit-expanderContent {{
    border: 1px solid {C_BORDER} !important;
    border-radius: 4px !important;
}}

/* ── Buttons ── */
.stButton > button {{
    background: transparent !important;
    border: 1px solid {C_BORDER} !important;
    color: {C_TEXT2} !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    padding: 0.4rem 1rem !important;
    border-radius: 4px !important;
    transition: border-color 0.15s, color 0.15s;
}}
.stButton > button:hover {{
    border-color: {C_TEXT} !important;
    color: {C_TEXT} !important;
}}

/* ── Divider ── */
hr {{
    border: none !important;
    border-top: 1px solid {C_BORDER} !important;
    margin: 1.5rem 0 !important;
}}

/* ── Spinner ── */
.stSpinner > div {{ border-top-color: {C_TEXT} !important; }}

/* ── Metric card ── */
.metric-block {{
    padding: 1.25rem 0;
    border-bottom: 1px solid {C_BORDER2};
}}
.metric-label {{
    font-size: 0.7rem;
    font-weight: 500;
    color: {C_TEXT3};
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.4rem;
}}
.metric-value {{
    font-size: 1.6rem;
    font-weight: 600;
    color: {C_TEXT};
    letter-spacing: -0.02em;
    line-height: 1;
}}
.metric-delta {{
    font-size: 0.72rem;
    font-weight: 500;
    margin-top: 0.3rem;
    letter-spacing: 0.01em;
}}
.delta-up   {{ color: {C_UP}; }}
.delta-down {{ color: {C_DOWN}; }}
.delta-nil  {{ color: {C_TEXT3}; }}

/* ── Page title ── */
.page-title {{
    font-size: 1.1rem;
    font-weight: 600;
    color: {C_TEXT};
    letter-spacing: -0.01em;
    margin-bottom: 0.15rem;
}}
.page-sub {{
    font-size: 0.78rem;
    color: {C_TEXT3};
    font-weight: 400;
    margin-bottom: 2rem;
}}

/* ── Section label ── */
.section-label {{
    font-size: 0.7rem;
    font-weight: 500;
    color: {C_TEXT3};
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.75rem;
    display: block;
}}

/* ── Summary table ── */
.tbl-row {{
    display: grid;
    grid-template-columns: 1.6fr 0.6fr 0.9fr 0.9fr 0.75fr 0.9fr 0.75fr 0.9fr 0.75fr 0.75fr 0.75fr;
    padding: 0.6rem 0;
    border-bottom: 1px solid {C_BORDER2};
    align-items: center;
}}
.tbl-header-row {{
    border-bottom: 1px solid {C_BORDER} !important;
    padding-bottom: 0.5rem !important;
    margin-bottom: 0.1rem;
}}
.tbl-header {{
    font-size: 0.67rem;
    font-weight: 500;
    color: {C_TEXT3};
    text-transform: uppercase;
    letter-spacing: 0.07em;
}}
.tbl-cell {{
    font-size: 0.8rem;
    color: {C_TEXT};
    font-variant-numeric: tabular-nums;
}}
.tbl-name {{ font-weight: 500; font-size: 0.82rem; }}
.tbl-ticker {{ color: {C_TEXT3}; font-size: 0.72rem; }}

/* ── Sidebar company list ── */
.nav-company {{
    font-size: 0.82rem;
    font-weight: 400;
    color: {C_TEXT2};
    padding: 0.45rem 0.6rem;
    border-radius: 4px;
    cursor: pointer;
    transition: background 0.1s;
}}
.nav-company:hover {{ background: {C_BORDER}; }}
.nav-company-active {{
    font-weight: 600;
    color: {C_TEXT};
    background: {C_BORDER};
    padding: 0.45rem 0.6rem;
    border-radius: 4px;
    font-size: 0.82rem;
}}
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
        st.error(f"Could not load data: {e}")
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
    url    = f"{BASE_URL}/stock-prices/{ticker}"
    params = {"limit": 100000, "order": "asc", "format": "json", "apikey": API_KEY}
    try:
        r    = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        df   = pd.DataFrame(data if isinstance(data, list) else data.get("data", []))
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
        return df
    except:
        return pd.DataFrame()


# ── Number helpers ────────────────────────────────────────────────────────────
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

def fmt_currency(val):
    """Render dollar amounts with clean rounding — no false precision."""
    try:
        v = float(val)
        if pd.isna(v): return "—"
        neg = v < 0
        v = abs(v)
        if v >= 1e12:   s = f"${v/1e12:.1f}T"
        elif v >= 1e9:  s = f"${v/1e9:.1f}B"
        elif v >= 1e6:  s = f"${v/1e6:.0f}M"
        else:           s = f"${v:,.0f}"
        return f"({s})" if neg else s
    except:
        return "—"

def fmt_pct(val, decimals=1):
    try:
        v = float(val)
        if pd.isna(v): return "—"
        if abs(v) <= 1: v *= 100
        return f"{v:.{decimals}f}%"
    except:
        return "—"

def fmt_multiple(val):
    try:
        v = float(val)
        if pd.isna(v): return "—"
        return f"{v:.0f}x"
    except:
        return "—"

def fmt_eps(val):
    try:
        v = float(val)
        if pd.isna(v): return "—"
        return f"${v:.2f}"
    except:
        return "—"

def to_pct_list(s):
    out = []
    for v in s:
        try:
            v = float(v)
            out.append(v * 100 if abs(v) <= 1 else v)
        except:
            out.append(None)
    return out

def delta_html(val):
    if val is None: return ""
    sign = "+" if val >= 0 else ""
    cls  = "delta-up" if val >= 0 else "delta-down"
    return f'<span class="metric-delta {cls}">{sign}{val:.1f}%</span>'


# Chart theme
CHART_BASE = dict(
    paper_bgcolor=C_BG,
    plot_bgcolor=C_BG,
    font=dict(family="Inter, -apple-system, sans-serif", color=C_TEXT3, size=11),
    xaxis=dict(
        showgrid=False,
        zeroline=False,
        showline=False,
        tickfont=dict(size=10, color=C_TEXT3),
        tickcolor=C_BORDER,
    ),
    margin=dict(l=0, r=0, t=28, b=0),
    hovermode="x unified",
    hoverlabel=dict(
        bgcolor=C_BG,
        bordercolor=C_BORDER,
        font=dict(family="Inter, sans-serif", size=11, color=C_TEXT),
    ),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        borderwidth=0,
        font=dict(size=10, color=C_TEXT2),
        orientation="h",
        yanchor="bottom", y=1.02,
        xanchor="left",   x=0,
    ),
)

# Two-tone palette — restrained, works on white
LINE_COLORS = ["#111111", "#AAAAAA", "#555555", "#CCCCCC"]

def make_bar(x, y, title, height=280, color=C_ACCENT):
    y_safe  = [v if v is not None and not pd.isna(v) else 0 for v in y]
    c_list  = [C_DOWN if v < 0 else color for v in y_safe]
    fig = go.Figure(go.Bar(
        x=x, y=y_safe,
        marker_color=c_list,
        marker_line_width=0,
        hovertemplate="%{x}<br>%{y:,.1f}<extra></extra>",
    ))
    fig.update_layout(**CHART_BASE)
    fig.update_layout(
        height=height,
        title=dict(text=title, font=dict(size=11, color=C_TEXT2, weight=500), x=0, xanchor="left"),
        bargap=0.35,
        yaxis=dict(showgrid=True, gridcolor=C_BORDER2, gridwidth=1,
                   zeroline=False, showline=False,
                   tickfont=dict(size=10, color=C_TEXT3), tickcolor="rgba(0,0,0,0)"),
    )
    return fig

def make_line(x, ys, names, title, height=300, suffix=""):
    fig = go.Figure()
    for i, (y, name) in enumerate(zip(ys, names)):
        y_clean = [v if v and not pd.isna(v) else None for v in y]
        fig.add_trace(go.Scatter(
            x=x, y=y_clean,
            name=name,
            mode="lines",
            line=dict(color=LINE_COLORS[i % len(LINE_COLORS)], width=1.5),
            hovertemplate=f"%{{x}}<br>{name}: %{{y:,.1f}}{suffix}<extra></extra>",
            connectgaps=False,
        ))
    fig.update_layout(**CHART_BASE)
    fig.update_layout(
        height=height,
        title=dict(text=title, font=dict(size=11, color=C_TEXT2, weight=500), x=0, xanchor="left"),
        yaxis=dict(showgrid=True, gridcolor=C_BORDER2, gridwidth=1,
                   zeroline=False, showline=False,
                   tickfont=dict(size=10, color=C_TEXT3), tickcolor="rgba(0,0,0,0)"),
    )
    return fig



# ── KPI block ─────────────────────────────────────────────────────────────────
def kpi_block(col, label, value_str, delta=None):
    col.markdown(f"""
    <div class="metric-block">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value_str}</div>
        {delta_html(delta)}
    </div>""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-size:1rem;font-weight:600;color:#111;margin-bottom:0.2rem;letter-spacing:-0.01em">Compounder</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.72rem;color:#999;margin-bottom:2rem">Quality Growth Tracker</div>', unsafe_allow_html=True)

    page = st.radio("", ["Overview", "Company"], label_visibility="collapsed")

    if page == "Company":
        st.markdown('<div style="font-size:0.68rem;color:#999;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.5rem">Company</div>', unsafe_allow_html=True)
        selected = st.selectbox("", list(STOCKS.keys()), label_visibility="collapsed")

    st.markdown("<br>" * 6, unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.68rem;color:#ccc">Updated every 30 min</div>', unsafe_allow_html=True)
    if st.button("Refresh"):
        st.cache_data.clear()
        st.rerun()


# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner(""):
    inc_all = load_sheet(SHEET_INCOME)
    bs_all  = load_sheet(SHEET_BS)
    cf_all  = load_sheet(SHEET_CF)


# ══════════════════════════════════════════════════════════════════════════════
# OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == "Overview":

    st.markdown('<div class="page-title">Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Seven quality compounders — latest annual figures</div>', unsafe_allow_html=True)

    def calc_cagr(s):
        vals = [v for v in s.dropna().tolist() if v is not None and v > 0]
        if len(vals) < 2:
            return None, 0
        start, end = vals[0], vals[-1]
        n = len(vals) - 1
        if start <= 0 or n == 0:
            return None, 0
        return ((end / start) ** (1.0 / n) - 1) * 100, n

    def fmt_cagr(val, n):
        if val is None: return "—"
        sign = "+" if val >= 0 else ""
        return f"{sign}{val:.1f}%"

    rows = []
    for company, ticker in STOCKS.items():
        inc = get_ticker_data(inc_all, ticker)
        if inc.empty:
            rows.append({"Company": company, "Ticker": ticker})
            continue

        rev_s = safe(inc, "Sales Revenue", "Sales and Services Revenues", "Revenue")
        gp_s  = safe(inc, "Gross Profit")
        oi_s  = safe(inc, "Operating Income", "EBIT")
        ni_s  = safe(inc, "Net Income", "Net Income Including Minority Interest")
        gm_s  = safe(inc, "Gross Margin")
        opm_s = safe(inc, "Operating Margin")
        npm_s = safe(inc, "Profit Margin")

        rev_cagr, rev_n = calc_cagr(rev_s)
        oi_cagr,  oi_n  = calc_cagr(oi_s)

        rows.append({
            "Company":      company,
            "Ticker":       ticker,
            "Revenue":      fmt_currency(latest(rev_s)),
            "Gross Profit": fmt_currency(latest(gp_s)),
            "GP Margin":    fmt_pct(latest(gm_s)),
            "Op Profit":    fmt_currency(latest(oi_s)),
            "Op Margin":    fmt_pct(latest(opm_s)),
            "Net Profit":   fmt_currency(latest(ni_s)),
            "Net Margin":   fmt_pct(latest(npm_s)),
            "Rev CAGR":     fmt_cagr(rev_cagr, rev_n),
            "Op CAGR":      fmt_cagr(oi_cagr,  oi_n),
        })

    # Render HTML table
    header_cols = ["Company", "Ticker", "Revenue", "Gross Profit", "GP Margin",
                   "Op Profit", "Op Margin", "Net Profit", "Net Margin", "Rev CAGR", "Op CAGR"]

    header_html = "".join(f'<span class="tbl-header">{h}</span>' for h in header_cols)
    st.markdown(f'''<div class="tbl-row tbl-header-row">{header_html}</div>''',
                unsafe_allow_html=True)

    for r in rows:
        def cell(key, cls="tbl-cell"):
            return f'<span class="{cls}">{r.get(key, "—")}</span>'

        rev_cagr_val = r.get("Rev CAGR", "—")
        oi_cagr_val  = r.get("Op CAGR",  "—")

        def cagr_span(val):
            if val == "—": return '<span class="tbl-cell" style="color:#ccc">—</span>'
            is_pos = not val.startswith("-")
            color  = C_UP if is_pos else C_DOWN
            return f'<span class="tbl-cell" style="color:{color};font-weight:500">{val}</span>'

        st.markdown(f'''
        <div class="tbl-row">
            <span class="tbl-cell tbl-name">{r.get("Company","")}</span>
            <span class="tbl-ticker">{r.get("Ticker","")}</span>
            {cell("Revenue")}
            {cell("Gross Profit")}
            {cell("GP Margin")}
            {cell("Op Profit")}
            {cell("Op Margin")}
            {cell("Net Profit")}
            {cell("Net Margin")}
            {cagr_span(rev_cagr_val)}
            {cagr_span(oi_cagr_val)}
        </div>''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Rebuild raw numeric data for charts from the sheet directly
    chart_rev, chart_gp, chart_oi, chart_ni, chart_opm, chart_npm, chart_names = [], [], [], [], [], [], []
    for company, ticker in STOCKS.items():
        inc = get_ticker_data(inc_all, ticker)
        if inc.empty:
            continue
        rev_v = latest(safe(inc, "Sales Revenue", "Sales and Services Revenues", "Revenue"))
        oi_v  = latest(safe(inc, "Operating Income", "EBIT"))
        ni_v  = latest(safe(inc, "Net Income", "Net Income Including Minority Interest"))
        opm_v = latest(safe(inc, "Operating Margin"))
        npm_v = latest(safe(inc, "Profit Margin"))
        if rev_v:
            chart_names.append(company)
            chart_rev.append(rev_v)
            chart_oi.append(oi_v)
            chart_ni.append(ni_v)
            chart_opm.append(to_pct_list([opm_v])[0] if opm_v else 0)
            chart_npm.append(to_pct_list([npm_v])[0] if npm_v else 0)

    # Revenue chart
    st.markdown('<span class="section-label">Revenue</span>', unsafe_allow_html=True)
    if chart_names:
        fig_rev = go.Figure(go.Bar(
            x=chart_names,
            y=[v/1e9 for v in chart_rev],
            marker_color=C_ACCENT,
            marker_line_width=0,
            hovertemplate="%{x}<br>$%{y:.1f}B<extra></extra>",
        ))
        fig_rev.update_layout(**CHART_BASE)
        fig_rev.update_layout(
            height=260, bargap=0.45, showlegend=False,
            yaxis=dict(showgrid=True, gridcolor=C_BORDER2, ticksuffix="B",
                       tickprefix="$", tickfont=dict(size=10, color=C_TEXT3),
                       zeroline=False, showline=False),
        )
        st.plotly_chart(fig_rev, use_container_width=True, config={"displayModeBar": False})

    # Margin comparison
    st.markdown('<span class="section-label">Margins</span>', unsafe_allow_html=True)
    if chart_names:
        fig_m = go.Figure()
        fig_m.add_trace(go.Bar(name="Operating", x=chart_names, y=chart_opm,
                               marker_color=C_ACCENT, marker_line_width=0,
                               hovertemplate="%{x}<br>Operating: %{y:.1f}%<extra></extra>"))
        fig_m.add_trace(go.Bar(name="Net", x=chart_names, y=chart_npm,
                               marker_color="#BBBBBB", marker_line_width=0,
                               hovertemplate="%{x}<br>Net: %{y:.1f}%<extra></extra>"))
        fig_m.update_layout(**CHART_BASE)
        fig_m.update_layout(
            height=260, barmode="group", bargap=0.35, bargroupgap=0.08,
            yaxis=dict(showgrid=True, gridcolor=C_BORDER2, ticksuffix="%",
                       tickfont=dict(size=10, color=C_TEXT3),
                       zeroline=False, showline=False),
        )
        st.plotly_chart(fig_m, use_container_width=True, config={"displayModeBar": False})


# ══════════════════════════════════════════════════════════════════════════════
# COMPANY DEEP DIVE
# ══════════════════════════════════════════════════════════════════════════════
else:
    ticker = STOCKS[selected]
    inc    = get_ticker_data(inc_all, ticker)
    bs     = get_ticker_data(bs_all,  ticker)
    cf     = get_ticker_data(cf_all,  ticker)

    if inc.empty:
        st.error(f"No data found for {ticker}. Check that the ticker matches exactly in your Google Sheet.")
        st.stop()

    years    = inc["Date"].dt.year.astype(str).tolist() if "Date" in inc.columns else [str(i) for i in range(len(inc))]
    cf_years = cf["Date"].dt.year.astype(str).tolist()  if not cf.empty and "Date" in cf.columns else years

    # Series
    rev_s    = safe(inc, "Sales Revenue", "Revenue")
    ni_s     = safe(inc, "Net Income")
    oi_s     = safe(inc, "Operating Income")
    gm_s     = safe(inc, "Gross Margin")
    opm_s    = safe(inc, "Operating Margin")
    npm_s    = safe(inc, "Profit Margin")
    eps_s    = safe(inc, "Diluted EPS", "Earnings Per Share")
    price_s  = safe(inc, "Stock Price")
    shares_s = safe(inc, "Diluted Shares Outstanding", "Average Shares Outstanding")
    fcf_s    = safe(cf,  "Free Cash Flow")       if not cf.empty else pd.Series(dtype=float)
    cfo_s    = safe(cf,  "Cash from Operations") if not cf.empty else pd.Series(dtype=float)
    nd_s     = safe(bs,  "Net Debt")             if not bs.empty else pd.Series(dtype=float)

    rev_list   = rev_s.tolist()
    rev_growth = [None] + [
        (rev_list[i] - rev_list[i-1]) / abs(rev_list[i-1]) * 100
        if (rev_list[i] and rev_list[i-1] and rev_list[i-1] != 0
            and not pd.isna(rev_list[i]) and not pd.isna(rev_list[i-1]))
        else None
        for i in range(1, len(rev_list))
    ]

    rev_l = latest(rev_s); rev_p = prev(rev_s)
    fcf_l = latest(fcf_s); fcf_p = prev(fcf_s)
    eps_l = latest(eps_s); eps_p = prev(eps_s)
    opm_l = latest(opm_s)
    npm_l = latest(npm_s)
    gm_l  = latest(gm_s)

    # Header — clean, typographic only
    st.markdown(f'<div class="page-title">{selected}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-sub">{ticker}</div>', unsafe_allow_html=True)

    # ── KPI row ────────────────────────────────────────────────────────────────
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    kpi_block(k1, "Revenue",       fmt_currency(rev_l),  yoy(rev_l, rev_p))
    kpi_block(k2, "Free Cash Flow",fmt_currency(fcf_l),  yoy(fcf_l, fcf_p))
    kpi_block(k3, "Gross Margin",  fmt_pct(gm_l))
    kpi_block(k4, "Operating Margin", fmt_pct(opm_l))
    kpi_block(k5, "Net Margin",    fmt_pct(npm_l))
    kpi_block(k6, "EPS",           fmt_eps(eps_l),       yoy(eps_l, eps_p))

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabs — no emojis ──────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs(["Revenue", "Margins", "Cash Flow", "Valuation"])

    # TAB 1 — Revenue
    with tab1:
        c1, c2 = st.columns(2, gap="large")
        with c1:
            vals_b = [v/1e9 if v and not pd.isna(v) else None for v in rev_s]
            st.plotly_chart(make_bar(years, vals_b, "Revenue  ($B)", height=260),
                            use_container_width=True, config={"displayModeBar": False})
        with c2:
            st.plotly_chart(make_bar(years, rev_growth, "Revenue Growth  (%)", height=260, color="#555555"),
                            use_container_width=True, config={"displayModeBar": False})

        st.markdown("<br>", unsafe_allow_html=True)
        c3, c4 = st.columns(2, gap="large")
        with c3:
            ni_b = [v/1e9 if v and not pd.isna(v) else None for v in ni_s]
            st.plotly_chart(make_bar(years, ni_b, "Net Income  ($B)", height=260),
                            use_container_width=True, config={"displayModeBar": False})
        with c4:
            st.plotly_chart(make_bar(years, eps_s.tolist(), "EPS  ($)", height=260, color="#555555"),
                            use_container_width=True, config={"displayModeBar": False})

    # TAB 2 — Margins
    with tab2:
        gm_pct  = to_pct_list(gm_s)
        opm_pct = to_pct_list(opm_s)
        npm_pct = to_pct_list(npm_s)

        fig_mg = make_line(
            years,
            [gm_pct, opm_pct, npm_pct],
            ["Gross", "Operating", "Net"],
            "Profit Margins  (%)",
            height=340,
            suffix="%",
        )
        fig_mg.update_layout(yaxis=dict(ticksuffix="%", showgrid=True,
                                        gridcolor=C_BORDER2, tickfont=dict(size=10, color=C_TEXT3),
                                        zeroline=False, showline=False))
        st.plotly_chart(fig_mg, use_container_width=True, config={"displayModeBar": False})

        # Clean table — no extra borders or color
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<span class="section-label">Historical</span>', unsafe_allow_html=True)
        margin_df = pd.DataFrame({
            "Year":      years,
            "Gross":     [f"{v:.1f}%" if v else "—" for v in gm_pct],
            "Operating": [f"{v:.1f}%" if v else "—" for v in opm_pct],
            "Net":       [f"{v:.1f}%" if v else "—" for v in npm_pct],
        }).set_index("Year").T
        st.dataframe(margin_df, use_container_width=True,
                     column_config={c: st.column_config.TextColumn(c, width="small") for c in margin_df.columns})

    # TAB 3 — Cash Flow
    with tab3:
        c1, c2 = st.columns(2, gap="large")
        with c1:
            if fcf_s.notna().any():
                fcf_b = [v/1e9 if v and not pd.isna(v) else None for v in fcf_s]
                st.plotly_chart(make_bar(cf_years, fcf_b, "Free Cash Flow  ($B)", height=260),
                                use_container_width=True, config={"displayModeBar": False})
            else:
                st.markdown('<span style="color:#999;font-size:0.82rem">No free cash flow data</span>', unsafe_allow_html=True)
        with c2:
            if cfo_s.notna().any():
                cfo_b = [v/1e9 if v and not pd.isna(v) else None for v in cfo_s]
                st.plotly_chart(make_bar(cf_years, cfo_b, "Operating Cash Flow  ($B)", height=260, color="#555555"),
                                use_container_width=True, config={"displayModeBar": False})

        if fcf_s.notna().any() and ni_s.notna().any():
            st.markdown("<br>", unsafe_allow_html=True)
            min_len = min(len(fcf_s), len(ni_s))
            fig_cmp = make_line(
                years[-min_len:],
                [[v/1e9 if v and not pd.isna(v) else None for v in fcf_s.tolist()[-min_len:]],
                 [v/1e9 if v and not pd.isna(v) else None for v in ni_s.tolist()[-min_len:]]],
                ["Free Cash Flow", "Net Income"],
                "FCF vs Net Income  ($B)",
                height=300,
            )
            st.plotly_chart(fig_cmp, use_container_width=True, config={"displayModeBar": False})

    # TAB 4 — Valuation
    with tab4:
        # Stock price
        if price_s.notna().any():
            fig_px = make_line(
                years,
                [price_s.tolist()],
                ["Price"],
                "Stock Price  ($)",
                height=300,
            )
            fig_px.update_layout(yaxis=dict(tickprefix="$", showgrid=True,
                                             gridcolor=C_BORDER2, tickfont=dict(size=10, color=C_TEXT3),
                                             zeroline=False, showline=False))
            st.plotly_chart(fig_px, use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown('<span class="section-label">Stock Price  — live</span>', unsafe_allow_html=True)
            with st.spinner(""):
                prices = fetch_prices(ticker)
            if not prices.empty:
                close_col = next((c for c in ["adj_close", "close", "adjusted_close"]
                                  if c in prices.columns), prices.columns[1])
                fig_px = go.Figure(go.Scatter(
                    x=prices["date"], y=prices[close_col],
                    mode="lines", name="Price",
                    line=dict(color=C_ACCENT, width=1.5),
                    hovertemplate="%{x|%d %b %Y}<br>$%{y:.2f}<extra></extra>",
                ))
                fig_px.update_layout(**CHART_BASE)
                fig_px.update_layout(
                    height=300, showlegend=False,
                    yaxis=dict(tickprefix="$", showgrid=True, gridcolor=C_BORDER2,
                               tickfont=dict(size=10, color=C_TEXT3), zeroline=False, showline=False),
                )
                st.plotly_chart(fig_px, use_container_width=True, config={"displayModeBar": False})

        # Multiples
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<span class="section-label">Multiples</span>', unsafe_allow_html=True)

        pe_list, pfcf_list, evebit_list = [], [], []
        for i in range(len(years)):
            def _g(s):
                return float(s.iloc[i]) if i < len(s) and pd.notna(s.iloc[i]) else None
            price = _g(price_s); eps = _g(eps_s); fcf = _g(fcf_s)
            ebit  = _g(oi_s);    nd  = _g(nd_s);  sh  = _g(shares_s)

            try:    pe_list.append(price / eps if price and eps and eps != 0 else None)
            except: pe_list.append(None)

            try:
                mc = price * sh if price and sh else None
                pfcf_list.append(mc / fcf if mc and fcf and fcf > 0 else None)
            except: pfcf_list.append(None)

            try:
                mc = price * sh if price and sh else None
                ev = (mc + nd) if mc and nd else mc
                evebit_list.append(ev / ebit if ev and ebit and ebit > 0 else None)
            except: evebit_list.append(None)

        val_ys, val_names = [], []
        if any(v for v in pe_list     if v): val_ys.append(pe_list);     val_names.append("P/E")
        if any(v for v in pfcf_list   if v): val_ys.append(pfcf_list);   val_names.append("P/FCF")
        if any(v for v in evebit_list if v): val_ys.append(evebit_list); val_names.append("EV/EBIT")

        if val_ys:
            fig_v = make_line(years, val_ys, val_names, "Valuation Multiples", height=300, suffix="x")
            st.plotly_chart(fig_v, use_container_width=True, config={"displayModeBar": False})

            val_df = pd.DataFrame({"Year": years})
            if any(v for v in pe_list     if v): val_df["P/E"]    = [fmt_multiple(v) for v in pe_list]
            if any(v for v in pfcf_list   if v): val_df["P/FCF"]  = [fmt_multiple(v) for v in pfcf_list]
            if any(v for v in evebit_list if v): val_df["EV/EBIT"]= [fmt_multiple(v) for v in evebit_list]
            st.dataframe(val_df.set_index("Year").T, use_container_width=True,
                         column_config={c: st.column_config.TextColumn(c, width="small") for c in val_df.columns if c != "Year"})
        else:
            st.markdown('<span style="color:#999;font-size:0.82rem">Stock price required to calculate multiples. Add a Stock Price column to your Google Sheet.</span>', unsafe_allow_html=True)

    # Raw data — tucked away, quiet
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("Raw data"):
        t1, t2, t3 = st.tabs(["Income Statement", "Balance Sheet", "Cash Flow"])
        with t1:
            st.dataframe(inc, use_container_width=True)
        with t2:
            if not bs.empty:
                st.dataframe(bs, use_container_width=True)
            else:
                st.markdown('<span style="color:#999;font-size:0.82rem">No data</span>', unsafe_allow_html=True)
        with t3:
            if not cf.empty:
                st.dataframe(cf, use_container_width=True)
            else:
                st.markdown('<span style="color:#999;font-size:0.82rem">No data</span>', unsafe_allow_html=True)

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests

# ── Config ────────────────────────────────────────────────────────────────────
API_KEY  = "73d3049608e044f1a63182f51656c760"
BASE_URL = "https://api.roic.ai/v2"

STOCKS = {
    "Ryanair":                "RYAAY",
    "Copart":                 "CPRT",
    "Constellation Software": "CSU.TO",
    "Fair Isaac":             "FICO",
    "S&P Global":             "SPGI",
    "Moody's":               "MCO",
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
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_fundamental(endpoint, ticker):
    """Fetch income-statement, balance-sheet, or cash-flow from roic.ai."""
    url = f"{BASE_URL}/{endpoint}/{ticker}"
    params = {"period": "annual", "limit": 20, "order": "desc", "apikey": API_KEY}
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        raw = r.json()
        # API returns list of dicts or {"data": [...]}
        rows = raw if isinstance(raw, list) else raw.get("data", [])
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        # Normalise column names: lowercase with underscores → keep original
        # Parse date
        for col in ["date", "Date", "period_end", "fiscal_year_end"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
                df = df.rename(columns={col: "Date"})
                break
        # Coerce all non-string columns to numeric
        skip = {"Date", "ticker", "Ticker", "period", "Period",
                "period_label", "currency", "Currency"}
        for col in df.columns:
            if col not in skip:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.sort_values("Date").reset_index(drop=True)
        return df
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_prices(ticker):
    """Fetch full daily price history."""
    url = f"{BASE_URL}/stock-prices/{ticker}"
    params = {"limit": 100000, "order": "asc", "apikey": API_KEY}
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        raw = r.json()
        rows = raw if isinstance(raw, list) else raw.get("data", [])
        df = pd.DataFrame(rows)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_year_end_price(ticker, month):
    """
    Return a Series of year-end closing prices aligned to fiscal year end month.
    Picks the last available trading day in the target month for each year.
    """
    prices = fetch_prices(ticker)
    if prices.empty or "date" not in prices.columns:
        return pd.Series(dtype=float), []
    close_col = next((c for c in ["adj_close", "adjusted_close", "close"] if c in prices.columns), None)
    if not close_col:
        return pd.Series(dtype=float), []
    prices = prices.dropna(subset=["date", close_col])
    prices["year"]  = prices["date"].dt.year
    prices["month"] = prices["date"].dt.month
    # Keep only rows in the target month
    monthly = prices[prices["month"] == month]
    if monthly.empty:
        return pd.Series(dtype=float), []
    # Last trading day per year
    idx = monthly.groupby("year")["date"].idxmax()
    result = monthly.loc[idx].set_index("year")[close_col].sort_index()
    return result, result.index.astype(str).tolist()


# ── Number helpers ────────────────────────────────────────────────────────────
def safe(df, *cols):
    """Return first matching column as numeric Series."""
    for c in cols:
        if c in df.columns:
            return pd.to_numeric(df[c], errors="coerce").reset_index(drop=True)
    return pd.Series(dtype=float)

def align(s, n):
    """Ensure Series has exactly n elements, padding/truncating as needed."""
    s = s.reset_index(drop=True) if not s.empty else s
    if len(s) == n:
        return s
    if len(s) > n:
        return s.iloc[:n].reset_index(drop=True)
    # Pad with NaN
    pad = pd.Series([float("nan")] * (n - len(s)))
    return pd.concat([s, pad], ignore_index=True)

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
    margin=dict(l=0, r=0, t=48, b=0),
    hovermode="x unified",
    hoverlabel=dict(
        bgcolor=C_BG,
        bordercolor=C_BORDER,
        font=dict(family="Inter, sans-serif", size=11, color=C_TEXT),
    ),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        borderwidth=0,
        font=dict(size=10, color=C_TEXT3),
        orientation="h",
        yanchor="top",  y=1.0,
        xanchor="right", x=1.0,
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
        margin=dict(l=0, r=0, t=52, b=0),
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
    st.markdown('<div style="font-size:0.68rem;color:#ccc">Live from roic.ai</div>', unsafe_allow_html=True)
    if st.button("Refresh"):
        st.cache_data.clear()
        st.rerun()


# (Data is fetched per-ticker on demand via fetch_fundamental)


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
        with st.spinner(f"Loading {company}..."):
            inc = fetch_fundamental("fundamental/income-statement", ticker)
        if inc.empty:
            rows.append({"Company": company, "Ticker": ticker})
            continue

        # Try all known variants — API may return camelCase, snake_case, or Title Case
        rev_s = safe(inc, "is_sales_revenue_turnover", "is_sales_and_services_revenues")
        gp_s  = safe(inc, "is_gross_profit")
        oi_s  = safe(inc, "ebit", "is_oper_income")
        ni_s  = safe(inc, "is_net_income", "is_ni_including_minority_int_ratio")
        gm_s  = safe(inc, "gross_margin")
        opm_s = safe(inc, "oper_margin")
        npm_s = safe(inc, "profit_margin")

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
            # keep raw for charts
            "_rev": latest(rev_s),
            "_oi":  latest(oi_s),
            "_ni":  latest(ni_s),
            "_opm": latest(opm_s),
            "_npm": latest(npm_s),
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

    # Use raw values stored in rows
    chart_names = [r["Company"] for r in rows if r.get("_rev")]
    chart_rev   = [r["_rev"]  for r in rows if r.get("_rev")]
    chart_opm   = [to_pct_list([r.get("_opm")])[0] if r.get("_opm") is not None else 0 for r in rows if r.get("_rev")]
    chart_npm   = [to_pct_list([r.get("_npm")])[0] if r.get("_npm") is not None else 0 for r in rows if r.get("_rev")]

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
    ticker     = STOCKS[selected]
    fe_month   = {"RYAAY": 3, "CPRT": 7, "CSU.TO": 12, "FICO": 9,
                  "SPGI": 12, "MCO": 12, "ASML": 12}.get(ticker, 12)

    with st.spinner(""):
        inc = fetch_fundamental("fundamental/income-statement", ticker)
        bs  = fetch_fundamental("fundamental/balance-sheet",    ticker)
        cf  = fetch_fundamental("fundamental/cash-flow",        ticker)

    if inc.empty:
        st.error(f"No data returned for {ticker}. The API may be unavailable or the ticker may have changed.")
        st.stop()

    years    = inc["Date"].dt.year.astype(str).tolist() if "Date" in inc.columns else [str(i) for i in range(len(inc))]
    cf_years = cf["Date"].dt.year.astype(str).tolist()  if not cf.empty and "Date" in cf.columns else years
    n        = len(years)  # canonical length — all series must match this

    # Series — all aligned to n (income statement row count)
    rev_s    = align(safe(inc, "is_sales_revenue_turnover", "is_sales_and_services_revenues"), n)
    ni_s     = align(safe(inc, "is_net_income", "is_ni_including_minority_int_ratio"), n)
    oi_s     = align(safe(inc, "ebit", "is_oper_income"), n)
    gp_s     = align(safe(inc, "is_gross_profit"), n)
    gm_s     = align(safe(inc, "gross_margin"), n)
    opm_s    = align(safe(inc, "oper_margin"), n)
    npm_s    = align(safe(inc, "profit_margin"), n)
    eps_s    = align(safe(inc, "diluted_eps", "eps"), n)
    shares_s = align(safe(inc, "is_sh_for_diluted_eps", "is_avg_num_sh_for_eps"), n)
    cogs_s   = align(safe(inc, "is_cogs", "is_cog_and_services_sold"), n)

    # Year-end price — aligned to income statement years
    price_series, price_years = fetch_year_end_price(ticker, fe_month)
    price_s = pd.Series([
        float(price_series.loc[int(y)]) if not price_series.empty and int(y) in price_series.index else float("nan")
        for y in years
    ], dtype=float)

    # Cash flow series — align to cf length then to n
    n_cf  = len(cf) if not cf.empty else 0
    fcf_s = align(safe(cf, "cf_free_cash_flow") if n_cf else pd.Series(dtype=float), n)
    cfo_s = align(safe(cf, "cf_cash_from_oper") if n_cf else pd.Series(dtype=float), n)

    # Balance sheet series — use bs_years for working capital, align to n for valuation
    bs_years = bs["Date"].dt.year.astype(str).tolist() if not bs.empty and "Date" in bs.columns else years
    n_bs  = len(bs) if not bs.empty else 0
    nd_s  = align(safe(bs, "net_debt") if n_bs else pd.Series(dtype=float), n)
    ar_s  = safe(bs, "bs_accts_notes_rec", "bs_accts_rec", "accounts_receivable") if n_bs else pd.Series(dtype=float)
    inv_s = safe(bs, "bs_inventories", "inventories") if n_bs else pd.Series(dtype=float)
    ap_s  = safe(bs, "bs_accts_payable", "bs_accts_pay_accruals", "accounts_payable") if n_bs else pd.Series(dtype=float)
    ca_s  = safe(bs, "bs_tot_cur_assets", "total_current_assets") if n_bs else pd.Series(dtype=float)
    cl_s  = safe(bs, "bs_tot_cur_liabilities", "total_current_liabilities") if n_bs else pd.Series(dtype=float)

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
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Revenue", "Margins", "Cash Flow", "Valuation", "Working Capital"])

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
            "Metric":    ["Gross Margin", "Operating Margin", "Net Margin"],
            **{y: [
                f"{gm_pct[i]:.1f}%"  if gm_pct[i]  else "—",
                f"{opm_pct[i]:.1f}%" if opm_pct[i] else "—",
                f"{npm_pct[i]:.1f}%" if npm_pct[i] else "—",
            ] for i, y in enumerate(years)}
        }).set_index("Metric")
        st.dataframe(margin_df, use_container_width=True)

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
        # Year-end price chart
        if price_s.notna().any():
            fig_px = make_line(years, [price_s.tolist()], ["Price"],
                               "Year-End Stock Price  ($)", height=300)
            fig_px.update_layout(yaxis=dict(tickprefix="$", showgrid=True,
                                             gridcolor=C_BORDER2, tickfont=dict(size=10, color=C_TEXT3),
                                             zeroline=False, showline=False))
            st.plotly_chart(fig_px, use_container_width=True, config={"displayModeBar": False})
        else:
            # Fall back to full daily price history
            with st.spinner(""):
                prices = fetch_prices(ticker)
            if not prices.empty:
                close_col = next((c for c in ["adj_close", "adjusted_close", "close"]
                                  if c in prices.columns), prices.columns[1])
                fig_px = go.Figure(go.Scatter(
                    x=prices["date"], y=prices[close_col],
                    mode="lines", name="Price",
                    line=dict(color=C_ACCENT, width=1.5),
                    hovertemplate="%{x|%d %b %Y}<br>$%{y:.2f}<extra></extra>",
                ))
                fig_px.update_layout(**CHART_BASE)
                fig_px.update_layout(height=300, showlegend=False,
                    yaxis=dict(tickprefix="$", showgrid=True, gridcolor=C_BORDER2,
                               tickfont=dict(size=10, color=C_TEXT3), zeroline=False, showline=False))
                st.plotly_chart(fig_px, use_container_width=True, config={"displayModeBar": False})
            else:
                st.markdown('<span style="color:#999;font-size:0.82rem">Price data not available.</span>', unsafe_allow_html=True)

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
            val_display = pd.DataFrame({
                "Metric": val_names,
                **{y: [val_ys[j][i] if val_ys[j][i] else None for j in range(len(val_names))]
                   for i, y in enumerate(years)}
            }).set_index("Metric")
            val_display = val_display.applymap(lambda v: fmt_multiple(v) if v else "—")
            st.dataframe(val_display, use_container_width=True)
        else:
            st.markdown('<span style="color:#999;font-size:0.82rem">Stock price required to calculate multiples. Add a Stock Price column to your Google Sheet.</span>', unsafe_allow_html=True)

    # TAB 5 — Working Capital
    with tab5:
        with st.expander("Debug: Balance Sheet columns"):
            st.write("BS columns:", bs.columns.tolist() if not bs.empty else "EMPTY")
            if not bs.empty:
                st.write("BS first row:", bs.head(1).to_dict())

        def days(numerator_s, denominator_s, label):
            """Calculate a days metric year by year. Returns list aligned to bs_years."""
            result = []
            for i in range(len(bs_years)):
                try:
                    num = float(numerator_s.iloc[i])   if i < len(numerator_s)   and pd.notna(numerator_s.iloc[i])   else None
                    den = float(denominator_s.iloc[i]) if i < len(denominator_s) and pd.notna(denominator_s.iloc[i]) else None
                    if num is not None and den is not None and den > 0:
                        result.append((num / den) * 365)
                    else:
                        result.append(None)
                except:
                    result.append(None)
            return result

        dso_list  = days(ar_s,  rev_s,  "DSO")
        inv_list  = days(inv_s, cogs_s, "Inventory Days")
        dpo_list  = days(ap_s,  cogs_s, "DPO")

        # CCC — only where all three components exist
        ccc_list = []
        for i in range(len(bs_years)):
            dso = dso_list[i]; inv = inv_list[i]; dpo = dpo_list[i]
            if dso is not None and inv is not None and dpo is not None:
                ccc_list.append(dso + inv - dpo)
            elif dso is not None and dpo is not None:
                # Some companies have no inventory (service businesses)
                ccc_list.append(dso - dpo)
            else:
                ccc_list.append(None)

        # NWC — year by year
        nwc_list = []
        for i in range(len(bs_years)):
            try:
                ca = float(ca_s.iloc[i]) if i < len(ca_s) and pd.notna(ca_s.iloc[i]) else None
                cl = float(cl_s.iloc[i]) if i < len(cl_s) and pd.notna(cl_s.iloc[i]) else None
                nwc_list.append(ca - cl if ca is not None and cl is not None else None)
            except:
                nwc_list.append(None)

        # ── KPI summary row — latest year ──────────────────────────────────────
        def latest_days(lst):
            vals = [v for v in lst if v is not None]
            return vals[-1] if vals else None

        def fmt_days(val):
            if val is None: return "—"
            return f"{val:.0f} days"

        def fmt_days_delta(lst):
            vals = [v for v in lst if v is not None]
            if len(vals) < 2: return None
            return vals[-1] - vals[-2]  # absolute change in days, not %

        w1, w2, w3, w4, w5 = st.columns(5)

        dso_l  = latest_days(dso_list)
        inv_l  = latest_days(inv_list)
        dpo_l  = latest_days(dpo_list)
        ccc_l  = latest_days(ccc_list)
        nwc_l  = latest(pd.Series(nwc_list, dtype=float))

        def wc_kpi(col, label, val_str, delta_days=None):
            if delta_days is not None:
                sign  = "+" if delta_days >= 0 else ""
                cls   = "delta-up" if delta_days <= 0 else "delta-down"  # fewer days = better for DSO/CCC
                d_html = f'<span class="metric-delta {cls}">{sign}{delta_days:.0f} days YoY</span>'
            else:
                d_html = ""
            col.markdown(f"""
            <div class="metric-block">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{val_str}</div>
                {d_html}
            </div>""", unsafe_allow_html=True)

        wc_kpi(w1, "DSO",            fmt_days(dso_l),  fmt_days_delta(dso_list))
        wc_kpi(w2, "Inventory Days", fmt_days(inv_l),  fmt_days_delta(inv_list))
        wc_kpi(w3, "DPO",            fmt_days(dpo_l),  fmt_days_delta(dpo_list))
        wc_kpi(w4, "Cash Cycle",     fmt_days(ccc_l),  fmt_days_delta(ccc_list))
        wc_kpi(w5, "NWC (Latest)",   fmt_currency(nwc_l))

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Days trend chart ───────────────────────────────────────────────────
        days_ys, days_names = [], []
        if any(v for v in dso_list  if v is not None): days_ys.append(dso_list);  days_names.append("DSO")
        if any(v for v in inv_list  if v is not None): days_ys.append(inv_list);  days_names.append("Inventory Days")
        if any(v for v in dpo_list  if v is not None): days_ys.append(dpo_list);  days_names.append("DPO")
        if any(v for v in ccc_list  if v is not None): days_ys.append(ccc_list);  days_names.append("Cash Cycle")

        if days_ys:
            fig_wc = make_line(bs_years, days_ys, days_names, "Working Capital Days", height=320, suffix=" days")
            fig_wc.update_layout(yaxis=dict(ticksuffix=" d", showgrid=True, gridcolor=C_BORDER2,
                                            tickfont=dict(size=10, color=C_TEXT3),
                                            zeroline=True, zerolinecolor=C_BORDER,
                                            showline=False))
            st.plotly_chart(fig_wc, use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown('<span style="color:#999;font-size:0.82rem">Insufficient balance sheet data to calculate working capital days.</span>', unsafe_allow_html=True)

        # ── NWC trend chart ────────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        if any(v for v in nwc_list if v is not None):
            fig_nwc = make_bar(bs_years,
                               [v/1e9 if v is not None else None for v in nwc_list],
                               "Net Working Capital  ($B)", height=260)
            fig_nwc.update_layout(yaxis=dict(tickprefix="$", ticksuffix="B", showgrid=True,
                                              gridcolor=C_BORDER2, tickfont=dict(size=10, color=C_TEXT3),
                                              zeroline=True, zerolinecolor=C_BORDER, showline=False))
            st.plotly_chart(fig_nwc, use_container_width=True, config={"displayModeBar": False})

        # ── Historical table ───────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<span class="section-label">Historical</span>', unsafe_allow_html=True)

        wc_df = pd.DataFrame({"Year": bs_years})
        wc_df["DSO"]            = [fmt_days(v) for v in dso_list]
        wc_df["Inventory Days"] = [fmt_days(v) for v in inv_list]
        wc_df["DPO"]            = [fmt_days(v) for v in dpo_list]
        wc_df["Cash Cycle"]     = [fmt_days(v) for v in ccc_list]
        wc_df["NWC"]            = [fmt_currency(v) for v in nwc_list]
        wc_display = pd.DataFrame({
            "Metric":         ["DSO", "Inventory Days", "DPO", "Cash Cycle", "NWC"],
            **{bs_years[i]: [
                fmt_days(dso_list[i]),
                fmt_days(inv_list[i]),
                fmt_days(dpo_list[i]),
                fmt_days(ccc_list[i]),
                fmt_currency(nwc_list[i]),
            ] for i in range(len(bs_years))}
        }).set_index("Metric")
        st.dataframe(wc_display, use_container_width=True)

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

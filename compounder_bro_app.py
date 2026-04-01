import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import io
import re
from datetime import datetime

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

# Initialise editable watchlist in session state
if "stocks_list" not in st.session_state:
    st.session_state.stocks_list = [{"Name": k, "Ticker": v} for k, v in STOCKS.items()]

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
    grid-template-columns: 1.4fr 0.55fr 0.85fr 0.85fr 0.7fr 0.85fr 0.7fr 0.85fr 0.7fr 0.7fr 0.7fr 0.6fr 0.65fr;
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
def fetch_fundamental_quarterly(endpoint, ticker):
    """Fetch quarterly data from roic.ai."""
    url = f"{BASE_URL}/{endpoint}/{ticker}"
    params = {"period": "quarterly", "limit": 8, "order": "desc", "apikey": API_KEY}
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        raw = r.json()
        rows = raw if isinstance(raw, list) else raw.get("data", [])
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        for col in ["date", "Date", "period_end", "fiscal_year_end"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
                df = df.rename(columns={col: "Date"})
                break
        skip = {"Date", "ticker", "Ticker", "period", "Period",
                "period_label", "currency", "Currency"}
        for col in df.columns:
            if col not in skip:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.sort_values("Date").reset_index(drop=True)
        return df
    except Exception:
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


# ── Earnings transcript + research report ────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_transcript(ticker, year, quarter):
    """Fetch a single earnings call transcript."""
    url = f"{BASE_URL}/company/earnings-calls/transcript/{ticker}"
    params = {"year": year, "quarter": quarter, "apikey": API_KEY}
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict):
            return data.get("transcript", data.get("text", str(data)))
        return str(data)
    except:
        return None

def fetch_last_4_transcripts(ticker):
    """Fetch the last 4 available quarterly transcripts."""
    from datetime import datetime
    transcripts = []
    now = datetime.now()
    year = now.year
    quarter = (now.month - 1) // 3 + 1
    attempts = 0
    while len(transcripts) < 4 and attempts < 12:
        text = fetch_transcript(ticker, year, quarter)
        if text and len(str(text)) > 100:
            transcripts.append({"year": year, "quarter": quarter, "text": str(text)[:8000]})
        quarter -= 1
        if quarter < 1:
            quarter = 4
            year -= 1
        attempts += 1
    return transcripts

def format_financials_for_prompt(inc, bs, cf, years):
    """Format key financial data as compact text for the AI prompt."""
    def s(df, *cols):
        for c in cols:
            if c in df.columns:
                return pd.to_numeric(df[c], errors="coerce")
        return pd.Series(dtype=float)

    lines = ["=== INCOME STATEMENT (last 5 years) ==="]
    recent_years = years[-5:] if len(years) >= 5 else years
    recent_idx = slice(-len(recent_years), None)

    rev  = s(inc, "is_sales_revenue_turnover", "is_sales_and_services_revenues").iloc[recent_idx].tolist()
    gp   = s(inc, "is_gross_profit").iloc[recent_idx].tolist()
    ebit = s(inc, "ebit").iloc[recent_idx].tolist()
    ni   = s(inc, "is_net_income").iloc[recent_idx].tolist()
    eps  = s(inc, "diluted_eps").iloc[recent_idx].tolist()
    gm   = s(inc, "gross_margin").iloc[recent_idx].tolist()
    opm  = s(inc, "oper_margin").iloc[recent_idx].tolist()
    npm  = s(inc, "profit_margin").iloc[recent_idx].tolist()

    for i, y in enumerate(recent_years):
        def v(lst): 
            try: return f"{lst[i]/1e9:.2f}B" if lst[i] and not pd.isna(lst[i]) else "N/A"
            except: return "N/A"
        def pct(lst):
            try: return f"{lst[i]:.1f}%" if lst[i] and not pd.isna(lst[i]) else "N/A"
            except: return "N/A"
        def ep(lst):
            try: return f"${lst[i]:.2f}" if lst[i] and not pd.isna(lst[i]) else "N/A"
            except: return "N/A"
        lines.append(f"{y}: Rev={v(rev)}, GrossProfit={v(gp)}, EBIT={v(ebit)}, NetIncome={v(ni)}, EPS={ep(eps)}, GM={pct(gm)}, OM={pct(opm)}, NM={pct(npm)}")

    lines.append("\n=== BALANCE SHEET (latest year) ===")
    if not bs.empty:
        def bv(col):
            try:
                val = float(bs[col].iloc[-1]) if col in bs.columns and pd.notna(bs[col].iloc[-1]) else None
                return f"{val/1e9:.2f}B" if val else "N/A"
            except: return "N/A"
        lines.append(f"Total Assets={bv('bs_tot_asset')}, Total Equity={bv('bs_total_equity')}, Net Debt={bv('net_debt')}")
        lines.append(f"Current Assets={bv('bs_cur_asset_report')}, Current Liabilities={bv('bs_cur_liab')}")

    lines.append("\n=== CASH FLOW (last 5 years) ===")
    if not cf.empty:
        fcf = s(cf, "cf_free_cash_flow").iloc[recent_idx].tolist()
        cfo = s(cf, "cf_cash_from_oper").iloc[recent_idx].tolist()
        dep = s(cf, "cf_depr_amort").iloc[recent_idx].tolist()
        cap = s(cf, "cf_cap_expenditures").iloc[recent_idx].tolist()
        cf_years = cf["Date"].dt.year.astype(str).tolist() if "Date" in cf.columns else recent_years
        cf_recent = cf_years[-5:] if len(cf_years) >= 5 else cf_years
        for i, y in enumerate(cf_recent):
            def cv(lst):
                try: return f"{lst[i]/1e9:.2f}B" if lst[i] and not pd.isna(lst[i]) else "N/A"
                except: return "N/A"
            lines.append(f"{y}: CFO={cv(cfo)}, FCF={cv(fcf)}, D&A={cv(dep)}, CapEx={cv(cap)}")

    return "\n".join(lines)

# ── EDGAR 10-K / 20-F fetcher ────────────────────────────────────────────────

def edgar_get_cik(ticker):
    """Look up CIK using SEC's official company_tickers.json — most reliable method."""
    try:
        hdrs = {"User-Agent": "compounder-app research@example.com"}
        r = requests.get("https://www.sec.gov/files/company_tickers.json",
                         headers=hdrs, timeout=15)
        r.raise_for_status()
        t_upper = ticker.upper()
        for entry in r.json().values():
            if entry.get("ticker", "").upper() == t_upper:
                return str(entry["cik_str"]).zfill(10)
        return None
    except:
        return None


def edgar_latest_filing(cik, form_type):
    """Return (accession_no_dashes, filing_date) for the most recent matching form."""
    try:
        hdrs = {"User-Agent": "compounder-app research@example.com"}
        r = requests.get(f"https://data.sec.gov/submissions/CIK{cik}.json",
                         headers=hdrs, timeout=15)
        r.raise_for_status()
        recent = r.json().get("filings", {}).get("recent", {})
        forms   = recent.get("form", [])
        accnums = recent.get("accessionNumber", [])
        dates   = recent.get("filingDate", [])
        for i, form in enumerate(forms):
            if form in (form_type, form_type + "/A"):
                return accnums[i].replace("-", ""), dates[i]
        return None, None
    except:
        return None, None


def edgar_fetch_filing_text(cik, accession_no_dashes, max_chars=80000):
    """
    Fetch Business (Item 1) and MD&A (Item 7) from an EDGAR filing.
    Uses the filing index JSON to find the primary document reliably.
    """
    import re as _re
    hdrs = {"User-Agent": "compounder-app research@example.com"}

    try:
        # Format accession for URL: 0001234567890123 -> 0001234567/89/0123
        acc = accession_no_dashes
        acc_dashes = f"{acc[:10]}-{acc[10:12]}-{acc[12:]}"
        cik_int = int(cik)

        # Use the filing index JSON — much more reliable than parsing HTML index
        idx_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        # Actually use the index JSON for this specific accession
        index_json_url = (f"https://www.sec.gov/cgi-bin/browse-edgar"
                          f"?action=getcompany&CIK={cik_int}&type=10-K"
                          f"&dateb=&owner=include&count=1&search_text=")

        # Direct approach: fetch the filing index page
        idx_page_url = (f"https://www.sec.gov/Archives/edgar/data/"
                        f"{cik_int}/{acc}/{acc_dashes}-index.htm")
        r_idx = requests.get(idx_page_url, headers=hdrs, timeout=15)

        if not r_idx.ok:
            # Try without leading zeros in cik
            idx_page_url = (f"https://www.sec.gov/Archives/edgar/data/"
                            f"{cik_int}/{acc_dashes.replace('-','')}/{acc_dashes}-index.htm")
            r_idx = requests.get(idx_page_url, headers=hdrs, timeout=15)

        # Find the primary document — look for the largest .htm that isn't an exhibit
        doc_url = None
        if r_idx.ok:
            # Parse table rows to find document type and href
            rows = _re.findall(
                r'<tr[^>]*>.*?</tr>', r_idx.text, _re.DOTALL | _re.IGNORECASE)
            candidates = []
            for row in rows:
                href_m = _re.search(r'href="(/Archives[^"]+\.htm)"', row, _re.IGNORECASE)
                type_m = _re.search(r'<td[^>]*>\s*(10-K|20-F|FORM 10-K|FORM 20-F)\s*</td>', row, _re.IGNORECASE)
                if href_m and type_m:
                    candidates.append("https://www.sec.gov" + href_m.group(1))
            if not candidates:
                # Broader search — any .htm link containing the accession
                all_links = _re.findall(r'href="(/Archives/edgar/data/[^"]+\.htm)"',
                                        r_idx.text, _re.IGNORECASE)
                candidates = ["https://www.sec.gov" + l for l in all_links
                              if acc.lower() in l.lower().replace("-", "").replace("/", "")]
            if candidates:
                doc_url = candidates[0]

        if not doc_url:
            return None

        r_doc = requests.get(doc_url, headers=hdrs, timeout=60)
        if not r_doc.ok:
            return None

        # Clean HTML to text
        text = _re.sub(r"<[^>]{1,200}>", " ", r_doc.text)
        text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&#160;", " ")
        text = _re.sub(r"\s{3,}", "\n\n", text).strip()

        # Extract Item 1 (Business) and Item 7 (MD&A)
        sections = {}
        patterns = [
            ("BUSINESS",
             r"(?i)item\s*1[\s.]+business\b",
             r"(?i)item\s*1a[\s.]+risk"),
            ("MD&A",
             r"(?i)item\s*7[\s.]+management.{0,60}?discussion",
             r"(?i)item\s*7a[\s.]+"),
        ]
        for name, start_pat, end_pat in patterns:
            m_s = _re.search(start_pat, text)
            if not m_s:
                continue
            tail  = text[m_s.end():]
            m_e   = _re.search(end_pat, tail)
            chunk = tail[:m_e.start()] if m_e else tail[:30000]
            sections[name] = chunk[:25000].strip()

        if sections:
            out = ""
            for name, txt in sections.items():
                out += f"\n\n=== {name} ===\n{txt}"
            return out[:max_chars]

        # Fallback: mid-document slice
        return text[5000:5000 + max_chars]

    except Exception:
        return None


def fetch_10k_text(ticker):
    """
    Main entry: CIK lookup → filing search → text extraction.
    Returns (text, form_type, date) or (None, None, None).
    """
    cik = edgar_get_cik(ticker)
    if not cik:
        return None, None, None
    for form in ("10-K", "20-F"):
        acc, date = edgar_latest_filing(cik, form)
        if acc:
            text = edgar_fetch_filing_text(cik, acc)
            if text and len(text) > 500:
                return text, form, date
    return None, None, None


# ── Report generation — dual model path ──────────────────────────────────────

def _build_prompt(company_name, ticker, financials_text, transcript_text,
                  extra_context="", source_note=""):
    """Shared prompt template used by both NVIDIA and Haiku paths."""
    return f"""MASTER AI INSTRUCTION: THE OBJECTIVITY MANDATE
You must remain ruthlessly objective and strictly unbiased. Your mandate is not to pitch a long or short position, but to uncover the absolute ground truth of the business. Present both structural strengths and fatal flaws with equal clinical detachment. Do not sugarcoat poor capital allocation, and do not dismiss durable moats. Analyze the data without emotion; it does not matter if the company looks good or bad to the reader.

You are writing a comprehensive research report on {company_name} ({ticker}) for a sophisticated investment committee. {source_note}

ACCURACY & SOURCING RULES — ZERO TOLERANCE:
Every financial figure must be sourced inline immediately after the number, e.g. (FY2024 Income Statement), (FY2024 Balance Sheet), (FY2024 Cash Flow Statement). Every piece of management commentary must include a direct verbatim quote where available, followed by its source, e.g. CEO John Smith stated "we expect margins to expand by 200 basis points" (Q3 2024 Earnings Call). Every fact from the SEC filing must be cited, e.g. (10-K 2024, Business Section) or (20-F 2024, MD&A). Do not state any number without a source. Do not paraphrase management when a direct quote exists — use their exact words and cite the call. Before writing any number, double-check it against the provided data.

CURRENCY: State the reporting currency explicitly for every figure — "USD 4.2B", "EUR 890M", "INR 1.47T". Never use bare currency symbols.

FORMATTING — ABSOLUTE AND NON-NEGOTIABLE:
Write exclusively in continuous flowing prose. No bullet points, no dashes as list markers, no numbered sub-lists, no tables anywhere in the body. Every section must read like a chapter from a serious investment research book — dense, analytical paragraphs that build a sustained argument. Do not write one sentence per line. Every paragraph must be at minimum five sentences, containing a point, evidence from the data, analysis of what that evidence means, and a conclusion. Begin the report immediately with the first section heading — no preamble, no meta-commentary. Section headings must appear exactly as written below on their own line with no markdown characters.

DATA PROVIDED:
{financials_text}{transcript_text}{extra_context}

1. THE FOUNDATION: BUSINESS OVERVIEW & TANGIBLE SCALE

Stripped of all corporate jargon and marketing buzzwords, explain exactly what this business does and walk through the life cycle of a single dollar from the customer's wallet to the company's bank account. Then quantify the tangible scale of the operation with precision — exact physical assets such as number of retail locations, aircraft, manufacturing plants, or logistics hubs, or digital scale such as monthly active users, data centres, or compute capacity, sourced from the filing or financial statements. For each distinct operating segment, explain the exact mechanism for making money and state precisely what percentage of total revenue and operating profit that segment represents, using real figures. Define what a single "unit" of sale is for this business and calculate the true contribution margin of that unit — revenue minus strictly variable costs — and identify at what volume the business breaks even. Spend substantial space here because understanding the precise economics of value creation and value leakage is the foundation of everything that follows.

2. THE BATTLEFIELD: INDUSTRY LANDSCAPE & COMPETITIVE PROFILE

Describe the broader industry with precision: is it consolidated or highly fragmented, experiencing secular growth or structural decline, and what phase of the industry life cycle are we in. Name the top three to five direct competitors and identify in which specific arenas — geographic regions, product tiers, customer demographics — they directly clash with this company. Analyse how competitors fundamentally differ in their operating models, cost structures, vertical integration, and target audiences, using quantitative comparisons where the data supports it. Then prove the moat — do not simply name it. If the claim is network effects, explain precisely how adding one more user or customer makes the product more valuable and why a well-funded new entrant cannot replicate this. If the claim is cost advantage, show the actual cost gap in basis points and explain the structural source of it. If switching costs, quantify the financial, operational, and psychological friction a customer endures to replace this product. A named moat without a mechanism is not an investment insight — it is a platitude.

3. THE GENERALS: MANAGEMENT, ALIGNMENT & TRACK RECORD

Identify the key decision-makers — CEO, CFO, and COO — their background prior to this company, and how long they have held their current positions. Then audit the three to four most consequential strategic or capital allocation decisions made by this specific management team over the last decade, including major acquisitions, aggressive expansions, or pivots in strategy, and deliver a clear verdict on whether each decision created or destroyed shareholder value, backed by measurable outcomes. Examine insider ownership precisely: what percentage do executives and founders own, are they buying shares on the open market, and what does the pattern of stock-based compensation and insider selling tell you about their conviction in the business. Where earnings call transcripts are available, use direct verbatim quotes from management to assess their candour, strategic clarity, and willingness to acknowledge problems — quote them precisely and cite each call. Assess whether the incentive structures disclosed in the proxy or filing align management with long-term free cash flow per share and return on invested capital, or whether they are optimising for short-term adjusted metrics that flatter performance.

4. THE CHOKEPOINTS: CUSTOMER DYNAMICS & SUPPLY CHAIN

Analyse the customer base with specificity: is revenue concentrated among a few large clients or distributed across millions of small ones, and is the purchase an operational necessity or highly discretionary. Quantify switching costs — what is the precise financial, operational, and psychological friction a customer endures to replace this product with a competitor's, and where has the company disclosed evidence of high retention, long contract durations, or high switching penalties in its filings. Examine the supply chain: does the company dictate pricing to its suppliers, or are they at the mercy of consolidated vendors with significant leverage. Identify any single points of failure in the supply chain that could halt operations or compress margins materially, and assess whether management has disclosed credible mitigation strategies, citing specific earnings call commentary or filing disclosures where available.

5. THE SCORECARD: FINANCIAL TRUTH & CAPITAL ALLOCATION

Begin with the balance sheet forensically: total assets, equity, net debt, and debt maturity profile. Calculate the interest coverage ratio using operating income against interest expense from the income statement and state what it tells you about financial fragility. Walk through the cash conversion cycle in full — days sales outstanding, days payable outstanding, and inventory days — and explain what the resulting cycle duration reveals about the quality of the business model; a negative cash conversion cycle is a mark of exceptional business quality and must be discussed explicitly if present. Perform the Owner's Earnings calculation showing every line with its source: reported net income, plus depreciation and amortisation, adjusted for working capital changes, minus maintenance capital expenditure. Compare the result to reported net income and explain any material divergence. Then analyse whether this company consistently generates a return on invested capital that exceeds its cost of capital across a full economic cycle, using multi-year ROIC data from the financial statements. Stress-test the balance sheet: could it survive a severe multi-year recession without dilutive equity issuance or insolvency risk. Finally assess capital allocation historically — acquisitions, buybacks, dividends, organic reinvestment — and deliver a verdict on whether management has been a good steward of shareholder capital.

6. THE ASYMMETRIC BET: GROWTH RUNWAY & THE KILL SHOT

Quantify the realistic serviceable obtainable market taking geographic and regulatory constraints into account, state the current penetration rate, and explain the structural drivers that could expand either the market or the company's share within it anchored in evidence from the filing, earnings call guidance, or observable revenue trends. Separate genuine structural growth from cyclical recovery or one-time tailwinds explicitly. Then deliver the bear case — the highest-probability sequence of events, whether regulatory, competitive, or macroeconomic, that could cause this company to permanently lose fifty percent or more of its intrinsic value over the next five years. This must be a specific, mechanistic argument with a plausible chain of causation, not a generic list of risks. Assess the probability and magnitude of this scenario honestly and without minimisation.

7. CATALYSTS & INFLECTION POINTS

Identify the specific, trackable events over the next six to eighteen months — product launches, contract expirations, regulatory rulings, M&A closures — that will force the market to actively reprice this asset, and explain the directional impact of each. Then describe the undeniable multi-year secular tailwinds and headwinds that are fundamentally driving revenue growth or compressing margins, distinguishing between macro forces the company cannot control and structural competitive dynamics it can influence. If the business is undergoing a fundamental transition — shifting from high-growth cash burn to mature cash cow, or experiencing structural margin degradation — quantify that inflection precisely and assess whether the current market pricing reflects it.

LENGTH MANDATE — THIS IS CRITICAL:
Each of the seven sections must be written to its full analytical depth. Do not truncate a section because you have covered the headline point — go deeper. For each section, after writing your initial analysis, ask yourself: what have I not yet examined? What nuance have I glossed over? What second-order implication have I not traced through? Then write that. A section on financial strength is not complete after one paragraph on leverage — it must cover leverage, interest coverage, cash conversion cycle mechanics with actual day counts, the full Owner's Earnings walk-through with every line sourced, ROIC versus cost of capital across multiple years, balance sheet stress testing, and a verdict on capital allocation quality. Every section should be thorough enough that a sophisticated investor could not reasonably ask "but what about X?" and find that X was not addressed. The total report should run to several thousand words. Do not stop writing a section until you have genuinely exhausted what the data and research supports saying.

Remember: every assertion must be backed by evidence. Every number must have a source. Every management quote must be verbatim and cited. Present the ground truth, not a sales pitch."""


def _call_nvidia(messages, api_key, max_tokens=32000):
    """Single NVIDIA API call. Returns text or raises."""
    r = requests.post(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key}"},
        json={
            "model": "nvidia/llama-3.1-nemotron-ultra-253b-v1",
            "max_tokens": max_tokens,
            "temperature": 0.6,
            "top_p": 0.95,
            "messages": messages,
        },
        timeout=300,
    )
    r.raise_for_status()
    msg = r.json()["choices"][0]["message"]
    return str(msg.get("content") or msg.get("reasoning_content") or msg.get("text") or "").strip()


def generate_report_nvidia(company_name, ticker, financials_text, transcripts, filing_text, form_type, filing_date):
    """
    Section-by-section generation strategy.
    Each of the 7 sections is requested in a separate API call with the full
    data context but only the instructions for that one section.
    This prevents any single call from hitting the token ceiling mid-report,
    and lets each section receive the model's full attention and token budget.
    """
    transcript_text = _format_transcripts(transcripts)
    filing_section  = f"\n\n=== {form_type} FILING ({filing_date}) ===\n{filing_text[:60000]}" if filing_text else ""
    source_note     = f"You have been provided the {form_type} filing ({filing_date}), financial statements, and earnings transcripts."
    api_key         = st.secrets.get("NVIDIA_API_KEY", "")

    # Shared data context — sent with every section call
    data_block = f"""You are writing one section of a comprehensive equity research report on {company_name} ({ticker}) for a sophisticated investment committee. {source_note}

OBJECTIVITY MANDATE: Remain ruthlessly objective. Present structural strengths and fatal flaws with equal clinical detachment. Analyze the data without emotion.

SOURCING RULES: Every financial figure sourced inline, e.g. (FY2024 Income Statement). Every management quote must be verbatim and cited to the specific call, e.g. (Q3 2024 Earnings Call). Every SEC filing fact cited, e.g. (10-K 2024, Business Section). State currency explicitly: "USD 4.2B", "EUR 890M".

FORMATTING: Continuous flowing prose only. No bullet points, no dashes as list markers, no sub-lists. Every paragraph minimum five sentences with a point, evidence, analysis, and conclusion. Write the section heading exactly as given on its own line with no markdown characters, then begin immediately.

LENGTH: Write this section to its absolute maximum depth. Do not stop when you have covered the headline point — go deeper into every sub-dimension. A sophisticated investor should not be able to ask "but what about X?" and find X unaddressed. Exhaust everything the data supports.

DATA:
{financials_text}{transcript_text}{filing_section}

NOW WRITE ONLY THE FOLLOWING SECTION:
"""

    # Section definitions — heading + specific instructions
    sections = [
        ("1. THE FOUNDATION: BUSINESS OVERVIEW & TANGIBLE SCALE",
         "Stripped of all jargon, explain exactly what this business does and walk through the life cycle of a single dollar from the customer to the company. Quantify the exact physical or digital scale with sourced figures. For each operating segment state the exact revenue and operating profit contribution as a percentage. Define the unit of sale and calculate the true contribution margin. Trace gross profit down to operating profit and free cash flow, identifying where value is created and where it leaks. Explain the full margin structure trend over the last ten years and what it reveals about the business model."),

        ("2. THE BATTLEFIELD: INDUSTRY LANDSCAPE & COMPETITIVE PROFILE",
         "Describe the industry structure with precision — consolidated or fragmented, secular growth or decline, what phase of the cycle. Name the top three to five direct competitors and the specific arenas where they clash with this company. Analyse how they differ in operating model, cost structure, and target audience. Then prove the moat — do not name it, prove it mechanistically. Show exactly how the competitive advantage prevents a well-funded entrant from stealing share, with quantitative evidence."),

        ("3. THE GENERALS: MANAGEMENT, ALIGNMENT & TRACK RECORD",
         "Identify CEO, CFO, and COO — their background and tenure. Audit the three to four most consequential capital allocation decisions of this management team over the last decade and deliver a clear verdict on whether each created or destroyed value, with measured outcomes. Examine insider ownership precisely. Use direct verbatim quotes from earnings call transcripts where available, citing each call. Assess whether incentive structures align management with long-term free cash flow per share and ROIC, or short-term adjusted metrics."),

        ("4. THE CHOKEPOINTS: CUSTOMER DYNAMICS & SUPPLY CHAIN",
         "Analyse customer concentration precisely — is revenue distributed or whale-dependent, is the purchase a necessity or discretionary. Quantify switching costs with specific evidence from filings: contract durations, retention rates, switching penalties disclosed. Examine the supply chain — does the company dictate pricing or are they at the mercy of consolidated vendors. Identify any single points of failure that could halt operations and assess management's disclosed mitigation strategies with direct citation."),

        ("5. THE SCORECARD: FINANCIAL TRUTH & CAPITAL ALLOCATION",
         "Cover the balance sheet forensically: total assets, equity, net debt, debt maturity profile, and interest coverage ratio calculated from the income statement. Walk through the full cash conversion cycle — calculate DSO, DPO, and inventory days from the financial statements and explain what the cycle duration reveals. Perform the complete Owner's Earnings calculation showing every line with source: net income + D&A + working capital changes - maintenance capex. Analyse ROIC versus cost of capital across multiple years. Stress-test the balance sheet against a severe multi-year recession. Deliver a verdict on capital allocation quality across acquisitions, buybacks, dividends, and organic reinvestment."),

        ("6. THE ASYMMETRIC BET: GROWTH RUNWAY & THE KILL SHOT",
         "Quantify the realistic serviceable obtainable market with geographic and regulatory constraints, state current penetration, and explain the structural growth drivers anchored in evidence. Separate structural growth from cyclical recovery explicitly. Then deliver the bear case — the specific highest-probability sequence of events that could cause this company to permanently lose 50% or more of intrinsic value over five years. This must be a mechanistic argument with a causal chain, not a generic risk list. Assess probability and magnitude without minimisation."),

        ("7. CATALYSTS & INFLECTION POINTS",
         "Identify specific trackable events over the next 6 to 18 months that will force a market repricing and explain the directional impact of each with evidence. Describe the undeniable multi-year secular tailwinds and headwinds driving revenue or compressing margins, distinguishing macro forces from competitive dynamics. If the business is undergoing a fundamental transition, quantify the inflection precisely and assess whether current market pricing reflects it."),
    ]

    try:
        import re as _re_assemble
        report_parts = []

        for heading, instructions in sections:
            section_prompt = data_block + f"{heading}\n\n{instructions}"
            text = _call_nvidia([{"role": "user", "content": section_prompt}], api_key)
            if not text:
                continue

            text = text.strip()

            # Remove the exact heading (and any markdown-wrapped variant) from the text
            sec_num = heading.split(".")[0].strip()  # e.g. "1"
            # Strip any line that starts with this section number + dot/paren
            lines = text.split("\n")
            cleaned_lines = []
            for line in lines:
                stripped = line.strip().lstrip("*#").strip()
                # Drop lines that ARE the heading (start with "1." or "1)")
                if _re_assemble.match(rf"^{sec_num}[.\)]\s+", stripped):
                    continue
                cleaned_lines.append(line)

            body = "\n".join(cleaned_lines).strip()
            # Strip any remaining leading blank lines
            body = body.lstrip("\n").strip()

            if not body:
                continue

            # Canonical heading + body — exactly one heading per section
            section_text = f"{heading}\n\n{body}"
            report_parts.append(section_text)

        if not report_parts:
            return "NVIDIA returned empty responses for all sections."

        # Join with double newline — each part already starts with its heading
        full_report = "\n\n".join(report_parts)
        return _clean_report(full_report)

    except Exception as e:
        return f"Error generating report via NVIDIA: {e}"


def generate_report_haiku(company_name, ticker, financials_text, transcripts):
    """Use Claude Haiku with web_search tool when no SEC filing is available."""
    transcript_text = _format_transcripts(transcripts)
    source_note = ("No SEC filing is available for this company. "
                   "Use the web_search tool extensively to research the business model, "
                   "competitive position, and recent developments before writing.")

    prompt = _build_prompt(company_name, ticker, financials_text,
                           transcript_text, "", source_note)
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }
        payload = {
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 16000,
            "tools": [{"type": "web_search_20250305", "name": "web_search"}],
            "messages": [{"role": "user", "content": prompt}],
        }
        r = requests.post("https://api.anthropic.com/v1/messages",
                          headers=headers, json=payload, timeout=180)
        r.raise_for_status()
        data = r.json()

        # Tool use loop
        messages = [{"role": "user", "content": prompt}]
        for _ in range(8):
            messages.append({"role": "assistant", "content": data["content"]})
            if data.get("stop_reason") == "end_turn":
                break
            tool_results = [
                {"type": "tool_result", "tool_use_id": b["id"], "content": "Search completed."}
                for b in data["content"] if b.get("type") == "tool_use"
            ]
            if not tool_results:
                break
            messages.append({"role": "user", "content": tool_results})
            r2 = requests.post("https://api.anthropic.com/v1/messages",
                               headers=headers,
                               json={**payload, "messages": messages},
                               timeout=180)
            r2.raise_for_status()
            data = r2.json()

        text_parts = [b["text"] for b in data["content"] if b.get("type") == "text"]
        return _clean_report("\n\n".join(text_parts))
    except Exception as e:
        return f"Error generating report via Haiku: {e}"


def _format_transcripts(transcripts):
    if transcripts:
        txt = "\n\n=== EARNINGS CALL TRANSCRIPTS (last 4 quarters) ==="
        for t in transcripts:
            txt += f"\n\nQ{t['quarter']} {t['year']} Earnings Call (excerpt):\n{t['text'][:4000]}"
        return txt
    return "\n\n=== EARNINGS CALL TRANSCRIPTS ===\nNo transcripts available."


def generate_research_report(company_name, ticker, financials_text, transcripts, web_context=""):
    """
    Routing logic:
    - Ticker with exchange suffix (e.g. CSU.TO, RELIANCE.NS, AZN.L) → non-US listed
      → skip EDGAR entirely, use Haiku with web search
    - No suffix → US-listed, try EDGAR for 10-K or 20-F
      → Found: use NVIDIA with filing text
      → Not found: fall back to Haiku with web search
    """
    import re as _re

    # Detect exchange suffix: any ticker containing a dot followed by 1-4 letters at the end
    has_suffix = bool(_re.search(r"[.][A-Z]{1,4}$", ticker.upper()))

    if has_suffix:
        # Non-US stock — go straight to Haiku
        return generate_report_haiku(company_name, ticker, financials_text,
                                     transcripts), "haiku", None

    # US-listed — try EDGAR
    filing_text, form_type, filing_date = fetch_10k_text(ticker)
    if filing_text:
        return generate_report_nvidia(company_name, ticker, financials_text,
                                      transcripts, filing_text, form_type, filing_date), "nvidia", form_type

    # EDGAR came up empty — fall back to Haiku
    return generate_report_haiku(company_name, ticker, financials_text,
                                 transcripts), "haiku", None


def _clean_report(text):
    """Strip preamble, markdown, bullet points, and fix currency rendering."""
    import re as _re

    # No preamble strip needed — section assembly guarantees correct heading order

    # Remove markdown headings
    text = _re.sub(r"(?m)^#{1,6}\s*", "", text)

    # Remove bold/italic
    text = _re.sub(r"\*{2}(.+?)\*{2}", r"\1", text, flags=_re.DOTALL)
    text = _re.sub(r"\*(.+?)\*",       r"\1", text)

    # Convert bullet/dash list lines into prose sentences
    def _debullet(m):
        line = m.group(1).strip()
        # Preserve section headings like "1. BUSINESS OVERVIEW"
        if _re.match(r"^\d+[.\)]\s+", line):
            return line
        if line and line[-1] not in ".!?:":
            line = line[0].upper() + line[1:] + "."
        else:
            line = line[0].upper() + line[1:]
        return line + " "

    text = _re.sub(r"(?m)^[ \t]*[-\*\u2022\u2013]\s+(.+)$", _debullet, text)

    # Fix currency placeholder squares (■ □ \ufffd before digits)
    text = _re.sub(r"[\u25a0\u25a1\ufffd](\d)", r"\1", text)

    # Collapse 3+ blank lines to 2
    text = _re.sub(r"\n{3,}", "\n\n", text)

    # Merge orphaned short paragraphs (< 120 chars, not a section heading)
    # into the following paragraph so they form proper flowing prose
    paras = text.split("\n\n")
    merged = []
    i = 0
    while i < len(paras):
        p = paras[i].strip()
        # Section headings: keep alone
        if _re.match(r"^\d+[.\)]\s+[A-Z]{3}", p):
            merged.append(p)
            i += 1
        # Short orphan — merge forward
        elif len(p) < 120 and i + 1 < len(paras) and not _re.match(r"^\d+[.\)]\s+[A-Z]{3}", paras[i+1].strip()):
            combined = p.rstrip()
            # Add space joiner — ensure sentence ends with punctuation
            if combined and combined[-1] not in ".!?":
                combined += "."
            combined += " " + paras[i+1].strip()
            paras[i+1] = combined
            i += 1  # skip current, let next iteration pick up combined
        else:
            merged.append(p)
            i += 1

    text = "\n\n".join(merged)
    return text.strip()
def build_report_pdf(company, ticker, report_text, transcripts, chart_figs=None):
    """
    Build a professional research report PDF.
    chart_figs: list of (title, plotly Figure) tuples — rendered as images, no extra tokens.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm, mm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
        KeepTogether, Image as RLImage, PageBreak
    )
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
    import re, io
    from datetime import datetime

    buf = io.BytesIO()
    W, H = A4

    # ── Colours ──────────────────────────────────────────────────────────────
    INK      = colors.HexColor("#111111")
    BODY_CLR = colors.HexColor("#2A2A2A")
    MID      = colors.HexColor("#555555")
    MUTED    = colors.HexColor("#888888")
    RULE_CLR = colors.HexColor("#DDDDDD")
    LIGHT_BG = colors.HexColor("#F7F7F7")

    # ── Styles ────────────────────────────────────────────────────────────────
    def S(name, **kw):
        defaults = dict(fontName="Helvetica", fontSize=10, leading=15,
                        textColor=BODY_CLR, spaceBefore=0, spaceAfter=0,
                        alignment=TA_LEFT)
        defaults.update(kw)
        return ParagraphStyle(name, **defaults)

    s_cover_co   = S("cco",  fontName="Helvetica",      fontSize=10, textColor=MUTED, spaceAfter=2)
    s_cover_name = S("cnm",  fontName="Helvetica-Bold",  fontSize=26, textColor=INK,
                     leading=30, spaceAfter=6)
    s_cover_sub  = S("csb",  fontName="Helvetica",      fontSize=12, textColor=MID,  spaceAfter=4)
    s_cover_meta = S("cmt",  fontName="Helvetica",      fontSize=8.5, textColor=MUTED)
    s_disc       = S("dsc",  fontName="Helvetica-Oblique", fontSize=7.5, textColor=MUTED,
                     spaceAfter=12, leading=11)
    s_sec        = S("sec",  fontName="Helvetica-Bold",  fontSize=11, textColor=INK,
                     spaceBefore=20, spaceAfter=6, leading=14)
    s_body       = S("bdy",  fontName="Helvetica",       fontSize=9.5, textColor=BODY_CLR,
                     leading=15, spaceAfter=8, alignment=TA_JUSTIFY)
    s_caption    = S("cap",  fontName="Helvetica-Oblique", fontSize=8, textColor=MUTED,
                     spaceBefore=3, spaceAfter=10, alignment=TA_CENTER)
    s_footer     = S("ftr",  fontName="Helvetica",       fontSize=7.5, textColor=MUTED,
                     alignment=TA_CENTER)
    s_source     = S("src",  fontName="Helvetica-Oblique", fontSize=8, textColor=MUTED,
                     spaceAfter=14, leading=11)

    story = []
    now   = datetime.now().strftime("%d %B %Y")
    lm    = 2.2*cm
    rm    = 2.2*cm
    usable_w = W - lm - rm

    def hr(thick=0.5, color=RULE_CLR, before=4, after=8):
        return HRFlowable(width="100%", thickness=thick, color=color,
                          spaceBefore=before*mm, spaceAfter=after*mm)

    # ── Cover ─────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 1.2*cm))
    story.append(Paragraph("EQUITY RESEARCH", s_cover_co))
    story.append(Paragraph(company, s_cover_name))
    story.append(Paragraph(ticker, s_cover_sub))
    story.append(Spacer(1, 0.4*cm))
    story.append(hr(thick=1.5, color=INK, before=0, after=4))
    tc = f"{len(transcripts)} earnings transcript(s)" if transcripts else "No transcripts available"
    story.append(Paragraph(f"Generated {now}  \u00b7  {tc}  \u00b7  Fundamental analysis", s_cover_meta))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        "This report is AI-generated for informational purposes only and does not constitute "
        "investment advice. All financial figures are sourced from roic.ai. "
        "Verify all data independently before making investment decisions.",
        s_disc))
    story.append(hr())

    # ── Helper: render a plotly figure as an image ────────────────────────────
    def add_chart(fig, title, width_cm=16):
        try:
            import plotly.io as pio
            img_bytes = pio.to_image(fig, format="png", width=900, height=380,
                                      scale=2, engine="kaleido")
            img_buf = io.BytesIO(img_bytes)
            img_w   = width_cm * cm
            img_h   = img_w * (380 / 900)
            story.append(RLImage(img_buf, width=img_w, height=img_h))
            story.append(Paragraph(title, s_caption))
        except Exception:
            pass  # skip chart silently if kaleido not available

    # ── Parse and render report sections ─────────────────────────────────────
    # Match headings like:
    #   "1. THE FOUNDATION: BUSINESS OVERVIEW & TANGIBLE SCALE"
    #   "2. THE BATTLEFIELD: INDUSTRY LANDSCAPE & COMPETITIVE PROFILE"
    # Requires: digit, dot, space, then THE or all-caps word
    section_re = re.compile(
        r"(?m)^(\d+[.\)]\s+(?:THE\s+)?[A-Z][A-Z0-9 :&'\-\/\(\),]{4,})\s*$"
    )
    parts = section_re.split(report_text)

    # Any text before first heading (preamble — should be empty after _clean_report)
    if parts[0].strip():
        for para in parts[0].strip().split("\n\n"):
            if para.strip():
                story.append(Paragraph(para.strip(), s_body))

    # Chart placement: section 1 (Foundation) → Revenue, section 5 (Scorecard) → FCF
    SECTION_CHART_MAP = {
        "1": 0,  # THE FOUNDATION → Revenue chart
        "5": 1,  # THE SCORECARD  → FCF chart
    }

    i = 1
    while i < len(parts) - 1:
        heading  = parts[i].strip()
        body_txt = parts[i+1] if i+1 < len(parts) else ""
        sec_num  = heading[0]  # "1", "2" … "7"

        # Section break + heading
        story.append(KeepTogether([
            hr(thick=0.5, before=4, after=3),
            Paragraph(heading, s_sec),
        ]))

        # Body — split on double newline, render each as a prose paragraph
        paragraphs = [p.strip() for p in re.split(r"\n\n+", body_txt) if p.strip()]
        for para in paragraphs:
            # Detect sub-headings that leaked through (short all-caps lines)
            if re.match(r"^[A-Z][A-Z\s&:]{4,}:?\s*$", para) and len(para) < 80:
                story.append(Spacer(1, 3*mm))
                story.append(Paragraph(para, s_sec))
                continue
            # Convert inline markdown to reportlab XML
            para = re.sub(r"\*{2}(.+?)\*{2}", r"<b>\1</b>", para, flags=re.DOTALL)
            para = re.sub(r"\*(.+?)\*",        r"<i>\1</i>", para)
            # Escape ampersands that aren't already XML entities
            para = re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;)", "&amp;", para)
            story.append(Paragraph(para, s_body))

        # Embed chart after key sections
        if chart_figs and sec_num in SECTION_CHART_MAP:
            chart_idx = SECTION_CHART_MAP[sec_num]
            if chart_idx < len(chart_figs):
                c_title, c_fig = chart_figs[chart_idx]
                story.append(Spacer(1, 4*mm))
                add_chart(c_fig, c_title)

        i += 2

    # ── All remaining charts appended after final section ────────────────────
    placed = set(SECTION_CHART_MAP.values())
    remaining = [(t, f) for idx, (t, f) in enumerate(chart_figs or []) if idx not in placed]
    if remaining:
        story.append(hr(before=6, after=4))
        story.append(Paragraph("FINANCIAL CHARTS", s_sec))
        for c_title, c_fig in remaining:
            add_chart(c_fig, c_title)

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 1*cm))
    story.append(hr(thick=0.4, before=0, after=2))
    story.append(Paragraph(
        f"Compounder  \u00b7  {company} ({ticker})  \u00b7  {now}  \u00b7  For informational use only",
        s_footer))

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=lm, rightMargin=rm,
        topMargin=2.2*cm, bottomMargin=2.2*cm,
    )
    doc.build(story)
    buf.seek(0)
    return buf.read()

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

# Currency symbol map — ISO 4217 codes to symbols
_CCY_SYMBOLS = {
    "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "CNY": "¥",
    "INR": "₹", "CAD": "C$", "AUD": "A$", "CHF": "CHF ", "KRW": "₩",
    "HKD": "HK$", "SGD": "S$", "SEK": "SEK ", "NOK": "NOK ", "DKK": "DKK ",
    "BRL": "R$", "MXN": "MX$", "ZAR": "R ", "TWD": "NT$", "THB": "฿",
    "IDR": "Rp", "MYR": "RM", "ILS": "₪", "SAR": "SAR ", "AED": "AED ",
}

def ccy_symbol(currency_code):
    """Return the symbol for a currency code, falling back to the code itself."""
    if not currency_code:
        return "$"
    return _CCY_SYMBOLS.get(str(currency_code).upper(), str(currency_code).upper() + " ")

def fmt_currency(val, ccy="$"):
    """Render a monetary value with correct currency symbol and clean rounding."""
    try:
        v = float(val)
        if pd.isna(v): return "—"
        neg = v < 0
        v = abs(v)
        if v >= 1e12:   s = f"{ccy}{v/1e12:.1f}T"
        elif v >= 1e9:  s = f"{ccy}{v/1e9:.1f}B"
        elif v >= 1e6:  s = f"{ccy}{v/1e6:.0f}M"
        else:           s = f"{ccy}{v:,.0f}"
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

def fmt_eps(val, ccy="$"):
    try:
        v = float(val)
        if pd.isna(v): return "—"
        return f"{ccy}{v:.2f}"
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
        xaxis=dict(showgrid=False, showline=True, linecolor=C_BORDER,
                   tickfont=dict(size=10, color=C_TEXT3), zeroline=False),
        yaxis=dict(showgrid=True, gridcolor=C_BORDER2, gridwidth=1,
                   showline=True, linecolor=C_BORDER,
                   zeroline=False, tickfont=dict(size=10, color=C_TEXT3)),
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
        xaxis=dict(showgrid=False, showline=True, linecolor=C_BORDER,
                   tickfont=dict(size=10, color=C_TEXT3), zeroline=False),
        yaxis=dict(showgrid=True, gridcolor=C_BORDER2, gridwidth=1,
                   showline=True, linecolor=C_BORDER,
                   zeroline=False, tickfont=dict(size=10, color=C_TEXT3)),
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
        st.markdown('<div style="font-size:0.68rem;color:#999;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.5rem">Watchlist</div>', unsafe_allow_html=True)
        _wl_names = [s["Name"] for s in st.session_state.stocks_list]
        watchlist_choice = st.selectbox("", ["— Enter ticker below —"] + _wl_names, label_visibility="collapsed")

        st.markdown('<div style="font-size:0.68rem;color:#999;text-transform:uppercase;letter-spacing:0.08em;margin-top:1rem;margin-bottom:0.3rem">Any Ticker</div>', unsafe_allow_html=True)
        custom_ticker = st.text_input("", placeholder="e.g. NVDA, META, 7203.T", label_visibility="collapsed").strip().upper()

        # Resolve which ticker to use
        _wl_map = {s["Name"]: s["Ticker"] for s in st.session_state.stocks_list}
        if custom_ticker:
            selected_ticker  = custom_ticker
            selected_company = custom_ticker
        elif watchlist_choice != "— Enter ticker below —":
            selected_ticker  = _wl_map.get(watchlist_choice, watchlist_choice)
            selected_company = watchlist_choice
        else:
            selected_ticker  = None
            selected_company = None

    st.markdown("<br>" * 4, unsafe_allow_html=True)
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
    st.markdown('<div class="page-sub">Quality compounders — latest annual figures</div>', unsafe_allow_html=True)

    # ── Editable watchlist ────────────────────────────────────────────────────
    with st.expander("Edit Watchlist", expanded=False):
        edited_df = st.data_editor(
            pd.DataFrame(st.session_state.stocks_list),
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            column_config={
                "Name":   st.column_config.TextColumn("Company Name", width="medium"),
                "Ticker": st.column_config.TextColumn("Ticker",       width="small"),
            },
            key="stocks_editor",
        )
        if st.button("Apply Changes"):
            new_list = [
                {"Name": r["Name"], "Ticker": str(r["Ticker"]).strip().upper()}
                for _, r in edited_df.iterrows()
                if r["Ticker"] and str(r["Ticker"]).strip()
            ]
            if new_list != st.session_state.stocks_list:
                st.session_state.stocks_list = new_list
                st.cache_data.clear()
                st.rerun()

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
    for s in st.session_state.stocks_list:
        company, ticker = s["Name"], s["Ticker"]
        with st.spinner(f"Loading {company}..."):
            inc = fetch_fundamental("fundamental/income-statement", ticker)
            cf  = fetch_fundamental("fundamental/cash-flow",        ticker)
        if inc.empty:
            rows.append({"Company": company, "Ticker": ticker})
            continue

        # Try all known variants — API may return camelCase, snake_case, or Title Case
        rev_s    = safe(inc, "is_sales_revenue_turnover", "is_sales_and_services_revenues")
        gp_s     = safe(inc, "is_gross_profit")
        oi_s     = safe(inc, "ebit", "is_oper_income")
        ni_s     = safe(inc, "is_net_income", "is_ni_including_minority_int_ratio")
        gm_s     = safe(inc, "gross_margin")
        opm_s    = safe(inc, "oper_margin")
        npm_s    = safe(inc, "profit_margin")
        eps_s    = safe(inc, "diluted_eps", "eps")
        shares_s = safe(inc, "is_sh_for_diluted_eps", "is_avg_num_sh_for_eps")
        fcf_s    = safe(cf,  "cf_free_cash_flow") if not cf.empty else pd.Series(dtype=float)

        # Get reporting currency
        ccy_code = inc["currency"].iloc[-1] if "currency" in inc.columns and len(inc) > 0 else "USD"
        ccy = ccy_symbol(ccy_code)

        rev_cagr, rev_n = calc_cagr(rev_s)
        oi_cagr,  oi_n  = calc_cagr(oi_s)

        # Latest price for P/E and FCF yield
        prices = fetch_prices(ticker)
        latest_price = None
        if not prices.empty:
            close_col = next((c for c in ["adj_close", "adjusted_close", "close"] if c in prices.columns), None)
            if close_col:
                latest_price = float(prices[close_col].dropna().iloc[-1])

        # TTM EPS: sum of last 4 quarters
        inc_q = fetch_fundamental_quarterly("fundamental/income-statement", ticker)
        ttm_eps = None
        if not inc_q.empty:
            eps_q = safe(inc_q, "diluted_eps", "eps").dropna()
            if len(eps_q) >= 4:
                ttm_eps = float(eps_q.iloc[-4:].sum())
            elif len(eps_q) > 0:
                ttm_eps = float(eps_q.iloc[-len(eps_q):].sum())

        latest_shares = latest(shares_s)
        latest_fcf    = latest(fcf_s)

        def _pe():
            if latest_price and ttm_eps and ttm_eps != 0:
                return f"{latest_price / ttm_eps:.1f}x"
            return "—"

        def _fcf_yield():
            if latest_price and latest_shares and latest_shares > 0 and latest_fcf:
                mc = latest_price * latest_shares
                if mc > 0:
                    return f"{(latest_fcf / mc) * 100:.1f}%"
            return "—"

        rows.append({
            "Company":      company,
            "Ticker":       ticker,
            "Revenue":      fmt_currency(latest(rev_s), ccy),
            "Gross Profit": fmt_currency(latest(gp_s), ccy),
            "GP Margin":    fmt_pct(latest(gm_s)),
            "Op Profit":    fmt_currency(latest(oi_s), ccy),
            "Op Margin":    fmt_pct(latest(opm_s)),
            "Net Profit":   fmt_currency(latest(ni_s), ccy),
            "Net Margin":   fmt_pct(latest(npm_s)),
            "Rev CAGR":     fmt_cagr(rev_cagr, rev_n),
            "OI CAGR":      fmt_cagr(oi_cagr,  oi_n),
            "P/E":          _pe(),
            "FCF Yield":    _fcf_yield(),
            # keep raw for charts
            "_rev":  latest(rev_s),
            "_oi":   latest(oi_s),
            "_ni":   latest(ni_s),
            "_opm":  latest(opm_s),
            "_npm":  latest(npm_s),
            "_ccy":  ccy,
            "_ccy_code": str(ccy_code),
        })

    # Render HTML table
    header_cols = ["Company", "Ticker", "Revenue", "Gross Profit", "GP Margin",
                   "Op Profit", "Op Margin", "Net Profit", "Net Margin", "Rev CAGR", "OI CAGR", "P/E", "FCF Yield"]

    header_html = "".join(f'<span class="tbl-header">{h}</span>' for h in header_cols)
    st.markdown(f'''<div class="tbl-row tbl-header-row">{header_html}</div>''',
                unsafe_allow_html=True)

    for r in rows:
        def cell(key, cls="tbl-cell"):
            return f'<span class="{cls}">{r.get(key, "—")}</span>'

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
            {cagr_span(r.get("Rev CAGR", "—"))}
            {cagr_span(r.get("OI CAGR", "—"))}
            {cell("P/E")}
            {cell("FCF Yield")}
        </div>''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Use raw values stored in rows
    chart_names = [r["Company"] for r in rows if r.get("_rev")]
    chart_rev   = [r["_rev"]  for r in rows if r.get("_rev")]
    chart_opm   = [to_pct_list([r.get("_opm")])[0] if r.get("_opm") is not None else 0 for r in rows if r.get("_rev")]
    chart_npm   = [to_pct_list([r.get("_npm")])[0] if r.get("_npm") is not None else 0 for r in rows if r.get("_rev")]

    # Revenue chart — use each company's own currency for hover
    st.markdown('<span class="section-label">Revenue</span>', unsafe_allow_html=True)
    if chart_names:
        hover_texts = []
        for r in [r for r in rows if r.get("_rev")]:
            ccy = r.get("_ccy", "$")
            v   = r.get("_rev", 0)
            hover_texts.append(f"{ccy}{v/1e9:.1f}B")
        fig_rev = go.Figure(go.Bar(
            x=chart_names,
            y=[v/1e9 for v in chart_rev],
            marker_color=C_ACCENT,
            marker_line_width=0,
            text=hover_texts,
            hovertemplate="%{x}<br>%{text}<extra></extra>",
        ))
        fig_rev.update_layout(**CHART_BASE)
        fig_rev.update_layout(
            height=260, bargap=0.45, showlegend=False,
            yaxis=dict(showgrid=True, gridcolor=C_BORDER2, ticksuffix="B",
                       tickfont=dict(size=10, color=C_TEXT3),
                       zeroline=False, showline=True, linecolor=C_BORDER),
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
    if not selected_ticker:
        st.markdown('<div class="page-title">Company</div>', unsafe_allow_html=True)
        st.markdown('<div class="page-sub">Select a company from the watchlist or enter any ticker in the sidebar.</div>', unsafe_allow_html=True)
        st.stop()

    ticker   = selected_ticker
    company  = selected_company

    WATCHLIST_FE = {"RYAAY": 3, "CPRT": 7, "CSU.TO": 12, "FICO": 9,
                    "SPGI": 12, "MCO": 12, "ASML": 12}
    fe_month = WATCHLIST_FE.get(ticker, 12)

    with st.spinner(f"Loading {ticker}..."):
        inc = fetch_fundamental("fundamental/income-statement", ticker)
        bs  = fetch_fundamental("fundamental/balance-sheet",    ticker)
        cf  = fetch_fundamental("fundamental/cash-flow",        ticker)

    if inc.empty:
        st.error(f"No data returned for {ticker}. Check the ticker is correct and listed on a supported exchange.")
        st.stop()

    years    = inc["Date"].dt.year.astype(str).tolist() if "Date" in inc.columns else [str(i) for i in range(len(inc))]
    cf_years = cf["Date"].dt.year.astype(str).tolist()  if not cf.empty and "Date" in cf.columns else years
    n        = len(years)  # canonical length — all series must match this

    # Reporting currency for this company
    ccy_code = str(inc["currency"].iloc[-1]) if "currency" in inc.columns and len(inc) > 0 else "USD"
    ccy      = ccy_symbol(ccy_code)          # e.g. "₹", "€", "$"

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
    ar_s  = safe(bs, "bs_acct_note_rcv", "bs_accts_rec_excl_notes_rec") if n_bs else pd.Series(dtype=float)
    inv_s = safe(bs, "bs_inventories") if n_bs else pd.Series(dtype=float)
    ap_s  = safe(bs, "bs_acct_payable") if n_bs else pd.Series(dtype=float)
    ca_s  = safe(bs, "bs_cur_asset_report") if n_bs else pd.Series(dtype=float)
    cl_s  = safe(bs, "bs_cur_liab") if n_bs else pd.Series(dtype=float)

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

    # Header
    st.markdown(f'<div class="page-title">{company}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-sub">{ticker}</div>', unsafe_allow_html=True)

    # ── KPI row ────────────────────────────────────────────────────────────────
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    kpi_block(k1, "Revenue",       fmt_currency(rev_l, ccy),  yoy(rev_l, rev_p))
    kpi_block(k2, "Free Cash Flow",fmt_currency(fcf_l, ccy),  yoy(fcf_l, fcf_p))
    kpi_block(k3, "Gross Margin",  fmt_pct(gm_l))
    kpi_block(k4, "Operating Margin", fmt_pct(opm_l))
    kpi_block(k5, "Net Margin",    fmt_pct(npm_l))
    kpi_block(k6, "EPS",           fmt_eps(eps_l, ccy),  yoy(eps_l, eps_p))

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabs — no emojis ──────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Revenue", "Margins", "Cash Flow", "Valuation", "Working Capital", "Research Report"])

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
                fig_fcf = make_bar(cf_years, fcf_b, f"Free Cash Flow  ({ccy_code}, B)", height=260)
                fig_fcf.update_layout(yaxis=dict(showgrid=True, gridcolor=C_BORDER2,
                    tickprefix=ccy, ticksuffix="B", tickfont=dict(size=10, color=C_TEXT3),
                    zeroline=False, showline=True, linecolor=C_BORDER))
                st.plotly_chart(fig_fcf, use_container_width=True, config={"displayModeBar": False})
            else:
                st.markdown('<span style="color:#999;font-size:0.82rem">No free cash flow data</span>', unsafe_allow_html=True)
        with c2:
            if cfo_s.notna().any():
                cfo_b = [v/1e9 if v and not pd.isna(v) else None for v in cfo_s]
                fig_cfo = make_bar(cf_years, cfo_b, f"Operating Cash Flow  ({ccy_code}, B)", height=260, color="#555555")
                fig_cfo.update_layout(yaxis=dict(showgrid=True, gridcolor=C_BORDER2,
                    tickprefix=ccy, ticksuffix="B", tickfont=dict(size=10, color=C_TEXT3),
                    zeroline=False, showline=True, linecolor=C_BORDER))
                st.plotly_chart(fig_cfo, use_container_width=True, config={"displayModeBar": False})

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
            fig_px.update_layout(yaxis=dict(tickprefix=ccy, showgrid=True,
                                             gridcolor=C_BORDER2, tickfont=dict(size=10, color=C_TEXT3),
                                             zeroline=False, showline=True, linecolor=C_BORDER))
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
                    yaxis=dict(tickprefix=ccy, showgrid=True, gridcolor=C_BORDER2,
                               tickfont=dict(size=10, color=C_TEXT3), zeroline=False, showline=True, linecolor=C_BORDER))
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
            val_display = val_display.map(lambda v: fmt_multiple(v) if v else "—")
            st.dataframe(val_display, use_container_width=True)
        else:
            st.markdown('<span style="color:#999;font-size:0.82rem">Stock price required to calculate multiples. Add a Stock Price column to your Google Sheet.</span>', unsafe_allow_html=True)

    # TAB 5 — Working Capital
    with tab5:

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
        wc_kpi(w5, "NWC (Latest)",   fmt_currency(nwc_l, ccy))

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
                               f"Net Working Capital  ({ccy_code}, B)", height=260)
            fig_nwc.update_layout(yaxis=dict(tickprefix=ccy, ticksuffix="B", showgrid=True,
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
        wc_df["NWC"]            = [fmt_currency(v, ccy) for v in nwc_list]
        wc_display = pd.DataFrame({
            "Metric":         ["DSO", "Inventory Days", "DPO", "Cash Cycle", "NWC"],
            **{bs_years[i]: [
                fmt_days(dso_list[i]),
                fmt_days(inv_list[i]),
                fmt_days(dpo_list[i]),
                fmt_days(ccc_list[i]),
                fmt_currency(nwc_list[i], ccy),
            ] for i in range(len(bs_years))}
        }).set_index("Metric")
        st.dataframe(wc_display, use_container_width=True)

    # TAB 6 — Research Report
    with tab6:
        st.markdown('<div style="font-size:0.82rem;color:#555;margin-bottom:1.5rem;line-height:1.6">'
                    'Generates a comprehensive equity research report in the style of a Berkshire Hathaway analyst. '
                    'Uses the last 20 years of financial statements, last 4 earnings call transcripts, and web research. '
                    'Takes approximately 30–60 seconds.', unsafe_allow_html=True)

        generate_btn = st.button("Generate Report")

        if generate_btn:
            import re as _re_tab
            _has_suffix = bool(_re_tab.search(r"[.][A-Z]{1,4}$", ticker.upper()))

            with st.spinner("Fetching earnings transcripts..."):
                transcripts = fetch_last_4_transcripts(ticker)

            # Decide path and fetch filing once
            if _has_suffix:
                _filing_text, _form_preview, _date_preview = None, None, None
                spin_msg = f"{ticker} is non-US listed — generating report with Haiku + web search..."
            else:
                with st.spinner("Searching EDGAR for 10-K / 20-F..."):
                    _filing_text, _form_preview, _date_preview = fetch_10k_text(ticker)
                if _filing_text:
                    spin_msg = f"Found {_form_preview} ({_date_preview}) — generating report with NVIDIA..."
                else:
                    spin_msg = "No SEC filing found — generating report with Haiku + web search..."

            with st.spinner(spin_msg):
                financials_text = format_financials_for_prompt(inc, bs, cf, years)
                # Pass pre-fetched filing directly to avoid double EDGAR call
                if _filing_text:
                    report_text = generate_report_nvidia(
                        company, ticker, financials_text, transcripts,
                        _filing_text, _form_preview, _date_preview)
                    model_used, form_used = "nvidia", _form_preview
                else:
                    report_text = generate_report_haiku(
                        company, ticker, financials_text, transcripts)
                    model_used, form_used = "haiku", None

            # Show inline
            st.markdown("---")
            st.markdown(report_text)
            st.markdown("---")

            # Build PDF
            with st.spinner("Building PDF..."):
                chart_figs = []
                # Revenue chart
                rev_b = [v/1e9 if v and not pd.isna(v) else None for v in rev_s]
                if any(v for v in rev_b if v):
                    chart_figs.append(("Revenue (USD billions)", make_bar(years, rev_b, "Annual Revenue")))
                # FCF chart
                if fcf_s.notna().any():
                    fcf_b_pdf = [v/1e9 if v and not pd.isna(v) else None for v in fcf_s]
                    chart_figs.append(("Free Cash Flow (USD billions)", make_bar(years, fcf_b_pdf, "Free Cash Flow")))
                # Margins chart
                gm_pct_pdf  = to_pct_list(gm_s)
                opm_pct_pdf = to_pct_list(opm_s)
                npm_pct_pdf = to_pct_list(npm_s)
                if any(v for v in gm_pct_pdf if v):
                    chart_figs.append(("Profit Margins (%)",
                        make_line(years, [gm_pct_pdf, opm_pct_pdf, npm_pct_pdf],
                                  ["Gross", "Operating", "Net"], "Margins")))
                pdf_bytes = build_report_pdf(company, ticker, report_text, transcripts, chart_figs)

            st.download_button(
                label="Download PDF",
                data=pdf_bytes,
                file_name=f"{ticker}_research_report.pdf",
                mime="application/pdf",
            )

            # Show provenance
            meta_parts = []
            if model_used == "nvidia" and form_used:
                meta_parts.append(f"Model: NVIDIA Nemotron  ·  Filing: {form_used} ({_date_preview})")
            else:
                meta_parts.append("Model: Claude Haiku  ·  Source: web search + financial data")
            if transcripts:
                labels = ", ".join([f"Q{t['quarter']} {t['year']}" for t in transcripts])
                meta_parts.append(f"Transcripts: {labels}")
            st.markdown(
                f'<div style="font-size:0.72rem;color:#999;margin-top:0.5rem">{" &nbsp;·&nbsp; ".join(meta_parts)}</div>',
                unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#ccc;font-size:0.8rem">Click Generate Report to begin.</div>', unsafe_allow_html=True)

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

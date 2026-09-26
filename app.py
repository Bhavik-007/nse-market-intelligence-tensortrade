import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging

from datetime import datetime
from zoneinfo import ZoneInfo

from services.market_data import YahooMarketData


logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

IST = ZoneInfo("Asia/Kolkata")


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="Enterprise Market Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# ENTERPRISE UI
# ============================================================

st.markdown(
    """
    <style>
    :root {
        --emi-border: #e4e7ec;
        --emi-muted: #667085;
        --emi-text: #101828;
        --emi-soft: #f8fafc;
        --emi-blue: #175cd3;
        --emi-green: #039855;
    }

    .block-container {
        max-width: 1480px;
        padding-top: 1.25rem;
        padding-right: 2.2rem;
        padding-bottom: 2.5rem;
        padding-left: 2.2rem;
    }

    /* Header */
    .app-header {
        width: 100%;
        box-sizing: border-box;
        padding: 1.35rem 1.55rem 1.2rem 1.55rem;
        margin: 0 0 1.15rem 0;
        border: 1px solid var(--emi-border);
        border-radius: 16px;
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
    }

    .app-header-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
    }

    .app-title {
        color: var(--emi-text);
        font-size: clamp(1.75rem, 2.7vw, 2.35rem);
        line-height: 1.1;
        font-weight: 800;
        letter-spacing: -0.035em;
        margin: 0;
        padding: 0;
    }

    .app-badge {
        flex-shrink: 0;
        padding: 0.34rem 0.62rem;
        border: 1px solid #d0d5dd;
        border-radius: 999px;
        background: #ffffff;
        color: #475467;
        font-size: 0.68rem;
        font-weight: 750;
        letter-spacing: 0.07em;
        text-transform: uppercase;
    }

    .app-subtitle {
        color: var(--emi-muted);
        font-size: 0.86rem;
        line-height: 1.5;
        margin-top: 0.55rem;
    }

    /* Section headings */
    .section-label {
        font-size: 0.70rem;
        font-weight: 800;
        letter-spacing: 0.10em;
        text-transform: uppercase;
        color: #475467;
        margin: 0.15rem 0 0.65rem 0;
    }

    .section-divider {
        height: 1px;
        background: #eaecf0;
        margin: 1rem 0 0.85rem 0;
    }

    /* Status cards */
    .status-card {
        border: 1px solid var(--emi-border);
        border-radius: 14px;
        padding: 0.82rem 0.95rem;
        background: #ffffff;
        min-height: 70px;
        box-shadow: 0 1px 2px rgba(16, 24, 40, 0.03);
    }

    .status-label {
        font-size: 0.64rem;
        font-weight: 800;
        letter-spacing: 0.09em;
        color: var(--emi-muted);
        text-transform: uppercase;
    }

    .status-value {
        color: var(--emi-text);
        font-size: 0.88rem;
        font-weight: 700;
        margin-top: 0.34rem;
    }

    .status-dot {
        color: var(--emi-green);
        margin-right: 0.22rem;
    }

    /* Streamlit inputs */
    div[data-testid="stTextInput"] label,
    div[data-testid="stSelectbox"] label,
    div[data-testid="stNumberInput"] label {
        font-size: 0.73rem;
        font-weight: 700;
        color: #344054;
    }

    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input {
        border-radius: 9px;
    }

    div[data-baseweb="select"] > div {
        border-radius: 9px;
    }

    /* KPI cards */
    div[data-testid="stMetric"] {
        border: 1px solid var(--emi-border);
        border-radius: 14px;
        padding: 0.85rem 0.9rem 0.75rem 0.9rem;
        background: #ffffff;
        box-shadow: 0 1px 2px rgba(16, 24, 40, 0.03);
        min-height: 100px;
    }

    div[data-testid="stMetricLabel"] {
        color: #667085;
        font-size: 0.72rem;
        font-weight: 650;
    }

    div[data-testid="stMetricValue"] {
        color: #101828;
        font-size: 1.55rem;
        font-weight: 750;
        letter-spacing: -0.025em;
    }

    div[data-testid="stMetricDelta"] {
        font-size: 0.72rem;
        font-weight: 650;
    }

    /* Data and expanders */
    div[data-testid="stDataFrame"] {
        border: 1px solid var(--emi-border);
        border-radius: 12px;
        overflow: hidden;
    }

    div[data-testid="stExpander"] {
        border: 1px solid var(--emi-border);
        border-radius: 12px;
        background: #ffffff;
    }

    /* Buttons */
    div.stDownloadButton > button {
        width: 100%;
        border-radius: 9px;
        font-weight: 700;
    }

    /* Instrument identity / freshness */
    .instrument-strip {
        border: 1px solid var(--emi-border);
        border-radius: 14px;
        padding: 0.85rem 1rem;
        background: #ffffff;
        margin: 0.55rem 0 0.85rem 0;
        box-shadow: 0 1px 2px rgba(16, 24, 40, 0.03);
    }
    .instrument-name { color: var(--emi-text); font-size: 1.05rem; font-weight: 800; }
    .instrument-meta { color: var(--emi-muted); font-size: 0.76rem; margin-top: 0.28rem; }
    .freshness { color: #344054; font-size: 0.74rem; font-weight: 700; text-align: right; }
    .trend-pill {
        display: inline-block; padding: 0.22rem 0.55rem; border-radius: 999px;
        font-size: 0.68rem; font-weight: 800; letter-spacing: 0.05em;
        text-transform: uppercase; border: 1px solid #d0d5dd;
    }
    .trend-pill.bullish { background: #ecfdf3; color: #027a48; border-color: #abefc6; }
    .trend-pill.bearish { background: #fef3f2; color: #b42318; border-color: #fecdca; }
    .trend-pill.neutral { background: #f9fafb; color: #475467; }

    /* Chart spacing */
    div[data-testid="stPlotlyChart"] {
        border: 1px solid var(--emi-border);
        border-radius: 14px;
        padding: 0.25rem;
        background: #ffffff;
    }

    /* Reduce excessive Streamlit vertical gaps */
    div[data-testid="stVerticalBlock"] > div:has(> div.stMarkdown) {
        margin-bottom: 0.1rem;
    }

    @media (max-width: 900px) {
        .app-header-top {
            align-items: flex-start;
            flex-direction: column;
        }

        .app-badge {
            align-self: flex-start;
        }

        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }
    
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="app-header">
        <div class="app-header-top">
            <div class="app-title">Enterprise Market Intelligence</div>
            <div class="app-badge">Research • No Execution</div>
        </div>
        <div class="app-subtitle">
            Global Yahoo Finance market data&nbsp;&nbsp;•&nbsp;&nbsp;
            Streamlit analytics&nbsp;&nbsp;•&nbsp;&nbsp;
            TensorTrade-ready OHLCV
            <strong>(Open, High, Low, Close, Volume)</strong>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SERVICE
# ============================================================

# ============================================================

@st.cache_resource
def get_market_service():
    return YahooMarketData()


try:
    market = get_market_service()
except Exception as exc:
    logger.exception("BLOCK FAILED — Market Service")
    st.stop()


# ============================================================
# TOP STATUS
# ============================================================

status_col1, status_col2, status_col3 = st.columns(3)

with status_col1:
    st.markdown(
        """<div class="status-card">
        <div class="status-label">Data Source</div>
        <div class="status-value"><span class="status-dot">●</span>Yahoo Finance</div>
        </div>""",
        unsafe_allow_html=True,
    )

with status_col2:
    st.markdown(
        """<div class="status-card">
        <div class="status-label">Execution</div>
        <div class="status-value"><span class="status-dot">●</span>Research Mode — Disabled</div>
        </div>""",
        unsafe_allow_html=True,
    )

with status_col3:
    st.markdown(
        """<div class="status-card">
        <div class="status-label">Data Model</div>
        <div class="status-value"><span class="status-dot">●</span>OHLCV Ready</div>
        </div>""",
        unsafe_allow_html=True,
    )


# ============================================================
# CONTROLS
# ============================================================

try:
    st.markdown(
        '<div class="section-divider"></div><div class="section-label">Instrument & Analysis Controls</div>',
        unsafe_allow_html=True,
    )

    # One input only: enter a company name or NSE ticker.
    # The backend resolves it to the Yahoo Finance .NS ticker.
    search_col, interval_col, period_col = st.columns([3.2, 1.0, 1.0])

    with search_col:
        search_query = st.text_input(
            "Company / Ticker Search",
            value="",
            placeholder="Enter company name or NSE ticker — e.g. TCS, Tata Consultancy Services, Reliance, BEL",
            type="search",
            key="company_ticker_search_v4",
            help="Enter an NSE company name or ticker. The application resolves it automatically and loads Yahoo Finance OHLCV data.",
        )

    with interval_col:
        interval = st.selectbox(
            "Interval",
            ["1m", "5m", "15m", "30m", "60m", "1h", "1d"],
            index=1,
        )

    with period_col:
        period = st.selectbox(
            "Period",
            ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y"],
            index=1,
        )

    analysis_col1, analysis_col2 = st.columns([1, 1])

    with analysis_col1:
        sma_fast = st.number_input(
            "Fast SMA",
            min_value=2,
            max_value=200,
            value=20,
            help="Shorter moving average used to show near-term trend.",
        )

    with analysis_col2:
        sma_slow = st.number_input(
            "Slow SMA",
            min_value=3,
            max_value=300,
            value=50,
            help="Longer moving average used to show broader trend.",
        )

    if sma_fast >= sma_slow:
        raise ValueError("Fast SMA must be smaller than Slow SMA.")

    query = search_query.strip()
    if not query:
        st.info("Enter an NSE company name or ticker above to load market data.")
        st.stop()

    # Resolve the user's input directly. There is intentionally no second
    # dropdown and no dependency on the NSE CSV for normal ticker searches.
    try:
        resolution = market.resolve_ticker(query)
        if not resolution.success:
            raise ValueError(resolution.error or "Unable to resolve company/ticker.")

        ticker = str(resolution.context.get("ticker") or "").strip().upper()
        if not ticker:
            raise ValueError("Ticker resolution returned an empty ticker.")

        company_name = resolution.context.get("company_name") or query
        instrument_label = f"{company_name} ({ticker})"

    except Exception:
        logger.exception("BLOCK FAILED — Company/Ticker Resolution")
        st.stop()

except Exception:
    # Backend-only logging. Keep the front end clean.
    logger.exception("BLOCK FAILED — Instrument & Analysis Controls")
    st.stop()


# ============================================================
# LOAD MARKET DATA
# ============================================================

try:
    with st.spinner(
        f"Loading {instrument_label} ({ticker}) market data..."
    ):
        result = market.get_history(
            ticker=ticker,
            period=period,
            interval=interval,
        )

    if not result.success:
        raise RuntimeError(result.error or "Yahoo Finance market-data request failed.")

    df = result.data

    if df is None or df.empty:
        raise ValueError(
            "Yahoo Finance returned no market data for this instrument/period/interval."
        )

    currency_codes = {
        "USD": "$",
        "INR": "₹",
        "GBP": "£",
        "EUR": "€",
        "JPY": "¥",
        "CNY": "¥",
        "HKD": "HK$",
        "SGD": "S$",
        "AUD": "A$",
        "CAD": "C$",
    }

    currency_code = result.context.get("currency") or ""
    currency_symbol = currency_codes.get(currency_code, "")
    price_prefix = f"{currency_symbol}" if currency_symbol else ""


except Exception as exc:
    logger.exception("BLOCK FAILED — Market Data")
    st.stop()

# ============================================================
# NORMALIZE
# ============================================================

try:
    df = market.normalize_ohlcv(df)

    if df is None or df.empty:
        raise ValueError("OHLCV normalization produced no rows.")

    required_ohlcv = {"timestamp", "open", "high", "low", "close", "volume"}
    missing_columns = required_ohlcv.difference(df.columns)

    if missing_columns:
        raise ValueError(
            f"Normalized OHLCV is missing columns: {sorted(missing_columns)}"
        )


except Exception as exc:
    logger.exception("BLOCK FAILED — OHLCV Normalization")
    st.stop()

# ============================================================
# INDICATORS
# ============================================================

try:
    indicator_result = market.add_indicators(
        df,
        fast_window=sma_fast,
        slow_window=sma_slow,
    )

    if not indicator_result.success:
        raise RuntimeError(
            indicator_result.error or "Indicator calculation failed."
        )

    df = indicator_result.data

    if df is None or df.empty:
        raise ValueError("Indicator calculation returned no rows.")


except Exception as exc:
    logger.exception("BLOCK FAILED — Technical Indicators")
    st.stop()

# ============================================================
# KPI
# ============================================================

try:
    latest = df.iloc[-1]

    last_close = float(latest["close"])
    first_close = float(df.iloc[0]["close"]) if len(df) else last_close
    change = last_close - first_close
    change_pct = change / first_close * 100 if first_close else 0

    period_high = float(df["high"].max())
    period_low = float(df["low"].min())
    latest_volume = float(latest["volume"])

    fast_sma = float(latest["sma_fast"]) if pd.notna(latest["sma_fast"]) else float("nan")
    slow_sma = float(latest["sma_slow"]) if pd.notna(latest["sma_slow"]) else float("nan")
    if pd.notna(fast_sma) and pd.notna(slow_sma):
        trend = "Bullish" if fast_sma > slow_sma else "Bearish" if fast_sma < slow_sma else "Neutral"
    else:
        trend = "Neutral"
    trend_class = trend.lower()

    exchange = result.context.get("exchange") or "NSE"
    currency = currency_code or "N/A"
    instrument_type = result.context.get("instrument_type") or "Equity"
    latest_timestamp = latest["timestamp"]

    st.markdown(
        f"""<div class="instrument-strip">
            <div style="display:flex;justify-content:space-between;gap:1rem;align-items:center;">
                <div>
                    <div class="instrument-name">{instrument_label}</div>
                    <div class="instrument-meta">{exchange} &nbsp;•&nbsp; {ticker} &nbsp;•&nbsp; {currency} &nbsp;•&nbsp; {instrument_type} &nbsp;•&nbsp; {interval} candles &nbsp;•&nbsp; {period} history</div>
                </div>
                <div class="freshness">Latest candle<br>{latest_timestamp}</div>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Last Price", f"{price_prefix}{last_close:,.2f}")
    k2.metric("Period Change", f"{change_pct:+.2f}%", f"{price_prefix}{change:+,.2f}")
    k3.metric("Period High", f"{price_prefix}{period_high:,.2f}")
    k4.metric("Period Low", f"{price_prefix}{period_low:,.2f}")
    k5.metric("Latest Volume", f"{latest_volume:,.0f}")
    with k6:
        st.metric("Data Rows", f"{len(df):,}")
        st.markdown(f'<span class="trend-pill {trend_class}">Trend: {trend}</span>', unsafe_allow_html=True)

    sma1, sma2 = st.columns(2)
    sma1.caption(f"Fast SMA {sma_fast}: {price_prefix}{fast_sma:,.2f}" if pd.notna(fast_sma) else f"Fast SMA {sma_fast}: N/A")
    sma2.caption(f"Slow SMA {sma_slow}: {price_prefix}{slow_sma:,.2f}" if pd.notna(slow_sma) else f"Slow SMA {sma_slow}: N/A")

except Exception as exc:
    logger.exception("BLOCK FAILED — Market KPIs")
    st.stop()

# ============================================================
# CHART
# ============================================================

try:
    st.divider()
    st.subheader(f"{instrument_label} — Price, Trend & Volume")

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05,
        row_heights=[0.78, 0.22],
    )

    fig.add_trace(
        go.Candlestick(
            x=df["timestamp"], open=df["open"], high=df["high"],
            low=df["low"], close=df["close"], name="OHLCV Price",
        ), row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(x=df["timestamp"], y=df["sma_fast"], mode="lines",
                   name=f"SMA {sma_fast}"), row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(x=df["timestamp"], y=df["sma_slow"], mode="lines",
                   name=f"SMA {sma_slow}"), row=1, col=1,
    )
    fig.add_trace(
        go.Bar(x=df["timestamp"], y=df["volume"], name="Volume", opacity=0.55),
        row=2, col=1,
    )

    fig.update_layout(
        template="plotly_white", height=650, hovermode="x unified",
        xaxis_rangeslider_visible=False, paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff", margin=dict(l=12, r=12, t=72, b=18),
        font=dict(family="Inter, Segoe UI, Arial, sans-serif", size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.015,
                    xanchor="center", x=0.5, bgcolor="rgba(255,255,255,0.90)",
                    bordercolor="#EAECF0", borderwidth=1, font=dict(size=11)),
    )
    fig.update_xaxes(showgrid=False, showline=True, linecolor="#EAECF0", tickfont=dict(size=10))
    fig.update_yaxes(showgrid=True, gridcolor="#F2F4F7", zeroline=False, tickfont=dict(size=10), row=1, col=1)
    fig.update_yaxes(showgrid=False, zeroline=False, tickfont=dict(size=9), row=2, col=1)
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)

    st.plotly_chart(fig, use_container_width=True)

except Exception as exc:
    logger.exception("BLOCK FAILED — Price Chart")

# ============================================================
# DATA + TENSORTRADE
# ============================================================

try:
    data_col, tt_col = st.columns([2, 1])

    with data_col:
        st.subheader("Market Data")

        display_columns = [
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "sma_fast",
            "sma_slow",
        ]

        st.dataframe(
            df[display_columns].tail(100),
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "Download OHLCV + Indicators",
            df[display_columns].to_csv(index=False).encode("utf-8"),
            file_name=f"{ticker}_ohlcv_indicators.csv",
            mime="text/csv",
            use_container_width=True,
        )


    with tt_col:
        st.subheader("TensorTrade-ready OHLCV")

        tt_df = market.tensortrade_ohlcv(df)

        if tt_df is None or tt_df.empty:
            raise ValueError("TensorTrade OHLCV conversion returned no rows.")

        st.caption("Standardized schema • Open • High • Low • Close • Volume")

        st.code(
            """
timestamp
open
high
low
close
volume
            """.strip()
        )

        st.download_button(
            "Download TensorTrade OHLCV",
            tt_df.to_csv(index=False).encode("utf-8"),
            file_name=f"{ticker}_tensortrade_ohlcv.csv",
            mime="text/csv",
            use_container_width=True,
        )


except Exception as exc:
    logger.exception("BLOCK FAILED — Market Data & TensorTrade")

# ============================================================
# DATA QUALITY
# ============================================================

try:
    with st.expander(
        "Data Quality & Diagnostics",
        expanded=False,
    ):
        q1, q2, q3, q4 = st.columns(4)

        q1.metric("Rows", len(df))
        q2.metric(
            "Missing Values",
            int(df.isna().sum().sum()),
        )
        q3.metric(
            "Duplicate Timestamps",
            int(df["timestamp"].duplicated().sum()),
        )
        q4.metric("Source", "Yahoo Finance")

        missing_total = int(df.isna().sum().sum())
        duplicate_total = int(df["timestamp"].duplicated().sum())
        required_ohlcv = ["timestamp", "open", "high", "low", "close", "volume"]
        ohlcv_complete = all(column in df.columns and df[column].notna().all() for column in required_ohlcv)
        quality_status = "PASS" if missing_total == 0 and duplicate_total == 0 and ohlcv_complete else "CHECK"
        st.caption(
            f"Data Quality: **{quality_status}**  •  OHLCV complete: **{'Yes' if ohlcv_complete else 'No'}**  •  Latest candle: **{latest_timestamp}**"
        )

        st.caption(
            f"Ticker: {ticker} | "
            f"Exchange: {result.context.get('exchange') or 'N/A'} | "
            f"Currency: {currency_code or 'N/A'} | "
            f"Type: {result.context.get('instrument_type') or 'N/A'}"
        )

        st.write("Latest timestamp:", latest["timestamp"])


except Exception as exc:
    logger.exception("BLOCK FAILED — Data Quality")

# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Research / paper-trading data application • "
    "No order execution • "
    f"Updated {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST')}"
)

# Enterprise Market Intelligence

## 1. Executive Overview

**Enterprise Market Intelligence** is a Streamlit-based market-data analytics application designed to provide a simple enterprise interface for researching listed-market instruments using Yahoo Finance data.

The application allows a user to:

- Enter a company name or ticker.
- Automatically resolve the instrument to a Yahoo Finance ticker.
- Retrieve OHLCV market data.
- Select market-data interval and historical period.
- Calculate configurable Simple Moving Averages (SMA).
- Visualize price movement through an interactive candlestick chart.
- Compare fast and slow SMA trends.
- Review market KPIs and data-quality diagnostics.
- Download enriched OHLCV data.
- Download TensorTrade-ready OHLCV data for downstream research and reinforcement-learning workflows.

The application is explicitly designed as a **research / analytics application** and does not perform order execution.

---

# 2. Business Purpose

The business objective is to provide a lightweight, reusable market-intelligence layer that converts raw market data into an analyst-friendly research view.

Instead of requiring users to manually:

1. Find a market ticker,
2. Obtain historical market data,
3. Clean OHLCV data,
4. Calculate technical indicators,
5. Build charts,
6. Validate data quality, and
7. Prepare datasets for ML / reinforcement-learning experiments,

the application combines these activities into a single workflow.

### Business value

The application provides:

- Faster market-data exploration.
- Standardized OHLCV data.
- Consistent technical-indicator calculations.
- Visual trend analysis.
- Basic data-quality validation.
- Downloadable analytical datasets.
- TensorTrade-compatible data preparation.
- A foundation for future AI/ML-based market research.

---

# 3. Current Functional Scope

## 3.1 Company / Ticker Search

The user provides either:

- Company name
- NSE ticker
- Yahoo Finance ticker

Examples:

```text
TCS
Tata Consultancy Services
RELIANCE
Reliance Industries
BEL
INFY
TCS.NS
```

The application resolves the input through the backend ticker-resolution service.

There is intentionally **one search input** and no secondary instrument-selection workflow.

---

## 3.2 Market Data

The application retrieves market data from:

**Yahoo Finance / yfinance**

The primary market-data structure is:

```text
Timestamp
Open
High
Low
Close
Volume
```

This is commonly referred to as **OHLCV**:

- Open
- High
- Low
- Close
- Volume

---

## 3.3 Interval Selection

Supported intervals in the current application include:

```text
1m
5m
15m
30m
60m
1h
1d
```

The selected interval controls the candle granularity.

Example:

```text
5m
```

means each candle represents approximately five minutes of market activity.

---

## 3.4 Historical Period

Supported historical periods include:

```text
1d
5d
1mo
3mo
6mo
1y
2y
```

The combination of interval + period determines the returned market-data dataset.

---

# 4. Technical Architecture

The application follows a layered architecture:

```text
                    ┌─────────────────────────────┐
                    │        Streamlit UI         │
                    │                             │
                    │ Company / Ticker Search     │
                    │ Interval / Period           │
                    │ SMA Parameters              │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │      Application Layer      │
                    │          app.py             │
                    │                             │
                    │ Validation                  │
                    │ Workflow orchestration      │
                    │ KPI calculation             │
                    │ Visualization               │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │      Market Data Layer      │
                    │ services/market_data.py     │
                    │                             │
                    │ Ticker Resolution            │
                    │ Yahoo Finance Retrieval      │
                    │ OHLCV Normalization          │
                    │ Indicator Calculation        │
                    │ TensorTrade Preparation      │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │       Yahoo Finance         │
                    │          / yfinance         │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │       OHLCV Market Data     │
                    └──────────────┬──────────────┘
                                   │
                  ┌────────────────┼────────────────┐
                  ▼                ▼                ▼
             Indicators        Chart/KPIs      TensorTrade
             SMA 20/50          Analytics       Dataset
```

---

# 5. Application Components

## 5.1 `app.py`

`app.py` is the main Streamlit application.

Its responsibilities include:

- Streamlit page configuration.
- Enterprise UI styling.
- Service initialization.
- User-input collection.
- Input validation.
- Company/ticker resolution orchestration.
- Market-data retrieval.
- OHLCV validation.
- KPI calculation.
- Technical-indicator display.
- Plotly visualization.
- Market-data table.
- TensorTrade download.
- Data-quality diagnostics.
- Backend exception logging.

The UI intentionally keeps backend exception details out of the front end.

---

# 6. Market Data Service

## `services/market_data.py`

This module isolates market-data logic from the Streamlit interface.

This separation is important because it prevents the UI layer from becoming tightly coupled to Yahoo Finance implementation details.

The service is responsible for:

```text
Ticker Resolution
       ↓
Market Data Retrieval
       ↓
OHLCV Normalization
       ↓
Indicator Calculation
       ↓
TensorTrade Transformation
```

This makes the application easier to extend later with another market-data provider.

---

# 7. Ticker Resolution

The application accepts human-friendly company input.

Conceptually:

```text
User Input
    ↓
Ticker Resolver
    ↓
Yahoo-compatible ticker
```

For NSE instruments, a typical Yahoo Finance ticker follows:

```text
<TICKER>.NS
```

Examples:

```text
TCS       → TCS.NS
INFY      → INFY.NS
BEL       → BEL.NS
RELIANCE  → RELIANCE.NS
```

The important architectural principle is that the UI does not need to know how the ticker is resolved.

It simply passes:

```python
market.resolve_ticker(query)
```

to the service layer.

---

# 8. Market Data Retrieval

Once a ticker is resolved, the application calls:

```python
market.get_history(
    ticker=ticker,
    period=period,
    interval=interval,
)
```

The returned result contains:

```text
DataFrame
+
Context / metadata
```

The application verifies that:

- The request succeeded.
- Data exists.
- The returned DataFrame is not empty.

This prevents downstream chart and indicator processing from operating on invalid datasets.

---

# 9. OHLCV Data Model

The normalized dataset follows a standardized structure:

```text
timestamp
open
high
low
close
volume
```

### Open

Price at the beginning of the candle.

### High

Highest traded price during the candle.

### Low

Lowest traded price during the candle.

### Close

Price at the end of the candle.

### Volume

Quantity of traded units represented by the candle.

---

# 10. OHLCV Normalization

Raw provider data is not directly passed to all downstream components.

The application performs normalization through:

```python
market.normalize_ohlcv(df)
```

The normalized dataset is validated against the required schema:

```python
{
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
}
```

This creates a consistent analytical contract between the market-data layer and the UI/ML layers.

---

# 11. Simple Moving Average

## SMA Definition

**SMA = Simple Moving Average**

SMA calculates the arithmetic average of the latest N observations.

Formula:

```text
SMA(N) =
(
Price1 +
Price2 +
...
PriceN
)
/
N
```

The application currently exposes two configurable SMA windows:

```text
Fast SMA
Slow SMA
```

Default values:

```text
Fast SMA = 20
Slow SMA = 50
```

The indicator layer calculates these through:

```python
market.add_indicators(
    df,
    fast_window=sma_fast,
    slow_window=sma_slow,
)
```

---

# 12. SMA Trend Analysis

The application provides a descriptive trend state based on the relationship between the two SMA values.

Conceptually:

```text
Fast SMA > Slow SMA
        ↓
Bullish relationship
```

```text
Fast SMA < Slow SMA
        ↓
Bearish relationship
```

```text
Fast SMA ≈ Slow SMA
        ↓
Neutral relationship
```

This is an analytical classification and is **not a guarantee or prediction of future market performance**.

---

# 13. KPI Layer

The application presents key market statistics.

Current KPI concepts include:

### Last Price

Latest closing price in the retrieved dataset.

### Period Change

Difference between the latest close and the previous available close.

### Period Change %

```text
Change %
=
(Current Close - Previous Close)
/
Previous Close
× 100
```

### Period High

Highest high across the selected dataset.

### Period Low

Lowest low across the selected dataset.

### Latest Volume

Volume of the latest available candle.

### Data Rows

Number of normalized market-data records.

---

# 14. Visualization Architecture

Plotly is used for interactive visualization.

The primary chart contains:

```text
Candlestick Price
       +
Fast SMA
       +
Slow SMA
       +
Volume
```

Candlestick components:

```text
Open
High
Low
Close
```

The chart supports interactive exploration through Plotly's native browser-based capabilities.

---

# 15. Market Data Table

The application provides a tabular view of the latest market records.

Displayed analytical columns include:

```text
timestamp
open
high
low
close
volume
sma_fast
sma_slow
```

The application currently displays the latest 100 records in the UI.

This provides a compact analytical view without attempting to render the complete historical dataset simultaneously.

---

# 16. TensorTrade-Ready Dataset

The application prepares a standardized OHLCV dataset for downstream TensorTrade research.

The conceptual flow is:

```text
Yahoo Finance
      ↓
Raw Data
      ↓
Normalized OHLCV
      ↓
TensorTrade Transformation
      ↓
TensorTrade-ready CSV
```

The expected core schema is:

```text
timestamp
open
high
low
close
volume
```

This allows the market-data component to be separated from future reinforcement-learning environments.

---

# 17. Data Quality Framework

The application contains a dedicated Data Quality & Diagnostics section.

Current checks include:

### Row Count

Number of records returned.

### Missing Values

Total missing values across the DataFrame.

### Duplicate Timestamps

Number of duplicate timestamp records.

### OHLCV Completeness

Validation that required OHLCV columns exist.

### Source

Expected source:

```text
Yahoo Finance
```

### Exchange

Returned market/exchange metadata when available.

### Currency

Returned currency metadata when available.

### Instrument Type

Returned instrument classification when available.

### Latest Timestamp

Latest available market-data timestamp.

---

# 18. Error Handling

The application uses backend-only exception handling.

The design principle is:

```text
Exception
   ↓
logger.exception(...)
   ↓
Stop affected workflow
```

Detailed exception traces are not intentionally exposed as front-end technical messages.

This keeps the enterprise UI clean while still providing developers with diagnostic information in application logs.

---

# 19. Streamlit Resource Management

The market-data service is initialized using Streamlit resource caching:

```python
@st.cache_resource
def get_market_service():
    return YahooMarketData()
```

This avoids unnecessarily recreating the service object on every Streamlit rerun.

---

# 20. User Journey

Typical user workflow:

```text
1. Open application
        ↓
2. Enter company/ticker
        ↓
3. Select interval
        ↓
4. Select historical period
        ↓
5. Configure Fast/Slow SMA
        ↓
6. Application resolves ticker
        ↓
7. Yahoo Finance data retrieved
        ↓
8. OHLCV validated
        ↓
9. SMA indicators calculated
        ↓
10. KPIs displayed
        ↓
11. Candlestick + SMA + Volume chart
        ↓
12. Market data table
        ↓
13. Data-quality validation
        ↓
14. Download analytical / TensorTrade dataset
```

---

# 21. Business Use Cases

## 21.1 Market Research

Analysts can quickly inspect market instruments without manually collecting historical price data.

## 21.2 Technical Analysis

Users can examine:

- Price movement
- SMA relationships
- Period high/low
- Volume
- Historical OHLCV

## 21.3 Data Engineering

The application provides a standardized market-data pipeline that can serve as a source for:

- Data transformation
- Feature engineering
- Analytics
- Machine-learning experiments

## 21.4 AI / ML Research

The normalized OHLCV dataset can become an input to future:

- ML models
- Time-series models
- Reinforcement-learning environments
- TensorTrade experiments

## 21.5 Data Quality / Observability

The diagnostic layer provides a basic foundation for monitoring:

- Data completeness
- Duplicate records
- Latest-data freshness
- Schema consistency
- Source metadata

---

# 22. Technical Design Principles

The application follows these principles:

### Separation of concerns

UI logic remains in:

```text
app.py
```

Market-data logic remains in:

```text
services/market_data.py
```

### Provider abstraction

The Streamlit application interacts with:

```python
YahooMarketData
```

rather than embedding Yahoo Finance calls throughout the UI.

This makes future provider replacement easier.

### Standardized data contract

Downstream processing expects standardized OHLCV.

### Backend-only diagnostics

Technical exceptions are logged rather than exposed as raw application errors.

### No execution

The application is explicitly designed for research and analytics.

There is no order-placement workflow.

---

# 23. Project Structure

Recommended project structure:

```text
groww_yfinance_tensortrade_streamlit/
│
├── app.py
│
├── config.py
│
├── requirements.txt
│
├── README.md
│
├── .gitignore
│
├── .streamlit/
│   └── secrets.toml.example
│
└── services/
    ├── __init__.py
    └── market_data.py
```

---

# 24. Technology Stack

| Layer | Technology |
|---|---|
| Frontend / Application | Streamlit |
| Market Data | Yahoo Finance / yfinance |
| Programming Language | Python |
| Data Processing | Pandas |
| Numerical Processing | NumPy |
| Scientific Computing | SciPy |
| Visualization | Plotly |
| ML Foundation | Scikit-learn |
| HTTP | Requests |
| Date/Time | Python datetime / dateutil |
| RL Readiness | TensorTrade-compatible OHLCV |
| Data Format | CSV / Pandas DataFrame |

---

# 25. Dependencies

The application currently requires packages including:

```text
streamlit
yfinance
pandas
numpy
scipy
scikit-learn
plotly
requests
python-dateutil
```

TensorTrade is intentionally treated as a downstream research dependency rather than a mandatory runtime dependency for the core market-data application.

---

# 26. Installation

Create the environment:

```bat
python -m venv .venv
```

Activate:

```bat
.venv\Scripts\activate
```

Install dependencies:

```bat
pip install -r requirements.txt
```

Run:

```bat
streamlit run app.py
```

---

# 27. Operational Architecture

For local development:

```text
User Browser
     ↓
Streamlit
     ↓
Python Application
     ↓
yfinance
     ↓
Yahoo Finance
```

For future enterprise deployment:

```text
User
 ↓
Enterprise Web/App Gateway
 ↓
Streamlit Application
 ↓
Market Data Service
 ↓
Market Data Provider
 ↓
Normalized Data Layer
 ↓
Analytics / ML / RL
```

---

# 28. Future Enterprise Enhancements

The current application provides a strong foundation for future extensions.

Potential next-stage capabilities include:

## Data Layer

- Persistent historical market-data storage.
- Incremental data ingestion.
- Data caching.
- Data lineage.
- Provider fallback.
- Market-data validation pipelines.

## Analytics

- RSI
- MACD
- Bollinger Bands
- VWAP
- ATR
- Volatility
- Returns
- Drawdown
- Correlation

## Machine Learning

- Feature engineering.
- Time-series forecasting experiments.
- Classification models.
- Anomaly detection.
- Model evaluation.

## Reinforcement Learning

```text
OHLCV
 ↓
Features
 ↓
Trading Environment
 ↓
Agent
 ↓
Reward Function
 ↓
Policy Evaluation
```

## Observability

A future production version could monitor:

- API latency
- Data freshness
- Data availability
- Missing records
- Provider failures
- Pipeline execution time
- Model inference latency
- Model/data drift

---

# 29. Security Considerations

The current application is designed as a market-data research application and does not execute trades.

Recommended enterprise deployment controls include:

- Authentication.
- Role-based access control.
- Network restrictions.
- Secrets management.
- API rate-limit protection.
- Audit logging.
- Input validation.
- Dependency vulnerability scanning.
- Secure deployment configuration.

No sensitive credentials should be hard-coded in Python source files.

---

# 30. Important Data Considerations

Yahoo Finance is used as the market-data provider.

Therefore:

- Data availability depends on Yahoo Finance.
- Ticker coverage depends on Yahoo Finance.
- Historical/intraday availability can vary by instrument and interval.
- Market-data timestamps and metadata should be validated before analytical use.
- The application should not treat analytical indicators as guaranteed predictions.

For production financial systems, a licensed market-data provider and appropriate exchange/data licensing should be evaluated separately.

---

# 31. Current Limitations

The current application is primarily an analytics and research platform.

It does not currently provide:

- Order execution.
- Broker integration.
- Portfolio management.
- Position management.
- Risk management engine.
- Production trading strategy execution.
- Guaranteed real-time exchange feed.
- Institutional-grade tick-level market data.

---

# 32. Business-to-Technical Mapping

| Business Requirement | Technical Implementation |
|---|---|
| Search company | Company/ticker input + resolver |
| Retrieve market data | yfinance / Yahoo Finance |
| Standardize data | OHLCV normalization |
| Analyze trends | SMA 20 / SMA 50 |
| Visualize market | Plotly |
| Review KPIs | Streamlit metrics |
| Validate data | Data-quality diagnostics |
| Export data | CSV download |
| Prepare ML/RL data | TensorTrade-ready OHLCV |
| Avoid trading risk | Research-only architecture |
| Maintain clean UI | Backend-only exception logging |
| Support future providers | Market-data service abstraction |

---

# 33. End-to-End Data Flow

```text
                    USER
                     │
                     ▼
          Company / Ticker Input
                     │
                     ▼
              Ticker Resolver
                     │
                     ▼
                Yahoo Ticker
                     │
                     ▼
             Yahoo Finance API
                     │
                     ▼
                 Raw OHLCV
                     │
                     ▼
             OHLCV Normalizer
                     │
                     ▼
              Data Validation
                     │
                     ▼
            Technical Indicators
              ┌──────┴──────┐
              │             │
            SMA 20         SMA 50
              │             │
              └──────┬──────┘
                     ▼
              Analytics Layer
              ┌──────┼──────┐
              │      │      │
             KPI   Chart   Trend
              │      │      │
              └──────┼──────┘
                     ▼
              Market Data View
                     │
             ┌───────┴────────┐
             ▼                ▼
       Analytical CSV   TensorTrade CSV
```

---

# 34. Summary

Enterprise Market Intelligence provides a clean separation between:

```text
Market Data Acquisition
        ↓
Data Standardization
        ↓
Technical Analysis
        ↓
Visualization
        ↓
Data Quality
        ↓
ML / Reinforcement Learning Readiness
```

The application is intentionally designed as a **research-first market intelligence platform**.

Its current architecture provides a practical foundation for evolving from a Streamlit analytics application into a larger market-data, ML, reinforcement-learning, and observability platform without coupling the user interface directly to the underlying market-data implementation.

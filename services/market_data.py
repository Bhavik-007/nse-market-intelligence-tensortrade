from dataclasses import dataclass, field
from typing import Optional

import pandas as pd
import requests
import yfinance as yf


@dataclass
class MarketDataResult:
    success: bool
    data: Optional[pd.DataFrame] = None
    error: Optional[str] = None
    context: dict = field(default_factory=dict)


class YahooMarketData:
    """
    Yahoo Finance market-data service.

    Responsibilities:
        - Search Yahoo Finance instruments globally
        - Download historical OHLCV
        - Normalize Yahoo columns
        - Calculate indicators
        - Produce TensorTrade-ready OHLCV

    No broker authentication.
    No order execution.
    """

    # --------------------------------------------------------
    # NSE EQUITY UNIVERSE
    # --------------------------------------------------------

    def get_nse_equity_universe(self) -> MarketDataResult:
        """
        Load the current NSE equity-segment security list from NSE India.

        This is intentionally not hard-coded. NSE publishes the current
        equity security master as a CSV, so newly listed/removed securities
        are reflected when the list is refreshed.

        Yahoo Finance convention:
            NSE symbol ABC -> Yahoo ticker ABC.NS
        """
        url = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"

        try:
            response = requests.get(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 Chrome/153 Safari/537.36"
                    ),
                    "Accept": "text/csv,*/*",
                    "Referer": "https://www.nseindia.com/",
                },
                timeout=20,
            )
            response.raise_for_status()

            from io import StringIO

            nse_df = pd.read_csv(StringIO(response.text))

            # NSE's current equity file normally contains SYMBOL,
            # NAME OF COMPANY and SERIES. Resolve columns defensively
            # in case NSE changes capitalization/spacing.
            normalized_columns = {
                str(column).strip().upper(): column
                for column in nse_df.columns
            }

            symbol_col = normalized_columns.get("SYMBOL")
            company_col = normalized_columns.get("NAME OF COMPANY")
            series_col = normalized_columns.get("SERIES")

            if not symbol_col or not company_col:
                raise ValueError(
                    "NSE equity CSV does not contain the expected "
                    "SYMBOL / NAME OF COMPANY columns."
                )

            result = pd.DataFrame(
                {
                    "nse_symbol": (
                        nse_df[symbol_col]
                        .fillna("")
                        .astype(str)
                        .str.strip()
                    ),
                    "company_name": (
                        nse_df[company_col]
                        .fillna("")
                        .astype(str)
                        .str.strip()
                    ),
                    "series": (
                        nse_df[series_col]
                        .fillna("")
                        .astype(str)
                        .str.strip()
                        if series_col
                        else ""
                    ),
                }
            )

            # Keep normal equity securities. This excludes unrelated
            # rows/series while preserving the broad NSE equity universe.
            if series_col:
                result = result.loc[
                    result["series"].str.upper().eq("EQ")
                ]

            result = (
                result[
                    (result["nse_symbol"] != "")
                    & (result["company_name"] != "")
                ]
                .drop_duplicates(subset=["nse_symbol"])
                .sort_values(
                    ["company_name", "nse_symbol"],
                    kind="stable",
                )
                .reset_index(drop=True)
            )

            result["yahoo_symbol"] = (
                result["nse_symbol"].str.upper() + ".NS"
            )

            result["label"] = result.apply(
                lambda row: (
                    f"{row['company_name']} "
                    f"({row['nse_symbol']}.NS)"
                ),
                axis=1,
            )

            return MarketDataResult(
                success=True,
                data=result,
                context={
                    "source": "NSE India",
                    "source_url": url,
                    "rows": len(result),
                },
            )

        except Exception as exc:
            return MarketDataResult(
                success=False,
                error=f"{type(exc).__name__}: {exc}",
                context={
                    "source": "NSE India",
                    "source_url": url,
                },
            )

    # --------------------------------------------------------
    # RESOLVE COMPANY / TICKER
    # --------------------------------------------------------

    def resolve_ticker(self, query: str) -> MarketDataResult:
        """Resolve a user-entered NSE company name or ticker to a Yahoo ticker.

        Examples:
            TCS -> TCS.NS
            RELIANCE.NS -> RELIANCE.NS
            Tata Consultancy Services -> TCS.NS

        The UI does not need a second selector. The resolved Yahoo ticker is
        used directly to request OHLCV data.
        """
        query = (query or "").strip()
        if not query:
            return MarketDataResult(False, error="Company or ticker is empty.")

        clean = query.upper().replace(".NS", "").strip()

        # 1. If the user supplied a Yahoo NSE ticker, use it directly.
        if query.upper().endswith(".NS"):
            return MarketDataResult(
                success=True,
                context={
                    "ticker": query.upper(),
                    "company_name": query,
                    "resolver": "direct_ticker",
                },
            )

        # 2. Try Yahoo search first for company names and symbols.
        #    This keeps the common path independent of NSE website access.
        try:
            search_result = self.search_instruments(query, max_results=25)
            if search_result.success and search_result.data is not None:
                df = search_result.data.copy()
                if not df.empty:
                    df["symbol"] = df["symbol"].fillna("").astype(str).str.strip().str.upper()
                    df["name"] = df["name"].fillna("").astype(str).str.strip()

                    # Only consider NSE Yahoo symbols for this application.
                    nse = df[df["symbol"].str.endswith(".NS")].copy()

                    if not nse.empty:
                        exact_symbol = nse[nse["symbol"].eq(clean + ".NS")]
                        if not exact_symbol.empty:
                            row = exact_symbol.iloc[0]
                            return MarketDataResult(
                                True,
                                context={
                                    "ticker": row["symbol"],
                                    "company_name": row["name"],
                                    "resolver": "yahoo_exact_symbol",
                                },
                            )

                        name_match = nse[
                            nse["name"].str.contains(query, case=False, regex=False, na=False)
                        ]
                        if not name_match.empty:
                            row = name_match.iloc[0]
                            return MarketDataResult(
                                True,
                                context={
                                    "ticker": row["symbol"],
                                    "company_name": row["name"],
                                    "resolver": "yahoo_company_name",
                                },
                            )

                        # Yahoo may return a relevant NSE result without an
                        # exact name match. Use the first NSE equity result.
                        row = nse.iloc[0]
                        return MarketDataResult(
                            True,
                            context={
                                "ticker": row["symbol"],
                                "company_name": row["name"],
                                "resolver": "yahoo_nse_result",
                            },
                        )
        except Exception:
            logger = getattr(yf, "logger", None)
            if logger:
                try:
                    logger.exception("Ticker resolution via Yahoo failed for %s", query)
                except Exception:
                    pass

        # 3. Use the official NSE security master for company-name lookup.
        try:
            nse_result = self.get_nse_equity_universe()
            if nse_result.success and nse_result.data is not None:
                nse_df = nse_result.data
                if not nse_df.empty:
                    exact = nse_df[
                        nse_df["nse_symbol"].astype(str).str.upper().eq(clean)
                    ]
                    if not exact.empty:
                        row = exact.iloc[0]
                        return MarketDataResult(
                            True,
                            context={
                                "ticker": row["yahoo_symbol"],
                                "company_name": row["company_name"],
                                "resolver": "nse_exact_symbol",
                            },
                        )

                    name_match = nse_df[
                        nse_df["company_name"].astype(str).str.contains(
                            query, case=False, regex=False, na=False
                        )
                    ]
                    if not name_match.empty:
                        row = name_match.iloc[0]
                        return MarketDataResult(
                            True,
                            context={
                                "ticker": row["yahoo_symbol"],
                                "company_name": row["company_name"],
                                "resolver": "nse_company_name",
                            },
                        )
        except Exception:
            pass

        # 4. Final symbol fallback. This guarantees simple inputs such as
        # TCS, INFY, BEL, SUZLON, RELIANCE resolve without any search API.
        if clean.replace(".", "").replace("-", "").isalnum() and " " not in clean:
            return MarketDataResult(
                True,
                context={
                    "ticker": clean + ".NS",
                    "company_name": query,
                    "resolver": "direct_nse_symbol_fallback",
                },
            )

        return MarketDataResult(
            False,
            error=f"Could not resolve '{query}' to an NSE Yahoo Finance ticker.",
            context={"query": query},
        )

    # --------------------------------------------------------
    # SEARCH INSTRUMENTS
    # --------------------------------------------------------

    def search_instruments(
        self,
        query: str,
        max_results: int = 12,
    ) -> MarketDataResult:
        """Search Yahoo Finance for stocks and other instruments."""

        try:
            query = (query or "").strip()

            if not query:
                return MarketDataResult(
                    success=True,
                    data=pd.DataFrame(),
                    context={"query": query, "rows": 0},
                )

            search = yf.Search(
                query,
                max_results=max_results,
            )

            quotes = search.quotes or []
            rows = []

            for quote in quotes:
                quote_type = str(
                    quote.get("quoteType")
                    or quote.get("typeDisp")
                    or ""
                ).upper()

                # Keep the picker focused on tradable/common market
                # instruments while still allowing global symbols.
                if quote_type and quote_type not in {
                    "EQUITY",
                    "ETF",
                    "MUTUALFUND",
                    "INDEX",
                    "CRYPTOCURRENCY",
                    "FUTURE",
                    "CURRENCY",
                }:
                    continue

                symbol = quote.get("symbol")
                if not symbol:
                    continue

                rows.append({
                    "symbol": symbol,
                    "name": quote.get("longname")
                    or quote.get("shortname")
                    or symbol,
                    "exchange": quote.get("exchange")
                    or quote.get("exchDisp")
                    or "",
                    "type": quote_type or "INSTRUMENT",
                })

            result = pd.DataFrame(
                rows,
                columns=["symbol", "name", "exchange", "type"],
            ).drop_duplicates(
                subset=["symbol"]
            )

            return MarketDataResult(
                success=True,
                data=result.reset_index(drop=True),
                context={
                    "query": query,
                    "rows": len(result),
                },
            )

        except Exception as exc:
            return MarketDataResult(
                success=False,
                error=f"{type(exc).__name__}: {exc}",
                context={
                    "query": query,
                },
            )

    # --------------------------------------------------------
    # GET HISTORY
    # --------------------------------------------------------

    def get_history(
        self,
        ticker: str,
        period: str = "5d",
        interval: str = "5m",
    ) -> MarketDataResult:
        """Fetch historical OHLCV with a resilient Yahoo fallback."""

        ticker = (ticker or "").strip().upper()
        primary_error = None

        # Yahoo's NSE ticker convention is SYMBOL.NS.
        if ticker and not ticker.endswith(".NS") and "=" not in ticker:
            ticker = f"{ticker}.NS"

        # ----------------------------------------------------
        # Attempt 1: Ticker.history (preferred for one symbol)
        # ----------------------------------------------------
        try:
            yf_ticker = yf.Ticker(ticker)
            data = yf_ticker.history(
                period=period,
                interval=interval,
                auto_adjust=False,
                actions=False,
                repair=True,
                timeout=20,
            )

            if data is not None and not data.empty:
                data = data.reset_index()
                return MarketDataResult(
                    success=True,
                    data=data,
                    context={
                        "ticker": ticker,
                        "period": period,
                        "interval": interval,
                        "rows": len(data),
                        "source": "Yahoo Finance",
                    },
                )

            primary_error = "Ticker.history returned no rows."

        except Exception as exc:
            primary_error = f"{type(exc).__name__}: {exc}"
            logger = getattr(yf, "logger", None)
            if logger:
                try:
                    logger.debug("Ticker.history failed for %s: %s", ticker, exc)
                except Exception:
                    pass

        # ----------------------------------------------------
        # Attempt 2: yf.download fallback
        # This is especially useful when Yahoo's chart endpoint
        # responds while the Ticker history path does not.
        # ----------------------------------------------------
        try:
            try:
                data = yf.download(
                    ticker,
                    period=period,
                    interval=interval,
                    auto_adjust=False,
                    actions=False,
                    progress=False,
                    repair=True,
                    timeout=20,
                    multi_level_index=False,
                )
            except TypeError:
                # Compatibility with older yfinance releases.
                data = yf.download(
                    ticker,
                    period=period,
                    interval=interval,
                    auto_adjust=False,
                    actions=False,
                    progress=False,
                    repair=True,
                    timeout=20,
                )

            if data is not None and not data.empty:
                data = data.reset_index()
                return MarketDataResult(
                    success=True,
                    data=data,
                    context={
                        "ticker": ticker,
                        "period": period,
                        "interval": interval,
                        "rows": len(data),
                        "source": "Yahoo Finance",
                        "fallback": "yf.download",
                    },
                )

            return MarketDataResult(
                success=False,
                error=(
                    f"Yahoo Finance returned no OHLCV rows for {ticker}. "
                    f"Primary attempt: {primary_error}"
                ),
                context={
                    "ticker": ticker,
                    "period": period,
                    "interval": interval,
                    "source": "Yahoo Finance",
                },
            )

        except Exception as exc:
            return MarketDataResult(
                success=False,
                error=(
                    f"Yahoo Finance request failed for {ticker}. "
                    f"Primary attempt: {primary_error}; "
                    f"Fallback: {type(exc).__name__}: {exc}"
                ),
                context={
                    "ticker": ticker,
                    "period": period,
                    "interval": interval,
                    "source": "Yahoo Finance",
                },
            )

    # --------------------------------------------------------
    # NORMALIZE OHLCV
    # --------------------------------------------------------

    def normalize_ohlcv(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        if df.empty:
            return pd.DataFrame()

        result = df.copy()

        # Yahoo can return Date or Datetime.
        timestamp_column = None

        for column in [
            "Datetime",
            "Date",
            "timestamp",
        ]:

            if column in result.columns:
                timestamp_column = column
                break

        if timestamp_column is None:

            raise ValueError(
                "No timestamp column found."
            )

        result = result.rename(
            columns={
                timestamp_column: "timestamp"
            }
        )

        required = [
            "timestamp",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
        ]

        missing = [
            column
            for column in required
            if column not in result.columns
        ]

        if missing:

            raise ValueError(
                f"Missing Yahoo columns: {missing}"
            )

        result = result.rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
        )

        result["timestamp"] = pd.to_datetime(
            result["timestamp"],
            errors="coerce",
        )

        numeric_columns = [
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]

        for column in numeric_columns:

            result[column] = pd.to_numeric(
                result[column],
                errors="coerce",
            )

        result = result.dropna(
            subset=[
                "timestamp",
                "open",
                "high",
                "low",
                "close",
            ]
        )

        result = (
            result
            .sort_values("timestamp")
            .drop_duplicates(
                subset=["timestamp"]
            )
            .reset_index(drop=True)
        )

        return result[
            [
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
            ]
        ]

    # --------------------------------------------------------
    # INDICATORS
    # --------------------------------------------------------

    def add_indicators(
        self,
        df: pd.DataFrame,
        fast_window: int = 20,
        slow_window: int = 50,
    ) -> MarketDataResult:

        try:

            result = df.copy()

            result["sma_fast"] = (
                result["close"]
                .rolling(
                    fast_window,
                    min_periods=1,
                )
                .mean()
            )

            result["sma_slow"] = (
                result["close"]
                .rolling(
                    slow_window,
                    min_periods=1,
                )
                .mean()
            )

            result["return"] = (
                result["close"]
                .pct_change()
            )

            result["volatility"] = (
                result["return"]
                .rolling(
                    20,
                    min_periods=2,
                )
                .std()
            )

            return MarketDataResult(
                success=True,
                data=result,
            )

        except Exception as exc:

            return MarketDataResult(
                success=False,
                error=(
                    f"{type(exc).__name__}: "
                    f"{exc}"
                ),
            )

    # --------------------------------------------------------
    # TENSORTRADE FORMAT
    # --------------------------------------------------------

    def tensortrade_ohlcv(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        columns = [
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]

        return (
            df[columns]
            .copy()
            .sort_values("timestamp")
            .reset_index(drop=True)
        )

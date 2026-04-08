"""
Unit tests for data.fetcher module.

Tests cover caching behavior, pre-IPO data handling, and error cases.
"""

import logging
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import yfinance as yf

from data.config import CACHE_DIR, WATCHLIST
from data.fetcher import fetch_ticker, fetch_all

# Sample OHLCV data for testing
SAMPLE_DATA = pd.DataFrame(
    {
        "Open": [100.0, 101.0, 102.0],
        "High": [105.0, 106.0, 107.0],
        "Low": [99.0, 100.0, 101.0],
        "Close": [104.0, 105.0, 106.0],
        "Volume": [1000000, 1100000, 1200000],
    },
    index=pd.date_range("2020-01-01", periods=3, freq="D"),
)


@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Clean up cache before and after each test."""
    # Ensure cache dir exists for tests that need it
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    yield
    # Clean up any parquet files created during tests
    for cache_file in CACHE_DIR.glob("*.parquet"):
        cache_file.unlink()


def test_fetch_all_creates_parquet_files():
    """
    GIVEN data/cache/ is empty
    WHEN fetch_all() is called
    THEN 15 Parquet files are written to data/cache/
    and yfinance.download() is called exactly once per ticker
    """
    # Ensure cache is empty
    for f in CACHE_DIR.glob("*.parquet"):
        f.unlink()

    mock_download = MagicMock(return_value=SAMPLE_DATA.copy())

    with patch.object(yf, "download", mock_download):
        results = fetch_all(start="2020-01-01", end="2020-01-10")

    # Verify we fetched all 15 tickers from the watchlist
    assert len(results) == len(WATCHLIST)
    assert set(results.keys()) == set(WATCHLIST)

    # Verify yf.download was called once per ticker
    assert mock_download.call_count == len(WATCHLIST)

    # Verify 15 parquet files exist in cache
    parquet_files = list(CACHE_DIR.glob("*.parquet"))
    assert len(parquet_files) == len(WATCHLIST)


def test_fetch_ticker_uses_cache_when_exists():
    """
    GIVEN data/cache/AAPL.parquet already exists
    WHEN fetch_ticker("AAPL") is called
    THEN returns the cached DataFrame without calling yfinance
    """
    # Create a cached parquet file
    cache_path = CACHE_DIR / "AAPL.parquet"
    SAMPLE_DATA.to_parquet(cache_path)

    mock_download = MagicMock(return_value=SAMPLE_DATA.copy())

    with patch.object(yf, "download", mock_download):
        df = fetch_ticker("AAPL", start="2020-01-01", end="2020-01-10")

    # Verify the result is from cache, not from yfinance
    pd.testing.assert_frame_equal(df, SAMPLE_DATA)
    mock_download.assert_not_called()


def test_fetch_ticker_pre_ipo_truncation_logs_warning(caplog):
    """
    GIVEN "META" requested with start="2000-01-01" (pre-IPO)
    WHEN fetch_ticker("META", start="2000-01-01") is called
    THEN returns data from META's actual IPO date onward
    and logs a WARNING about truncated range
    """
    # META IPO'd in 2012. Create sample data starting from 2012-05-18
    meta_data = SAMPLE_DATA.copy()
    meta_data.index = pd.date_range("2012-05-18", periods=3, freq="D")

    with patch.object(yf, "download", return_value=meta_data):
        with caplog.at_level(logging.WARNING):
            df = fetch_ticker("META", start="2000-01-01", end="2020-01-10")

    # Verify data is returned from actual start date (truncated)
    assert df.index.min().date() == datetime(2012, 5, 18).date()

    # Verify warning was logged about truncated range
    warning_messages = [record.message for record in caplog.records if record.levelname == "WARNING"]
    assert any("starts at" in msg and "META" in msg for msg in warning_messages)


def test_fetch_ticker_empty_dataframe_raises_value_error():
    """
    GIVEN yfinance returns an empty DataFrame
    WHEN fetch_ticker() processes the empty result
    THEN raises ValueError identifying the ticker and date range
    """
    with patch.object(yf, "download", return_value=pd.DataFrame()):
        with pytest.raises(ValueError) as exc_info:
            fetch_ticker("AAPL", start="2000-01-01", end="2020-01-01")

    error_msg = str(exc_info.value)
    assert "AAPL" in error_msg
    assert "2000-01-01" in error_msg
    assert "2020-01-01" in error_msg
    assert "returned no data" in error_msg


def test_fetch_ticker_caches_after_download():
    """
    Additional test: verify that after a cache miss, the data is cached.
    """
    # Ensure no cache exists
    cache_path = CACHE_DIR / "TEST.parquet"
    if cache_path.exists():
        cache_path.unlink()

    with patch.object(yf, "download", return_value=SAMPLE_DATA.copy()):
        df = fetch_ticker("TEST", start="2020-01-01", end="2020-01-10")

    # Verify cache file was created
    assert cache_path.exists()

    # Verify data matches
    cached_df = pd.read_parquet(cache_path)
    pd.testing.assert_frame_equal(df, cached_df)

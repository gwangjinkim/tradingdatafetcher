from __future__ import annotations
import os
import types
import pandas as pd
import tradingdatafetcher.main as cli
from tradingdatafetcher import core

PAGE_HTML = """
<html>
  <body>
    <div id="pair" data-pair-id="8860" data-sml-id="115"></div>
  </body>
</html>
"""

# Minimal HTML table that pandas.read_html can parse.
# Note: Date format aligns with the site's typical output; our cleaner will parse it.
AJAX_HTML = """
<table>
  <thead>
    <tr>
      <th>Date</th><th>Price</th><th>Open</th><th>High</th><th>Low</th><th>Change %</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>Jan 31, 2024</td><td>900.00</td><td>880.00</td><td>910.00</td><td>870.00</td><td>+1.11%</td></tr>
    <tr><td>Feb 29, 2024</td><td>910.00</td><td>900.00</td><td>920.00</td><td>890.00</td><td>+1.11%</td></tr>
  </tbody>
</table>
"""

class FakeResponse:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code
    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise RuntimeError(f"HTTP {self.status_code}")

class FakeSession:
    """A minimal drop-in for requests.Session used in core.SessionContext."""
    def __init__(self):
        self.headers = {}
        self.last_post = None
    def headers_update(self, mapping):
        self.headers.update(mapping)
    def get(self, url, timeout=30):
        # Return page HTML that includes data-pair-id and data-sml-id
        return FakeResponse(PAGE_HTML)
    def post(self, url, data=None, headers=None, timeout=60):
        self.last_post = (url, data, headers)
        return FakeResponse(AJAX_HTML)

def test_fetch_core_with_mocked_network(monkeypatch):
    # Monkeypatch requests.Session used by SessionContext to our FakeSession.
    monkeypatch.setattr(core.requests, "Session", FakeSession)

    ctx = core.SessionContext()
    res = core.InvestingComResource(
        page_url="https://www.investing.com/indices/arca-gold-miners-historical-data",
        header_text="ARCA Gold Miners Historical Data",
    )
    req = core.FetchRequest(interval=core.Monthly())

    df = core.fetch(ctx, res, req)

    # Basic shape and types
    assert isinstance(df, pd.DataFrame)
    assert {"Date", "Price", "Open", "High", "Low", "Change %"}.issubset(df.columns)
    assert pd.api.types.is_datetime64_any_dtype(df["Date"])
    # Sorted ascending by Date in cleaner
    assert df.iloc[0]["Date"] < df.iloc[-1]["Date"]

def test_cli_writes_output_csv(monkeypatch, tmp_path):
    # Monkeypatch network again for the CLI path
    monkeypatch.setattr(core.requests, "Session", FakeSession)

    out = tmp_path / "out.csv"
    # Call the CLI main with explicit arguments
    rc = cli.main([
        "--interval", "monthly",
        "--out", str(out),
        "--resource-url", "https://www.investing.com/indices/arca-gold-miners-historical-data",
        "--header", "ARCA Gold Miners Historical Data",
        "--start", "1900-01-01",
    ])
    assert rc == 0
    assert out.exists()

    # Read and validate a couple of values
    df = pd.read_csv(out)
    assert "Date" in df.columns
    assert len(df) >= 2

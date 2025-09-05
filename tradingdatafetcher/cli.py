from __future__ import annotations
import argparse
from datetime import date
import pandas as pd
from .core import (
    SessionContext,
    InvestingComResource,
    FetchRequest,
    Daily, Weekly, Monthly,
    fetch, save,
)

def _interval_from_str(s: str):
    s = s.lower().strip()
    if s == "daily": return Daily()
    if s == "weekly": return Weekly()
    if s == "monthly": return Monthly()
    raise ValueError("interval must be one of: daily, weekly, monthly")

def main(argv=None):
    p = argparse.ArgumentParser(
        prog="tradingdatafetcher",
        description="Fetch Investing.com historical data using pure multiple dispatch.",
    )
    p.add_argument("--interval", default="monthly", help="daily|weekly|monthly (default: monthly)")
    p.add_argument("--start", default="1900-01-01", help="YYYY-MM-DD (default: 1900-01-01)")
    p.add_argument("--end", default=None, help="YYYY-MM-DD (default: today)")
    p.add_argument("--out", default="out.csv", help="Output path (.csv or .parquet)")
    p.add_argument(
        "--resource-url",
        default="https://www.investing.com/indices/arca-gold-miners-historical-data",
        help="Investing.com historical-data page URL (default: ARCA Gold Miners index).",
    )
    p.add_argument(
        "--header",
        default="ARCA Gold Miners Historical Data",
        help="Header text sent to the AJAX endpoint (should match the page).",
    )
    args = p.parse_args(argv)

    start = date.fromisoformat(args.start)
    end = date.today() if args.end is None else date.fromisoformat(args.end)
    interval = _interval_from_str(args.interval)

    ctx = SessionContext()
    res = InvestingComResource(
        page_url=args.resource_url,
        header_text=args.header,
    )
    req = FetchRequest(start=start, end=end, interval=interval)

    df = fetch(ctx, res, req)
    save(df, args.out, req.interval)
    print(f"Saved {len(df)} rows → {args.out}")
    with pd.option_context("display.max_columns", None, "display.width", 120):
        print(df.tail())

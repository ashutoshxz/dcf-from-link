
from typing import Dict, Any
import pandas as pd
import yfinance as yf

def fetch_yf_bundle(ticker: str) -> Dict[str, Any]:
    """
    Pulls price, info, financial statements from yfinance.
    Returns: dict with 'info', 'price', 'financials', 'balance_sheet', 'cashflow'
    """
    tkr = yf.Ticker(ticker)
    info = tkr.info or {}
    price = None
    try:
        price = float(tkr.history(period="1d")["Close"].iloc[-1])
    except Exception:
        pass

    financials = tkr.financials or pd.DataFrame()
    balance_sheet = tkr.balance_sheet or pd.DataFrame()
    cashflow = tkr.cashflow or pd.DataFrame()

    return {
        "info": info,
        "price": price,
        "financials": financials,
        "balance_sheet": balance_sheet,
        "cashflow": cashflow,
    }

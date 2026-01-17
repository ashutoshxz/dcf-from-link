
# DCF From Link (India‑aware)

A CLI tool that converts a company link (e.g., Screener.in) or a ticker into a full **Discounted Cash Flow (DCF)** valuation with clean outputs:
- Markdown report
- Excel workbook
- JSON model state

**Data sources**:
- Identification from URL (no data scraping)
- Market & financials from Yahoo Finance via `yfinance`
- Defaults for Rf/ERP with easy overrides

> ⚠️ Educational use only. Not investment advice.

## Features
- FCFF DCF with 10‑year forecast, WACC via CAPM
- India‑aware display (₹ crores), lease & MI notes
- Banks/financials automatically guarded (switch to Residual Income suggested)
- Sensitivity tables: WACC ±200 bps, terminal g ±100 bps
- Clean artifacts in `./output/<ticker>/`

## Install
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt


import argparse
from pathlib import Path
from .pipeline import run_pipeline

def main():
    ap = argparse.ArgumentParser(description="Run a DCF valuation from a URL or ticker.")
    ap.add_argument("--url", type=str, help="Company URL (e.g., Screener.in company page)")
    ap.add_argument("--ticker", type=str, help="Yahoo-style ticker (e.g., TCS.NS)")
    ap.add_argument("--risk_free", type=float, default=0.07, help="Risk-free rate (decimal, default 0.07)")
    ap.add_argument("--erp", type=float, default=0.055, help="Equity risk premium (decimal, default 0.055)")
    ap.add_argument("--terminal_g", type=float, default=0.055, help="Terminal growth (decimal, default 0.055)")
    ap.add_argument("--years", type=int, default=10, help="Forecast years (default 10)")
    ap.add_argument("--output", type=str, default="output", help="Output folder (default ./output)")
    args = ap.parse_args()

    run_pipeline(
        url=args.url,
        ticker=args.ticker,
        risk_free=args.risk_free,
        erp=args.erp,
        terminal_g=args.terminal_g,
        years=args.years,
        out_dir=Path(args.output),
    )

if __name__ == "__main__":
    main()

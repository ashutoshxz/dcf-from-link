
import json
from pathlib import Path
from typing import Optional, Dict, Any
from .utils.logging_config import get_logger
from .data_providers.screener import resolve_identity_from_url
from .data_providers.market_yf import fetch_yf_bundle
from .model.dcf import DCFInputs, run_dcf
from .model.banks_guardrail import looks_like_financial
from .reports.markdown_report import write_markdown
from .reports.excel_writer import write_excel

log = get_logger("pipeline")

def run_pipeline(
    url: Optional[str],
    ticker: Optional[str],
    risk_free: float,
    erp: float,
    terminal_g: float,
    years: int,
    out_dir: Path,
) -> Dict[str, Any]:
    if not ticker and not url:
        raise ValueError("Provide either --url or --ticker")

    identity = resolve_identity_from_url(url) if url else None
    yf_ticker = ticker or (identity.ticker if identity and identity.ticker else None)
    if not yf_ticker:
        raise ValueError("Could not resolve ticker. Pass --ticker explicitly (e.g., TCS.NS)")

    log.info(f"Using ticker: {yf_ticker}")
    bundle = fetch_yf_bundle(yf_ticker)
    info = bundle["info"]

    # Guardrail for financials
    if looks_like_financial(info):
        msg = ("Detected financial sector (bank/NBFC/insurer). "
               "This template skips DCF and recommends Residual Income/Dividend Discount.")
        log.warning(msg)
        output_dir = out_dir / yf_ticker
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "report.md").write_text("# Model not run\n\n" + msg, encoding="utf-8")
        return {"skipped": True, "reason": msg}

    inputs = DCFInputs(
        ticker=yf_ticker,
        currency=info.get("currency", "INR") if info else "INR",
        risk_free=risk_free,
        erp=erp,
        terminal_g=terminal_g,
        years=years
    )
    outputs = run_dcf(bundle, inputs)

    model_state = {
        "summary": outputs.summary,
        "assumptions": outputs.assumptions,
        "forecast": outputs.forecast.to_dict(orient="list"),
        "ev": outputs.ev,
        "equity_value": outputs.equity_value,
        "value_per_share": outputs.value_per_share
    }

    output_dir = out_dir / yf_ticker
    output_dir.mkdir(parents=True, exist_ok=True)
    write_markdown(output_dir, model_state)
    write_excel(output_dir, outputs.forecast, outputs.assumptions, outputs.summary)
    (output_dir / "model.json").write_text(json.dumps(model_state, indent=2), encoding="utf-8")

    log.info(f"Outputs written to {output_dir}")
    return model_state

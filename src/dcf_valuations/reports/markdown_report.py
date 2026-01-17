
from pathlib import Path
from typing import Dict
from ..utils.units import to_crores

def format_crore(x: float) -> str:
    if x is None: return "NA"
    try:
        return f"₹{to_crores(float(x)):.2f} Cr"
    except Exception:
        return "NA"

def write_markdown(output_dir: Path, model: Dict):
    output_dir.mkdir(parents=True, exist_ok=True)
    s = model["summary"]
    a = model["assumptions"]

    md = []
    md.append(f"# DCF Valuation — {s.get('ticker','')}")
    md.append("")
    md.append("**Disclaimer:** Educational analysis only. Not investment advice.")
    md.append("")
    md.append("## Summary")
    md.append(f"- Intrinsic value / share: **{s.get('value_per_share'):.2f}**")
    md.append(f"- Current price: **{s.get('current_price')}**")
    if s.get("upside_pct") is not None:
        md.append(f"- Upside/(Downside): **{s.get('upside_pct'):.1f}%**")
    md.append(f"- WACC: **{a.get('wacc'):.2%}**, Terminal g: **{a.get('terminal_g'):.2%}**")
    md.append("")
    md.append("## Key Assumptions")
    md.append(f"- Beta: {a.get('beta')}, Rf: {a.get('risk_free'):.2%}, ERP: {a.get('erp'):.2%}, Size premium: {a.get('size_premium'):.2%}")
    md.append(f"- Cost of equity (Ke): {a.get('ke'):.2%}, Cost of debt (Kd): {a.get('kd'):.2%}, Tax: {a.get('tax_rate'):.2%}")
    md.append(f"- Weights: E={a.get('we'):.1%}, D={a.get('wd'):.1%}")
    md.append(f"- Net debt: {format_crore(a.get('net_debt'))}")
    md.append("")
    md.append("## Notes")
    md.append("- FCF proxied as Operating Cash Flow – CapEx due to data availability.")
    md.append("- If the company is a bank/NBFC/insurer, a Residual Income/Dividend model is more appropriate.")
    md.append("")
    (output_dir / "report.md").write_text("\n".join(md), encoding="utf-8")

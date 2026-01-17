
from typing import Dict

FINANCIAL_SECTOR_HINTS = {
    "bank", "nbfc", "insurance", "insurer", "broker", "asset management", "mutual fund"
}

def looks_like_financial(info: Dict) -> bool:
    sector = (info.get("sector") or "").lower()
    industry = (info.get("industry") or "").lower()
    cat = (info.get("category") or "").lower()
    joined = " ".join([sector, industry, cat])
    return any(h in joined for h in FINANCIAL_SECTOR_HINTS)

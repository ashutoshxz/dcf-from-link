
from dataclasses import dataclass
from typing import Optional

@dataclass
class CompanyIdentity:
    name: Optional[str]
    ticker: Optional[str]   # Yahoo-style ticker (e.g., TCS.NS)
    exchange: Optional[str] # "NSE" or "BSE" if known
    url: Optional[str]

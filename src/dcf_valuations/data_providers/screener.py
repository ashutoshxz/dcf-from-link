
import re
import requests
from bs4 import BeautifulSoup
from .base import CompanyIdentity

def resolve_identity_from_url(url: str) -> CompanyIdentity:
    """
    Parse Screener (or other) URL to get company name and a likely Yahoo-style ticker.
    We DO NOT scrape financial data. Only identity hints.
    """
    name, ticker, exch = None, None, None
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.find("title").get_text(strip=True) if soup.find("title") else None
        og_title = soup.find("meta", {"property": "og:title"})
        if og_title and og_title.get("content"):
            name = og_title["content"].split(" - ")[0].strip()
        elif title:
            name = title.split(" - ")[0].strip()

        # Heuristic: Screener URL often includes /company/<SYMBOL>/
        m = re.search(r"/company/([A-Z0-9\-]+)/", url.upper())
        if m:
            sym = m.group(1)
            # Guess Yahoo suffix: prefer NSE
            ticker = f"{sym}.NS"
            exch = "NSE"
    except Exception:
        pass

    return CompanyIdentity(name=name, ticker=ticker, exchange=exch, url=url)


from datetime import datetime, timezone

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")

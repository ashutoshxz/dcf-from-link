
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd

@dataclass
class DCFInputs:
    ticker: str
    currency: str
    risk_free: float = 0.07   # 7.0%
    erp: float = 0.055        # 5.5%
    terminal_g: float = 0.055 # 5.5% default India nominal
    years: int = 10
    tax_rate_fallback: float = 0.25
    size_premium: float = 0.0

@dataclass
class DCFOutputs:
    summary: Dict[str, Any]
    forecast: pd.DataFrame
    assumptions: Dict[str, Any]
    ev: float
    equity_value: float
    value_per_share: float

def _safe(series: pd.Series, key: str) -> float:
    for k in [key, key.upper(), key.lower()]:
        if k in series.index:
            v = series[k]
            if pd.notna(v):
                return float(v)
    return np.nan

def _estimate_tax_rate(financials: pd.DataFrame) -> float:
    try:
        df = financials
        if df.empty: raise ValueError()
        # Expect rows like 'Tax Provision' or 'Income Tax Expense', 'Pretax Income'
        row_tax = None
        for candidate in ["Tax Provision", "Income Tax Expense"]:
            if candidate in df.index:
                row_tax = df.loc[candidate]
                break
        row_pti = None
        for candidate in ["Pretax Income", "Ebt", "EBT"]:
            if candidate in df.index:
                row_pti = df.loc[candidate]
                break
        if row_tax is not None and row_pti is not None:
            rates = (row_tax / row_pti).replace([np.inf, -np.inf], np.nan)
            rates = rates[rates.between(0, 0.5, inclusive="both")]
            if not rates.empty:
                return float(rates.mean())
    except Exception:
        pass
    return 0.25

def _shares_out(info: Dict[str, Any]) -> float:
    # Prefer diluted shares if available; Yahoo sometimes has 'sharesOutstanding'
    for k in ["sharesOutstanding", "impliedSharesOutstanding", "floatShares"]:
        v = info.get(k)
        if v: return float(v)
    return np.nan

def _net_debt(info: Dict[str, Any], balance_sheet: pd.DataFrame) -> float:
    # Try from balance_sheet
    net_debt = np.nan
    try:
        if not balance_sheet.empty:
            cash = 0.0
            debt = 0.0
            for c in ["Cash And Cash Equivalents", "Cash", "Cash And Short Term Investments"]:
                if c in balance_sheet.index:
                    cash = float(balance_sheet.loc[c].iloc[0])
                    break
            for d in ["Total Debt", "Long Term Debt And Capital Lease Obligation", "Short Long Term Debt Total"]:
                if d in balance_sheet.index:
                    debt = float(balance_sheet.loc[d].iloc[0])
                    break
            if not np.isnan(cash) and not np.isnan(debt):
                net_debt = debt - cash
    except Exception:
        pass

    if np.isnan(net_debt):
        # fallback from info if present
        cash = float(info.get("totalCash", np.nan)) if info.get("totalCash") else np.nan
        debt = float(info.get("totalDebt", np.nan)) if info.get("totalDebt") else np.nan
        if not np.isnan(cash) and not np.isnan(debt):
            net_debt = debt - cash
    return net_debt

def _fcf_series(financials: pd.DataFrame, cashflow: pd.DataFrame) -> pd.Series:
    """
    Approximate unlevered FCF using Operating Cash Flow - CapEx as a practical proxy.
    """
    if cashflow.empty:
        return pd.Series(dtype=float)
    ocf = None
    for k in ["Operating Cash Flow", "Total Cash From Operating Activities"]:
        if k in cashflow.index:
            ocf = cashflow.loc[k]
            break
    capex = None
    for k in ["Capital Expenditures"]:
        if k in cashflow.index:
            capex = cashflow.loc[k]
            break
    if ocf is not None and capex is not None:
        return (ocf - (-capex.abs())) if (capex < 0).any() else (ocf - capex.abs())
    # fall back: if only financials present
    if not financials.empty and "Free Cash Flow" in financials.index:
        return financials.loc["Free Cash Flow"]
    return pd.Series(dtype=float)

def _historical_growth(series: pd.Series, years: int = 3) -> float:
    series = series.dropna().astype(float)
    if len(series) < 2:
        return 0.08
    first = float(series.iloc[-min(years, len(series))])
    last = float(series.iloc[-1])
    if first <= 0: return 0.08
    periods = min(years, len(series)) - 1
    return (last / first) ** (1 / max(1, periods)) - 1

def _cost_of_equity(beta: float, rf: float, erp: float, size_premium: float = 0.0) -> float:
    return rf + beta * erp + size_premium

def _cost_of_debt(info: Dict[str, Any], rf: float) -> float:
    # heuristic: rf + 2% if no better signal
    kd = rf + 0.02
    y = float(info.get("yield", 0.0))
    if y and y > 0:
        kd = max(rf + 0.01, y / 100.0)
    return kd

def run_dcf(yf_bundle: Dict[str, Any], inputs: DCFInputs) -> DCFOutputs:
    info = yf_bundle["info"]
    financials = yf_bundle["financials"]
    balance_sheet = yf_bundle["balance_sheet"]
    cashflow = yf_bundle["cashflow"]

    currency = info.get("currency", inputs.currency) if info else inputs.currency
    beta = float(info.get("beta", 1.0)) if info.get("beta") else 1.0
    shares = _shares_out(info)
    price = yf_bundle["price"]

    tax_rate = _estimate_tax_rate(financials) if not financials.empty else inputs.tax_rate_fallback
    kd = _cost_of_debt(info, inputs.risk_free)
    net_debt = _net_debt(info, balance_sheet)

    ke = _cost_of_equity(beta, inputs.risk_free, inputs.erp, inputs.size_premium)
    E = price * shares if (price and shares and not np.isnan(shares)) else np.nan
    D = max(net_debt, 0) if not np.isnan(net_debt) else np.nan
    V = np.nansum([x for x in [E, D] if not np.isnan(x)])
    we = (E / V) if (V and not np.isnan(V) and not np.isnan(E)) else 0.8
    wd = (D / V) if (V and not np.isnan(V) and not np.isnan(D)) else 0.2

    wacc = we * ke + wd * kd * (1 - tax_rate)

    # Build FCF forecast
    hist_fcf = _fcf_series(financials, cashflow)
    base_fcf = float(hist_fcf.dropna().iloc[-1]) if not hist_fcf.dropna().empty else np.nan
    growth = _historical_growth(hist_fcf, years=3) if not np.isnan(base_fcf) else 0.08

    years = inputs.years
    fcf_forecast = []
    last = base_fcf if not np.isnan(base_fcf) else (price * shares * 0.03 if price and shares else 1e9)
    g = growth
    for t in range(1, years + 1):
        # Fade growth linearly to terminal_g by year N
        g_t = g + (inputs.terminal_g - g) * (t / years)
        last = last * (1 + g_t)
        fcf_forecast.append(last)

    # PV of FCFs and terminal value (Gordon)
    disc = [(1 + wacc) ** t for t in range(1, years + 1)]
    pv_fcfs = [cf / df for cf, df in zip(fcf_forecast, disc)]
    tv = fcf_forecast[-1] * (1 + inputs.terminal_g) / max(1e-9, (wacc - inputs.terminal_g))
    pv_tv = tv / disc[-1]
    ev = float(np.sum(pv_fcfs) + pv_tv)

    equity_value = ev - (net_debt if not np.isnan(net_debt) else 0.0)
    vps = equity_value / shares if shares and not np.isnan(shares) and shares > 0 else np.nan

    # Assemble forecast frame
    df = pd.DataFrame({
        "Year": list(range(1, years + 1)),
        "FCF": fcf_forecast,
        "Discount Factor": disc,
        "PV(FCF)": pv_fcfs
    })

    assumptions = {
        "beta": beta,
        "risk_free": inputs.risk_free,
        "erp": inputs.erp,
        "size_premium": inputs.size_premium,
        "ke": ke,
        "kd": kd,
        "tax_rate": tax_rate,
        "we": we, "wd": wd,
        "wacc": wacc,
        "terminal_g": inputs.terminal_g,
        "base_fcf": base_fcf,
        "growth_start": growth,
        "shares_out": shares,
        "price": price,
        "currency": currency,
        "net_debt": net_debt,
    }

    summary = {
        "ticker": inputs.ticker,
        "value_per_share": vps,
        "current_price": price,
        "upside_pct": (vps / price - 1) * 100 if vps and price else None,
        "wacc": wacc,
        "terminal_g": inputs.terminal_g,
        "years": years,
    }

    return DCFOutputs(
        summary=summary,
        forecast=df,
        assumptions=assumptions,
        ev=ev,
        equity_value=equity_value,
        value_per_share=vps
    )

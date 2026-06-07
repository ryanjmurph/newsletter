# stockPrices.py

import yfinance as yf

# =========================================
# UNIVERSE
# =========================================

JSE_TOP40 = [
    "ABG.JO", "AGL.JO", "ANG.JO", "ANH.JO", "ARI.JO",
    "BHG.JO", "BID.JO", "BVT.JO", "BTI.JO", "CFR.JO",
    "CLS.JO", "CPI.JO", "DSY.JO", "EXX.JO", "FSR.JO",
    "GFI.JO", "GLN.JO", "GRT.JO", "HAR.JO", "IMP.JO",
    "INL.JO", "INP.JO", "KIO.JO", "MTN.JO", "NED.JO",
    "NPN.JO", "NRP.JO", "OMU.JO", "OUT.JO", "PRX.JO",
    "REM.JO", "SBK.JO", "SLM.JO", "SOL.JO", "SSW.JO",
    "VOD.JO", "WHL.JO"
]

INDICES = {
    "^J200.JO": "JSE Top 40",
    "^J203.JO": "JSE All Share",
}

COMMODITIES = {
    "GC=F":  "Gold",
    "SI=F":  "Silver",
    "PL=F":  "Platinum",
    "PA=F":  "Palladium",
    "CL=F":  "WTI Oil",
    "BZ=F":  "Brent Oil",
    "HG=F":  "Copper",
    "NG=F":  "Natural Gas",
}

# Expressed as USD/ZAR, GBP/ZAR etc. (units of ZAR per 1 foreign currency unit)
# — the convention most South Africans are familiar with (e.g. "dollar at R18.50")
FX_PAIRS = {
    "USDZAR=X": "USD/ZAR",
    "EURZAR=X": "EUR/ZAR",
    "GBPZAR=X": "GBP/ZAR",
    "JPYZAR=X": "JPY/ZAR",
    "CNYZAR=X": "CNY/ZAR",
    "AUDZAR=X": "AUD/ZAR",
}

# =========================================
# HELPERS
# =========================================

DIVIDER  = "=" * 70
THIN_DIV = "-" * 70


def pct_change(old, new):
    return ((new - old) / old) * 100


def arrow(pct):
    if pct > 0:
        return "▲"
    if pct < 0:
        return "▼"
    return " "


def fetch(ticker, period="5d"):
    """Return history DataFrame or None on failure."""
    try:
        data = yf.Ticker(ticker).history(period=period)
        return data if not data.empty else None
    except Exception:
        return None


# =========================================
# SECTION BUILDERS
# =========================================

def build_stock_sections():
    """
    Fetches all JSE Top 40 tickers and returns:
      - full daily ranking (best → worst)
      - top 5 biggest absolute movers
      - top 3 / bottom 3 over 3 trading days
    """

    daily   = []
    three_d = []

    for ticker in JSE_TOP40:

        data = fetch(ticker)

        if data is None or len(data) < 4:
            continue

        today     = data["Close"].iloc[-1]
        yesterday = data["Close"].iloc[-2]
        three_ago = data["Close"].iloc[-4]

        daily.append({
            "ticker": ticker,
            "close":  today,
            "pct":    pct_change(yesterday, today),
        })

        three_d.append({
            "ticker": ticker,
            "close":  today,
            "pct":    pct_change(three_ago, today),
        })

    daily_ranked   = sorted(daily,   key=lambda x: x["pct"], reverse=True)
    biggest_movers = sorted(daily,   key=lambda x: abs(x["pct"]), reverse=True)
    best_3d        = sorted(three_d, key=lambda x: x["pct"], reverse=True)
    worst_3d       = sorted(three_d, key=lambda x: x["pct"])

    lines = []

    # --- All daily movers ---
    lines += [DIVIDER, "JSE TOP 40  |  1-DAY MOVERS  (best → worst)", DIVIDER]
    for s in daily_ranked:
        lines.append(
            f"  {s['ticker']:<12} {arrow(s['pct'])} {s['pct']:+6.2f}%   "
            f"close: {s['close']:>10.2f}"
        )

    # --- Biggest absolute movers ---
    lines += ["", DIVIDER, "JSE TOP 40  |  BIGGEST MOVERS TODAY  (top 5)", DIVIDER]
    for s in biggest_movers[:5]:
        lines.append(
            f"  {s['ticker']:<12} {arrow(s['pct'])} {s['pct']:+6.2f}%   "
            f"close: {s['close']:>10.2f}"
        )

    # --- 3-day best ---
    lines += ["", DIVIDER, "JSE TOP 40  |  BEST 3-DAY PERFORMERS  (top 3)", DIVIDER]
    for s in best_3d[:3]:
        lines.append(
            f"  {s['ticker']:<12} {arrow(s['pct'])} {s['pct']:+6.2f}%   "
            f"close: {s['close']:>10.2f}"
        )

    # --- 3-day worst ---
    lines += ["", DIVIDER, "JSE TOP 40  |  WORST 3-DAY PERFORMERS  (bottom 3)", DIVIDER]
    for s in worst_3d[:3]:
        lines.append(
            f"  {s['ticker']:<12} {arrow(s['pct'])} {s['pct']:+6.2f}%   "
            f"close: {s['close']:>10.2f}"
        )

    return lines


def build_indices_section():

    lines = ["", DIVIDER, "JSE INDICES", DIVIDER]

    for ticker, name in INDICES.items():

        data = fetch(ticker)

        if data is None or len(data) < 2:
            lines.append(f"  {name:<20}  n/a")
            continue

        today     = data["Close"].iloc[-1]
        yesterday = data["Close"].iloc[-2]
        pct       = pct_change(yesterday, today)

        lines.append(
            f"  {name:<20} {arrow(pct)} {pct:+6.2f}%   "
            f"close: {today:>12.2f}"
        )

    return lines


def build_commodities_section():

    lines = ["", DIVIDER, "GLOBAL COMMODITIES", DIVIDER]

    for ticker, name in COMMODITIES.items():

        data = fetch(ticker)

        if data is None or len(data) < 2:
            lines.append(f"  {name:<15}  n/a")
            continue

        today     = data["Close"].iloc[-1]
        yesterday = data["Close"].iloc[-2]
        pct       = pct_change(yesterday, today)

        lines.append(
            f"  {name:<15} {arrow(pct)} {pct:+6.2f}%   "
            f"price: {today:>10.2f}"
        )

    return lines


def build_fx_section():

    lines = ["", DIVIDER, "SOUTH AFRICAN FX  (units of ZAR per 1 foreign unit)", DIVIDER]

    for ticker, name in FX_PAIRS.items():

        data = fetch(ticker)

        if data is None or len(data) < 2:
            lines.append(f"  {name:<12}  n/a")
            continue

        today     = data["Close"].iloc[-1]
        yesterday = data["Close"].iloc[-2]
        pct       = pct_change(yesterday, today)

        # A rising USD/ZAR means the rand weakened — flag it clearly
        direction = "rand weaker" if pct > 0 else "rand stronger" if pct < 0 else ""

        lines.append(
            f"  {name:<12} {arrow(pct)} {pct:+6.2f}%   "
            f"rate: {today:>8.4f}   {direction}"
        )

    return lines


# =========================================
# MAIN
# =========================================

def generate_stock_prices():

    sections = []
    sections += build_stock_sections()
    sections += build_indices_section()
    sections += build_commodities_section()
    sections += build_fx_section()
    sections.append("")   # trailing newline

    output = "\n".join(sections) + "\n"

    with open("stockInfo.txt", "a", encoding="utf-8") as f:
        f.write(output)

    print("DONE: stock prices appended to stockInfo.txt")


# =========================================
# RUN
# =========================================

if __name__ == "__main__":
    generate_stock_prices()
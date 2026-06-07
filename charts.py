# charts.py

import yfinance as yf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
import base64
import requests as req

TICKER_MAP = {
    "ABG": "ABG.JO", "AGL": "AGL.JO", "ANG": "ANG.JO",
    "ANH": "ANH.JO", "ARI": "ARI.JO", "BHG": "BHG.JO",
    "BID": "BID.JO", "BVT": "BVT.JO", "BTI": "BTI.JO",
    "CFR": "CFR.JO", "CLS": "CLS.JO", "CPI": "CPI.JO",
    "DSY": "DSY.JO", "EXX": "EXX.JO", "FSR": "FSR.JO",
    "GFI": "GFI.JO", "GLN": "GLN.JO", "GRT": "GRT.JO",
    "HAR": "HAR.JO", "IMP": "IMP.JO", "INL": "INL.JO",
    "INP": "INP.JO", "KIO": "KIO.JO", "MTN": "MTN.JO",
    "NED": "NED.JO", "NPN": "NPN.JO", "NRP": "NRP.JO",
    "OMU": "OMU.JO", "OUT": "OUT.JO", "PRX": "PRX.JO",
    "REM": "REM.JO", "SBK": "SBK.JO", "SLM": "SLM.JO",
    "SOL": "SOL.JO", "SSW": "SSW.JO", "VOD": "VOD.JO",
    "WHL": "WHL.JO"
}

NAME_VARIATIONS = {
    "ABG": ["Absa Group", "ABSA", "Absa", "ABG", "ABG.JO"],
    "AGL": ["Anglo American", "AGL", "AGL.JO"],
    "ANG": ["AngloGold Ashanti", "AngloGold", "ANG", "ANG.JO"],
    "ANH": ["AB InBev", "ANH", "ANH.JO"],
    "ARI": ["African Rainbow Minerals", "African Rainbow", "ARI", "ARI.JO"],
    "BHG": ["Bidcorp", "BHG", "BHG.JO"],
    "BID": ["Bidvest", "BID", "BID.JO"],
    "BVT": ["BVT", "BVT.JO"],
    "BTI": ["British American Tobacco", "BTI", "BTI.JO"],
    "CFR": ["Richemont", "CFR", "CFR.JO"],
    "CLS": ["Clicks", "CLS", "CLS.JO"],
    "CPI": ["Capitec", "CPI", "CPI.JO"],
    "DSY": ["Discovery", "DSY", "DSY.JO"],
    "EXX": ["Exxaro", "EXX", "EXX.JO"],
    "FSR": ["FirstRand", "FSR", "FSR.JO"],
    "GFI": ["Gold Fields", "GFI", "GFI.JO"],
    "GLN": ["Glencore", "GLN", "GLN.JO"],
    "GRT": ["Growthpoint", "GRT", "GRT.JO"],
    "HAR": ["Harmony Gold", "Harmony", "HAR", "HAR.JO"],
    "IMP": ["Impala Platinum", "Impala", "IMP", "IMP.JO"],
    "INL": ["Investec", "INL", "INL.JO"],
    "INP": ["INP", "INP.JO"],
    "KIO": ["Kumba", "KIO", "KIO.JO"],
    "MTN": ["MTN", "MTN.JO"],
    "NED": ["Nedbank", "NED", "NED.JO"],
    "NPN": ["Naspers", "NPN", "NPN.JO"],
    "NRP": ["NRP", "NRP.JO"],
    "OMU": ["Old Mutual", "OMU", "OMU.JO"],
    "OUT": ["OUTsurance", "OUT", "OUT.JO"],
    "PRX": ["Prosus", "PRX", "PRX.JO"],
    "REM": ["Remgro", "REM", "REM.JO"],
    "SBK": ["Standard Bank", "SBK", "SBK.JO"],
    "SLM": ["Sanlam", "SLM", "SLM.JO"],
    "SOL": ["Sasol", "SOL", "SOL.JO"],
    "SSW": ["Sibanye-Stillwater", "Sibanye", "SSW", "SSW.JO"],
    "VOD": ["Vodacom", "VOD", "VOD.JO"],
    "WHL": ["Woolworths", "WHL", "WHL.JO"],
}

# =========================================
# GENERATE CHART — returns PNG bytes
# =========================================

def generate_chart_bytes(ticker_short):
    import io

    yf_ticker = TICKER_MAP.get(ticker_short.upper())
    if not yf_ticker:
        return None

    try:
        data = yf.Ticker(yf_ticker).history(period="14d", interval="1h")
        if data.empty or len(data) < 2:
            return None

        # Strip weekends
        data = data[data.index.weekday < 5]

        # Last 5 trading days only
        trading_days = sorted(data.index.normalize().unique())
        if not trading_days:
            return None
        data = data[data.index.normalize().isin(trading_days[-5:])]

        if len(data) < 2:
            return None

        prices = data["Close"]
        x = list(range(len(prices)))
        y = prices.values

        net_change = float(y[-1]) - float(y[0])
        line_color = "#00c87a" if net_change >= 0 else "#ff4d4d"

        fig, ax = plt.subplots(figsize=(10, 4))
        fig.patch.set_facecolor("#0f1117")
        ax.set_facecolor("#0f1117")

        ax.plot(x, y, color=line_color, linewidth=2.0, zorder=3)
        ax.fill_between(x, y, float(y.min()), alpha=0.15, color=line_color, zorder=2)

        day_ticks = {}
        for i, ts in enumerate(prices.index):
            day_key = ts.normalize()
            if day_key not in day_ticks:
                day_ticks[day_key] = i

        ax.set_xticks(list(day_ticks.values()))
        ax.set_xticklabels(
            [ts.strftime("%a %b %d") for ts in day_ticks.keys()],
            color="#aaaaaa", fontsize=9
        )
        ax.tick_params(axis="y", colors="#aaaaaa", labelsize=9)

        for spine in ax.spines.values():
            spine.set_edgecolor("#333333")

        ax.grid(axis="y", color="#222222", linestyle="--", linewidth=0.5)
        ax.grid(axis="x", visible=False)
        ax.set_xlim(-1, len(x))

        pct = ((float(y[-1]) - float(y[0])) / float(y[0])) * 100
        sign = "+" if pct >= 0 else ""
        ax.set_title(
            f"{ticker_short}   {sign}{pct:.2f}%   (5 trading days)",
            color="white", fontsize=12, pad=10, fontweight="bold"
        )

        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    except Exception as e:
        print(f"Chart error for {ticker_short}: {e}")
        return None


# =========================================
# UPLOAD TO IMGUR — returns public URL
# Get a free Client-ID at imgur.com/oauth2/addclient
# Set IMGUR_CLIENT_ID in your .env
# =========================================

def upload_to_imgur(image_bytes, ticker):
    client_id = os.getenv("IMGUR_CLIENT_ID")
    if not client_id:
        print("WARNING: IMGUR_CLIENT_ID not set in .env — charts will not render in email")
        return None

    try:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        response = req.post(
            "https://api.imgur.com/3/image",
            headers={"Authorization": f"Client-ID {client_id}"},
            data={"image": b64, "type": "base64", "name": f"{ticker}.png"},
            timeout=30
        )
        data = response.json()
        if data.get("success"):
            url = data["data"]["link"]
            print(f"  Uploaded {ticker} -> {url}")
            return url
        else:
            print(f"  Imgur upload failed for {ticker}: {data}")
            return None
    except Exception as e:
        print(f"  Imgur upload error for {ticker}: {e}")
        return None


# =========================================
# GENERATE + UPLOAD CHARTS
# Returns dict: { "SBK": "https://i.imgur.com/xxx.png", ... }
# =========================================

def generate_charts(tickers):
    import shutil
    from dotenv import load_dotenv
    load_dotenv()

    # Wipe old charts so stale images never linger
    if os.path.exists("./charts"):
        shutil.rmtree("./charts")
        print("  Cleared old charts folder")

    charts = {}
    for t in tickers:
        print(f"  Generating chart: {t}")
        img_bytes = generate_chart_bytes(t)
        if img_bytes:
            url = upload_to_imgur(img_bytes, t)
            if url:
                charts[t] = url
    return charts


# =========================================
# INJECT CHARTS INTO HTML
# Inserts <img src="https://..."> after the
# closing </p> of the paragraph mentioning ticker
# =========================================

def inject_charts_into_html(html, charts):
    for ticker, url in charts.items():
        variations = NAME_VARIATIONS.get(ticker, [ticker, f"{ticker}.JO"])
        paragraphs = html.split("</p>")

        for i, para in enumerate(paragraphs):
            matched = False
            for name in variations:
                if f"<strong>{name}</strong>" in para or name in para:
                    img_tag = (
                        f'<div style="margin:16px 0;">'
                        f'<img src="{url}" '
                        f'width="600" '
                        f'style="width:100%;max-width:600px;display:block;border-radius:6px;" '
                        f'alt="{ticker} 5-day chart"/>'
                        f'</div>'
                    )
                    paragraphs[i] = para + "</p>" + img_tag
                    matched = True
                    break
            if matched:
                html = "".join(
                    p if j == i else (p + ("</p>" if j < len(paragraphs) - 1 else ""))
                    for j, p in enumerate(paragraphs)
                )
                break

    return html


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    charts = generate_charts(["SOL", "SBK", "ANG"])
    print(f"\nGenerated {len(charts)} charts")
    for t, url in charts.items():
        print(f"  {t} -> {url}")
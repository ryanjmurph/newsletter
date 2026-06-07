# stockNews.py

import os
import re
import time
import requests
from bs4 import BeautifulSoup
from pathlib import Path

# =========================================
# SARB MARKET RATES
# =========================================

def fetch_sarb_rates(retries=3):
    try:
        from playwright.sync_api import sync_playwright

        url = "https://www.resbank.co.za/en/home/what-we-do/statistics/key-statistics/current-market-rates"

        TARGET_RATES = {
            "sarb policy rate": "SARB Policy Rate (Repo)",
            "prime":            "Prime Rate",
            "r2030":            "R2030 yield",
            "r209":             "R209 yield",
            "sabor":            "SABOR",
            "zaronia":          "ZARONIA",
            "zar/usd":          "ZAR/USD",
            "zar/gbp":          "ZAR/GBP",
            "zar/eur":          "ZAR/EUR",
            "zar/jpy":          "ZAR/JPY",
        }

        numeric_re = re.compile(r"^\d{1,3}(\.\d{1,4})?$")

        for attempt in range(1, retries + 1):
            print(f"  SARB fetch attempt {attempt}/{retries}...")
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()

                    # domcontentloaded is much faster than networkidle
                    # the table data loads quickly — we just wait for it explicitly
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)

                    # Wait for the table to appear (up to 20s)
                    page.wait_for_selector("table", timeout=20000)

                    # Give JS a moment to populate the values
                    page.wait_for_timeout(4000)

                    html = page.content()
                    browser.close()

                soup = BeautifulSoup(html, "html.parser")
                rates = {}

                for table in soup.find_all("table"):
                    for row in table.find_all("tr"):
                        cells = row.find_all("td")
                        if not cells:
                            continue
                        indicator = cells[0].get_text(strip=True).lower()
                        matched_label = None
                        for target_key, display_name in TARGET_RATES.items():
                            if target_key in indicator:
                                matched_label = display_name
                                break
                        if not matched_label:
                            continue
                        numeric_values = [
                            cell.get_text(strip=True)
                            for cell in cells[1:]
                            if numeric_re.match(cell.get_text(strip=True))
                        ]
                        if not numeric_values:
                            continue
                        rates[matched_label] = {
                            "value":       numeric_values[0],
                            "last_period": numeric_values[1] if len(numeric_values) > 1 else ""
                        }

                if rates:
                    print(f"  SARB rates fetched: {list(rates.keys())}")
                    return rates
                else:
                    print(f"  Attempt {attempt}: page loaded but no rates found — retrying")

            except Exception as e:
                print(f"  Attempt {attempt} failed: {e}")
                if attempt < retries:
                    time.sleep(3)

        print("WARNING: All SARB fetch attempts failed")
        return {}

    except ImportError:
        print("WARNING: playwright not installed — run: pip install playwright && playwright install chromium")
        return {}


def format_sarb_rates(rates):
    if not rates:
        return "SARB rates unavailable.\n"
    lines = [
        "=" * 80,
        "SARB CURRENT MARKET RATES",
        "=" * 80,
        f"{'Indicator':<30} {'Value':>10}  {'Last Period':>12}",
        "-" * 60,
    ]
    for name, data in rates.items():
        lines.append(f"{name:<30} {data['value']:>10}  {data['last_period']:>12}")
    lines.append("")
    return "\n".join(lines)


# =========================================
# NEWS SCRAPER
# =========================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0 Safari/537.36"
    )
}

SOURCES = [
    {"name": "Daily Investor", "url": "https://dailyinvestor.com"},
    {"name": "Moneyweb",       "url": "https://www.moneyweb.co.za"},
    {"name": "BusinessLIVE",   "url": "https://www.businesslive.co.za"},
]

EQUITY_KEYWORDS = [
    "JSE", "share", "shares", "equity", "equities", "stock", "stocks",
    "earnings", "results", "profit", "dividend", "market", "trading update",
    "bond", "yield", "repo", "interest rate", "SARB", "inflation", "rand",
    "banks", "mining", "gold", "platinum", "financials", "commodity",
    "commodities", "oil",
    "Naspers", "Prosus", "Sasol", "MTN", "Standard Bank", "FirstRand",
    "Capitec", "Absa", "Nedbank", "Old Mutual", "Sanlam", "Vodacom",
    "Woolworths", "Shoprite", "Clicks", "Bidcorp", "Bidvest", "Tiger Brands",
    "Remgro", "OUTsurance",
    "Anglo American", "AngloGold", "Glencore", "Harmony", "Gold Fields",
    "Impala Platinum", "Exxaro", "Kumba", "Northam Platinum", "BHP",
    "African Rainbow Minerals", "Sibanye", "Thungela",
    "ABG", "AGL", "ANG", "ANH", "ARI", "BHG", "BID", "BVT", "BTI", "CFR",
    "CLS", "CPI", "DSY", "EXX", "FSR", "GFI", "GLN", "GRT", "HAR", "IMP",
    "INL", "INP", "KIO", "MTN", "NED", "NPN", "NRP", "OMU", "OUT", "PRX",
    "REM", "SBK", "SLM", "SOL", "SSW", "VOD", "WHL",
    "banking", "insurance", "credit", "consumer spending", "retail sales",
    "Federal Reserve", "Fed", "China", "GDP", "recession", "tariffs",
    "currency", "rates", "rate cut", "rate hike", "Treasury yields",
    "emerging markets",
]


def relevance_score(text):
    if not text:
        return 0
    text_lower = text.lower()
    return sum(kw.lower() in text_lower for kw in EQUITY_KEYWORDS)


def extract_date(soup):
    for tag, attrs in [
        ("meta", {"property": "article:published_time"}),
        ("meta", {"name": "publish-date"}),
        ("meta", {"name": "pubdate"}),
        ("meta", {"name": "date"}),
        ("meta", {"name": "dc.date"}),
        ("meta", {"itemprop": "datePublished"}),
    ]:
        meta = soup.find(tag, attrs=attrs)
        if meta and meta.get("content"):
            return meta["content"]
    time_tag = soup.find("time")
    if time_tag:
        return time_tag.get("datetime") or time_tag.get_text(strip=True)
    return "UNKNOWN DATE"


def scrape_site(site):
    articles = []
    try:
        resp = requests.get(site["url"], headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        seen = set()

        for link in soup.find_all("a"):
            href = link.get("href")
            if not href:
                continue
            if href.startswith("/"):
                href = site["url"] + href
            if href in seen or site["url"] not in href:
                continue
            seen.add(href)

            title = link.get_text(strip=True)
            if len(title) < 20 or relevance_score(title) == 0:
                continue

            try:
                article_resp = requests.get(href, headers=HEADERS, timeout=10)
                article_soup = BeautifulSoup(article_resp.text, "html.parser")
                date = extract_date(article_soup)
                body = " ".join(
                    p.get_text(" ", strip=True)
                    for p in article_soup.find_all("p")
                )
                score = relevance_score(body)
                if score == 0:
                    continue
                articles.append({
                    "source": site["name"],
                    "title":  title,
                    "url":    href,
                    "date":   date,
                    "body":   body[:3000],
                    "score":  score,
                })
                time.sleep(1)
            except Exception:
                continue

    except Exception:
        pass

    return articles


def scrape_all_news():
    guaranteed = []
    remaining  = []

    for site in SOURCES:
        site_articles = sorted(
            scrape_site(site),
            key=lambda x: x["score"],
            reverse=True
        )
        if site_articles:
            guaranteed.append(site_articles[0])
            remaining.extend(site_articles[1:])

    remaining = sorted(remaining, key=lambda x: x["score"], reverse=True)
    return guaranteed + remaining[:max(0, 8 - len(guaranteed))]


# =========================================
# MAIN
# =========================================

def generate_stock_news():

    Path("stockInfo.txt").unlink(missing_ok=True)

    print("Fetching SARB rates...")
    sarb_rates = fetch_sarb_rates()

    print("Scraping news...")
    articles = scrape_all_news()
    print(f"Scraped {len(articles)} articles")

    lines = []
    lines.append(format_sarb_rates(sarb_rates))
    lines.append("=" * 80)
    lines.append("JSE / MARKET NEWS ARTICLES")
    lines.append("=" * 80)

    for i, a in enumerate(articles):
        lines.append("")
        lines.append(f"ARTICLE {i + 1}")
        lines.append(f"SOURCE: {a['source']}")
        lines.append(f"DATE:   {a['date']}")
        lines.append("")
        lines.append("TITLE:")
        lines.append(a["title"])
        lines.append("")
        lines.append("URL:")
        lines.append(a["url"])
        lines.append("")
        lines.append("BODY:")
        lines.append(a["body"])
        lines.append("-" * 80)

    with open("stockInfo.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"DONE: stockInfo.txt written — {len(articles)} articles + SARB rates")


if __name__ == "__main__":
    generate_stock_news()
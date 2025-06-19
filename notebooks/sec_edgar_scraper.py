import re
import json
import csv
from pathlib import Path
from datetime import datetime

try:
    import requests
    import feedparser
    from bs4 import BeautifulSoup
except ImportError as e:
    raise ImportError(
        "requests, feedparser and beautifulsoup4 are required. Install via `pip install requests feedparser beautifulsoup4`."
    ) from e

TRACK_TYPES = {"8-K", "10-K", "10-Q"}
TICKERS = ["AAPL", "MSFT", "AMZN"]


def build_feed_url(ticker: str) -> str:
    return (
        "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany"
        f"&CIK={ticker}&type=&count=40&output=atom"
    )


def parse_accession(url: str) -> tuple[str, str]:
    match = re.search(r"data/(\d+)/(\d+)-index\.html", url)
    if not match:
        return "", ""
    cik = match.group(1)
    accession = match.group(2)
    return cik, accession


def fetch_feed(ticker: str):
    url = build_feed_url(ticker)
    headers = {"User-Agent": "sec_edgar_scraper"}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return feedparser.parse(resp.text)


def parse_filing_page(url: str) -> dict:
    headers = {"User-Agent": "sec_edgar_scraper"}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    def get_text(label: str) -> str:
        cell = soup.find(text=re.compile(label, re.I))
        if cell and cell.parent and cell.parent.find_next_sibling("td"):
            return cell.parent.find_next_sibling("td").get_text(strip=True)
        return ""

    filing_date = get_text("Filing Date")
    report_period = get_text("Period of Report")
    company_name = get_text("Company Name") or get_text("Company")

    docs = []
    for a in soup.select('table a[href$=".htm"], table a[href$=".txt"]'):
        href = a.get("href")
        if href and not href.startswith("http"):
            href = "https://www.sec.gov" + href
        docs.append(href)

    items = []
    if "8-K" in soup.text:
        items = re.findall(r"Item\s+\d+\.\d+", soup.text)

    return {
        "filing_date": filing_date,
        "report_period": report_period,
        "company_name": company_name,
        "document_links": docs,
        "item_sections": list(dict.fromkeys(items)),
    }


def parse_entries(ticker: str):
    feed = fetch_feed(ticker)
    filings = []
    for entry in feed.entries:
        form_type = entry.title.split("-")[0].strip()
        if form_type not in TRACK_TYPES:
            continue
        cik, accession = parse_accession(entry.link)
        base = {
            "ticker": ticker,
            "cik": cik,
            "form_type": form_type,
            "published_date": entry.published,
            "filing_url": entry.link,
            "accession_number": accession,
            "summary": getattr(entry, "summary", ""),
        }
        try:
            extra = parse_filing_page(entry.link)
        except Exception as e:  # noqa: BLE001
            print(f"Error parsing filing page {entry.link}: {e}")
            extra = {}
        filings.append({**base, **extra})
    return filings


def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_csv(data, path):
    if not data:
        return
    fields = list(data[0].keys())
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(data)


def main():
    all_filings = []
    for ticker in TICKERS:
        try:
            filings = parse_entries(ticker)
            all_filings.extend(filings)
        except Exception as e:  # noqa: BLE001
            print(f"Error fetching filings for {ticker}: {e}")

    root_dir = Path(__file__).resolve().parents[1]
    today = datetime.utcnow().strftime("%Y-%m-%d")
    out_dir = root_dir / "data" / "edgar" / today
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%H%M%S")
    json_path = out_dir / f"edgar_{timestamp}.json"
    csv_path = out_dir / f"edgar_{timestamp}.csv"

    save_json(all_filings, json_path)
    save_csv(all_filings, csv_path)
    print(f"Saved {len(all_filings)} filings to {json_path} and {csv_path}")


if __name__ == "__main__":
    main()

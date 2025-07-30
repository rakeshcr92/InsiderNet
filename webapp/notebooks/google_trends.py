import json
import csv
from datetime import datetime, timedelta
from pathlib import Path

try:
    from pytrends.request import TrendReq
except ImportError as e:
    raise ImportError("Install pytrends via `pip install pytrends`") from e


# Ticker-to-company/CEO map
STOCKS = {
    "AAPL": {"company": "Apple Inc", "ceo": "Tim Cook"},
    "MSFT": {"company": "Microsoft Corporation", "ceo": "Satya Nadella"},
    "AMZN": {"company": "Amazon.com, Inc.", "ceo": "Andy Jassy"},
}

DAYS_BACK = 730  # 2 years


def build_queries() -> list[str]:
    queries: list[str] = []
    for ticker, info in STOCKS.items():
        queries.extend([ticker, info["company"], info["ceo"]])
    return list(dict.fromkeys(queries))  # Remove duplicates, preserve order


def fetch_daily_interest(pytrends: TrendReq, query: str, days: int = 730) -> list[dict]:
    """Fetch daily Google Trends interest by chunking into multiple ranges."""
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)

    delta = timedelta(days=180)  # Google Trends allows ~180 days of daily granularity
    current_start = start_date
    all_records = []

    while current_start < end_date:
        current_end = min(current_start + delta, end_date)
        timeframe = f"{current_start} {current_end}"

        try:
            pytrends.build_payload([query], timeframe=timeframe)
            df = pytrends.interest_over_time()

            if not df.empty and query in df.columns:
                for date, row in df.iterrows():
                    all_records.append({
                        "query": query,
                        "date": date.strftime("%Y-%m-%d"),
                        "interest": int(row[query]),
                        "is_partial": bool(row.get("isPartial", False))
                    })
        except Exception as e:
            print(f"❌ Error fetching {query} from {timeframe}: {e}")

        current_start = current_end + timedelta(days=1)

    return all_records


def save_json(data: list[dict], path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_csv(data: list[dict], path: Path) -> None:
    if not data:
        return
    fields = list(data[0].keys())
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(data)


def main():
    pytrends = TrendReq(hl='en-US', tz=360, proxies=['http://proxy1.com', 'http://proxy2.com'])
    queries = build_queries()
    all_records = []

    for q in queries:
        print(f"🔍 Fetching 2 years of daily trends for '{q}'...")
        all_records.extend(fetch_daily_interest(pytrends, q, days=730))

    root_dir = Path(__file__).resolve().parents[1]
    today = datetime.utcnow().strftime("%Y-%m-%d")
    out_dir = root_dir / "data" / "trends" / today
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%H%M%S")
    save_json(all_records, out_dir / f"trends_{timestamp}.json")
    save_csv(all_records, out_dir / f"trends_{timestamp}.csv")

    print(f"✅ Saved {len(all_records)} records for {len(queries)} queries")


if __name__ == "__main__":
    main()

import json
import csv
from datetime import datetime, timedelta
from pathlib import Path

try:
    from pytrends.request import TrendReq
except ImportError as e:
    raise ImportError(
        "pytrends is required to run this script. Install via `pip install pytrends`."
    ) from e

# Example mapping of tickers to company and CEO names. Extend as needed.
STOCKS = {
    "AAPL": {"company": "Apple Inc", "ceo": "Tim Cook"},
    "MSFT": {"company": "Microsoft Corporation", "ceo": "Satya Nadella"},
    "AMZN": {"company": "Amazon.com, Inc.", "ceo": "Andy Jassy"},
}

DAYS_BACK = 90  # Number of days of interest data to fetch


def build_queries() -> list[str]:
    """Return a unique list of queries from ticker, company and CEO names."""
    queries: list[str] = []
    for ticker, info in STOCKS.items():
        queries.append(ticker)
        queries.append(info["company"])
        queries.append(info["ceo"])
    # Preserve order but remove duplicates
    return list(dict.fromkeys(queries))


def fetch_daily_interest(pytrends: TrendReq, query: str) -> list[dict]:
    """Fetch daily Google Trends interest for a single query."""
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=DAYS_BACK)
    timeframe = f"{start_date} {end_date}"
    pytrends.build_payload([query], timeframe=timeframe)
    df = pytrends.interest_over_time()
    records = []
    if df.empty:
        return records
    for date, row in df.iterrows():
        records.append(
            {
                "query": query,
                "date": date.strftime("%Y-%m-%d"),
                "interest": int(row[query]),
                "is_partial": bool(row.get("isPartial", False)),
            }
        )
    return records


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
    pytrends = TrendReq(hl="en-US", tz=360)
    queries = build_queries()
    all_records: list[dict] = []
    for q in queries:
        try:
            all_records.extend(fetch_daily_interest(pytrends, q))
        except Exception as e:  # noqa: BLE001
            print(f"Error fetching trends for '{q}': {e}")

    root_dir = Path(__file__).resolve().parents[1]
    today = datetime.utcnow().strftime("%Y-%m-%d")
    out_dir = root_dir / "data" / "trends" / today
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%H%M%S")
    json_path = out_dir / f"trends_{timestamp}.json"
    csv_path = out_dir / f"trends_{timestamp}.csv"

    save_json(all_records, json_path)
    save_csv(all_records, csv_path)
    print(f"Saved {len(all_records)} records to {json_path} and {csv_path}")


if __name__ == "__main__":
    main()

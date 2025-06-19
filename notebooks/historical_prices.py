import json
import csv
from datetime import datetime, timedelta
from pathlib import Path

try:
    import yfinance as yf
except ImportError as e:
    raise ImportError(
        "yfinance is required to run this script. Install via `pip install yfinance`."
    ) from e

# Sample tickers. Extend as needed.
TICKERS = ["AAPL", "MSFT", "AMZN"]

# Number of days of historical prices to fetch
DAYS_BACK = 365


def fetch_prices(ticker: str) -> list[dict]:
    """Return daily adjusted close and volatility for a ticker."""
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=DAYS_BACK)
    df = yf.download(ticker, start=start_date, end=end_date, progress=False, interval="1d")
    df = df.dropna(subset=["Adj Close"])
    records: list[dict] = []
    for date, row in df.iterrows():
        adj_close = float(row["Adj Close"])
        high = float(row.get("High", adj_close))
        low = float(row.get("Low", adj_close))
        volatility = (high - low) / adj_close if adj_close else 0.0
        records.append(
            {
                "ticker": ticker,
                "date": date.strftime("%Y-%m-%d"),
                "adj_close": adj_close,
                "volatility": volatility,
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


def main() -> None:
    all_records: list[dict] = []
    for ticker in TICKERS:
        try:
            all_records.extend(fetch_prices(ticker))
        except Exception as e:  # noqa: BLE001
            print(f"Error fetching prices for {ticker}: {e}")

    root_dir = Path(__file__).resolve().parents[1]
    today = datetime.utcnow().strftime("%Y-%m-%d")
    out_dir = root_dir / "data" / "prices" / today
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%H%M%S")
    json_path = out_dir / f"prices_{timestamp}.json"
    csv_path = out_dir / f"prices_{timestamp}.csv"

    save_json(all_records, json_path)
    save_csv(all_records, csv_path)
    print(f"Saved {len(all_records)} records to {json_path} and {csv_path}")


if __name__ == "__main__":
    main()

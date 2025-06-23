"""Compute future price change labels for a ticker."""
import csv
import json
from datetime import datetime, timedelta
from pathlib import Path

try:
    import yfinance as yf
except ImportError as e:  # pragma: no cover - handled by runtime
    raise ImportError(
        "yfinance is required to run this script. Install via `pip install yfinance`."
    ) from e

# Days to look ahead when calculating future close
LOOK_AHEAD_DAYS = 5


def fetch_price_history(ticker: str, days_back: int = 365) -> list[dict]:
    end = datetime.utcnow().date()
    start = end - timedelta(days=days_back)
    df = yf.download(ticker, start=start, end=end, progress=False, interval="1d")
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
                "close": adj_close,
                "volatility": volatility,
            }
        )
    return records


def add_labels(records: list[dict]) -> list[dict]:
    """Add future_close, pct_change, binary_label and volatility_label."""
    for i, row in enumerate(records):
        if i + LOOK_AHEAD_DAYS < len(records):
            future_close = records[i + LOOK_AHEAD_DAYS]["close"]
        else:
            future_close = row["close"]
        pct_change = (future_close - row["close"]) / row["close"] if row["close"] else 0.0
        binary_label = 1 if pct_change > 0 else 0
        volatility_label = 1 if row["volatility"] > 0.05 else 0
        row.update(
            {
                "future_close": future_close,
                "pct_change": pct_change,
                "binary_label": binary_label,
                "volatility_label": volatility_label,
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


def main(ticker: str) -> None:
    records = fetch_price_history(ticker)
    records = add_labels(records)

    root_dir = Path(__file__).resolve().parents[1]
    today = datetime.utcnow().strftime("%Y-%m-%d")
    out_dir = root_dir / "data" / "labels" / ticker / today
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%H%M%S")
    json_path = out_dir / f"labels_{timestamp}.json"
    csv_path = out_dir / f"labels_{timestamp}.csv"

    save_json(records, json_path)
    save_csv(records, csv_path)
    print(f"Saved {len(records)} rows to {json_path} and {csv_path}")


if __name__ == "__main__":  # pragma: no cover - manual execution
    import sys

    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    main(ticker)

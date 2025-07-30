import json
import csv
import datetime
from pathlib import Path

try:
    import yfinance as yf
except ImportError as e:
    raise ImportError("yfinance is required. Install via `pip install yfinance`.") from e

LOOK_AHEAD_DAYS = 3  # You can change this
TICKER = "AAPL"  # You can change or loop over many
DAYS_BACK = 365


def fetch_price_history(ticker: str) -> list[dict]:
    """Return daily full price history for a ticker."""
    end_date = datetime.datetime.utcnow() - datetime.timedelta(days=1)
    start_date = end_date - datetime.timedelta(days=DAYS_BACK)

    ticker_obj = yf.Ticker(ticker)
    df = ticker_obj.history(start=start_date, end=end_date, interval="1d", auto_adjust=True)

    if df.empty or "Close" not in df.columns:
        print(f"[WARN] No valid data for {ticker}. Columns found: {df.columns.tolist()}")
        raise ValueError(f"Missing or incomplete data for {ticker}.")

    df = df.dropna(subset=["Close"])
    records: list[dict] = []

    for date, row in df.iterrows():
        close = float(row["Close"])
        open_ = float(row.get("Open", close))
        high = float(row.get("High", close))
        low = float(row.get("Low", close))
        volume = int(row.get("Volume", 0))
        dividends = float(row.get("Dividends", 0.0))
        splits = float(row.get("Stock Splits", 0.0))
        volatility = (high - low) / close if close else 0.0

        records.append(
            {
                "ticker": ticker,
                "date": date.strftime("%Y-%m-%d"),
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "adj_close": close,  # same as close when auto_adjust=True
                "volume": volume,
                "dividends": dividends,
                "stock_splits": splits,
                "volatility": volatility,
            }
        )
    return records


def add_labels(records: list[dict]) -> list[dict]:
    for i, row in enumerate(records):
        if i + LOOK_AHEAD_DAYS < len(records):
            future_close = records[i + LOOK_AHEAD_DAYS]["close"]
        else:
            future_close = row["close"]
        pct_change = (future_close - row["close"]) / row["close"] if row["close"] else 0.0
        binary_label = 1 if pct_change > 0 else 0
        volatility_label = 1 if row["volatility"] > 0.05 else 0

        row.update({
            "future_close": future_close,
            "pct_change": round(pct_change, 4),
            "binary_label": binary_label,
            "volatility_label": volatility_label,
        })

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
    try:
        records = fetch_price_data(TICKER)
        labeled_records = add_labels(records)

        root_dir = Path(__file__).resolve().parents[1]
        today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        out_dir = root_dir / "data" / "labels" / TICKER / today
        out_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.datetime.utcnow().strftime("%H%M%S")
        json_path = out_dir / f"labels_{timestamp}.json"
        csv_path = out_dir / f"labels_{timestamp}.csv"

        save_json(labeled_records, json_path)
        save_csv(labeled_records, csv_path)
        print(f"✅ Saved {len(labeled_records)} labeled rows to {json_path} and {csv_path}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()

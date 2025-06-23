"""Generate price change labels from saved historical price data."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd


def create_labels(prices_path: Path, output_dir: Path, look_ahead: int = 3, volatility_threshold: float = 0.02) -> None:
    """Create labels from a CSV of historical prices.

    Parameters
    ----------
    prices_path:
        Path to a CSV file with columns ``ticker``, ``date`` and ``adj_close``.
    output_dir:
        Directory under which ``labels/YYYY-MM-DD`` will be created.
    look_ahead:
        Number of days ahead to use when computing the ``future_close``.
    volatility_threshold:
        Rolling standard deviation threshold to determine ``volatility_label``.
    """
    df = pd.read_csv(prices_path)
    df["date"] = pd.to_datetime(df["date"])
    df.sort_values(by=["ticker", "date"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Price column may be named 'adj_close' from the scraper
    price_col = "adj_close" if "adj_close" in df.columns else "close"

    df["future_close"] = df.groupby("ticker")[price_col].shift(-look_ahead)
    df["pct_change"] = (df["future_close"] - df[price_col]) / df[price_col]
    df["binary_label"] = (df["pct_change"] > 0).astype(int)

    df["rolling_std"] = df.groupby("ticker")[price_col].transform(lambda x: x.shift(-1).rolling(look_ahead).std())
    df["volatility_label"] = (df["rolling_std"] > volatility_threshold).astype(int)

    df.dropna(subset=["future_close", "pct_change", "rolling_std"], inplace=True)

    timestamp = datetime.utcnow().strftime("%H%M%S")
    label_dir = Path(output_dir) / "labels" / datetime.utcnow().strftime("%Y-%m-%d")
    label_dir.mkdir(parents=True, exist_ok=True)

    df_out = df[[
        "ticker",
        "date",
        price_col,
        "future_close",
        "pct_change",
        "binary_label",
        "volatility_label",
    ]].rename(columns={price_col: "close"})

    csv_path = label_dir / f"labels_{timestamp}.csv"
    json_path = label_dir / f"labels_{timestamp}.json"

    df_out.to_csv(csv_path, index=False)
    df_out.to_json(json_path, orient="records", indent=2, date_format="iso")
    print(f"Saved {len(df_out)} labeled rows to {csv_path} and {json_path}")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Generate labels from price data")
    parser.add_argument("prices", type=Path, help="Path to historical prices CSV")
    parser.add_argument("output", type=Path, help="Root data directory")
    args = parser.parse_args()

    create_labels(args.prices, args.output)


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()

import pandas as pd
import numpy as np

import pandas as pd
import numpy as np
import datetime
from pathlib import Path


def create_labels(prices_path: Path, output_dir: Path, volatility_threshold: float = 0.02) -> None:
    df = pd.read_csv(prices_path)
    df["date"] = pd.to_datetime(df["date"])
    df.sort_values(by=["ticker", "date"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Shifted data for label generation
    df["future_close"] = df.groupby("ticker")["close"].shift(-3)
    df["pct_change"] = ((df["future_close"] - df["close"]) / df["close"]).round(4)
    df["binary_label"] = (df["pct_change"] > 0).astype(int)

    # Volatility label based on 3-day rolling std dev of next prices
    df["rolling_std"] = (
        df.groupby("ticker")["close"].transform(lambda x: x.shift(-1).rolling(3).std())
    )
    df["volatility_label"] = (df["rolling_std"] > volatility_threshold).astype(int)

    # Drop rows with NaNs from label calculation
    df.dropna(subset=["future_close", "pct_change", "rolling_std"], inplace=True)

    # Save output
    timestamp = datetime.datetime.utcnow().strftime("%H%M%S")
    label_dir = output_dir / "labels" / datetime.datetime.utcnow().strftime("%Y-%m-%d")
    label_dir.mkdir(parents=True, exist_ok=True)

    json_path = label_dir / f"labels_{timestamp}.json"
    csv_path = label_dir / f"labels_{timestamp}.csv"

    df_out = df[[
        "ticker", "date", "close", "future_close", "pct_change", "binary_label", "volatility_label"
    ]]
    df_out.to_csv(csv_path, index=False)
    df_out.to_json(json_path, orient="records", indent=2, date_format="iso")

    print(f"✅ Saved {len(df_out)} labeled rows to {csv_path} and {json_path}")

def main():
    prices_path = Path("/Users/rakeshcavala/Desktop/InsiderNet/data/prices/2025-06-19/prices_151250.csv")
    output_dir = Path("/Users/rakeshcavala/Desktop/InsiderNet/data")
    create_labels(prices_path, output_dir)


if __name__ == "__main__":
    main()

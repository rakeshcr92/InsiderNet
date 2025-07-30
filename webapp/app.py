"""Simple Flask front end for data collection and training."""
from __future__ import annotations

import os
import csv
import json
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, render_template, request
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error
from xgboost import XGBClassifier, XGBRegressor
import joblib

try:
    import openai
except ImportError as e:
    raise ImportError("Install OpenAI via `pip install openai`.") from e

from notebooks import (
    labels,
    labels_from_prices,
    google_trends,
    historical_prices,
    reddit_scraper,
    sec_edgar_scraper,
    feature_engineering
)

from notebooks.feature_engineering import (
    compute_price_features,
    compute_reddit_features,
    compute_trend_features,
    compute_time_features,
)


app = Flask(__name__)
openai.api_key = "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"

# ------------------------ Utilities ------------------------

def generate_keywords(ticker: str) -> list[str]:
    prompt = f"Generate a short comma-separated list of keywords related to {ticker} for Reddit searches. Include company and CEO names if known."
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=32,
        )
        return [kw.strip() for kw in response.choices[0].message.content.split(",") if kw.strip()]
    except Exception as exc:
        print(f"❌ OpenAI error: {exc}")
        return [ticker]

def search_reddit(keywords: list[str], limit: int = 20):
    reddit = reddit_scraper.get_reddit_client()
    posts = []
    for kw in keywords:
        for submission in reddit.subreddit("all").search(kw, sort="new", time_filter="month", limit=limit):
            posts.append({
                "id": submission.id,
                "selftext": submission.selftext,
                "upvotes": submission.score,
                "title": submission.title,
                "created_utc": submission.created_utc,
                "score": submission.score,
                "num_comments": submission.num_comments,
            })
    return posts

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

def train_model(features_df, target_column: str, model_path: Path):
    drop_cols = ["date", "ticker", "query", "is_partial", "day_of_week", "month", "is_weekend"]
    drop_cols = [col for col in drop_cols if col in features_df.columns]

    X = features_df.drop(columns=drop_cols + [target_column], errors="ignore").select_dtypes(include=["number"])
    y = features_df[target_column]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = XGBClassifier(use_label_encoder=False, eval_metric="logloss") if y.nunique() == 2 else XGBRegressor()
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    score = accuracy_score(y_test, preds.round()) if y.nunique() == 2 else mean_squared_error(y_test, preds)
    metric = "Accuracy" if y.nunique() == 2 else "MSE"
    print(f"✅ {metric}: {score:.4f}")

    joblib.dump(model, model_path)
    print(f"✅ Model saved to {model_path}")
    return model

# ------------------------ Flask Routes ------------------------

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/track", methods=["POST"])
def track():
    ticker = request.form.get("ticker", "").upper()
    if not ticker:
        return render_template("index.html", message="No ticker provided")

    keywords = generate_keywords(ticker)
    reddit_posts = search_reddit(keywords)

    # ⚠️ Safe Google Trends fetch with fallback
    try:
        trends = google_trends.fetch_daily_interest(
            google_trends.TrendReq(hl="en-US", tz=360), ticker
        )
    except Exception as e:
        print(f"❌ Error fetching Google Trends for {ticker}: {e}")
        trends = []

    filings = sec_edgar_scraper.parse_entries(ticker)
    labels_data = labels.fetch_price_history(ticker)
    labels_data = labels.add_labels(labels_data)
    price_records = historical_prices.fetch_prices(ticker)

    root = Path(__file__).resolve().parents[1]
    today = datetime.utcnow().strftime("%Y-%m-%d")
    out_dir = root / "data" / ticker / today
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%H%M%S")

    save_json(reddit_posts, out_dir / f"reddit_{timestamp}.json")
    save_json(trends, out_dir / f"trends_{timestamp}.json")
    save_json(filings, out_dir / f"edgar_{timestamp}.json")
    save_json(labels_data, out_dir / f"labels_{timestamp}.json")
    save_json(price_records, out_dir / f"prices_{timestamp}.json")
    save_csv(price_records, out_dir / f"prices_{timestamp}.csv")

    # 🧠 Compute features
    price_df = pd.DataFrame(price_records)
    reddit_df = pd.DataFrame(reddit_posts)
    trend_df = pd.DataFrame(trends)

    price_features = compute_price_features(price_df)
    reddit_features = compute_reddit_features(reddit_df)

# ✅ Prevent KeyError if Google Trends failed
    if not trend_df.empty and "date" in trend_df.columns:
        trend_features = compute_trend_features(trend_df)
    else:
        print(f"⚠️ Skipping trend feature engineering — Google Trends missing or invalid.")
        trend_features = pd.DataFrame(columns=["date"])

    time_features = compute_time_features(price_df)

    feature_df = price_features.merge(trend_features, on="date", how="left")
    feature_df = feature_df.merge(time_features, on="date", how="left")
    feature_df.fillna(0, inplace=True)

    features_csv_path = out_dir / f"features_{timestamp}.csv"
    feature_df.to_csv(features_csv_path, index=False)

    try:
        labels_from_prices.create_labels(out_dir / f"prices_{timestamp}.csv", root / "data")
    except Exception as exc:
        print(f"labels_from_prices error: {exc}")

    label_df = pd.DataFrame(labels_data)
    target_column = "binary_label"

    # ✅ Defensive check for date column
    if "date" not in feature_df.columns or "date" not in label_df.columns:
        print("❌ Training/Prediction error: 'date' column missing in features or labels")
        return render_template("index.html", message=f"❌ Could not train model — 'date' missing")

    full_data = feature_df.merge(label_df[["date", target_column]], on="date", how="inner")

    if not full_data.empty and full_data[target_column].nunique() > 1:
        model_path = out_dir / f"model_{timestamp}.pkl"
        model = train_model(full_data, target_column, model_path)

        try:
            # 🔮 Predict on last row
            latest_row = full_data.sort_values("date").iloc[-3:]

            # Drop non-numeric & unwanted cols
            drop_cols = ["date", "ticker", "query", "is_partial", "day_of_week", "month", "is_weekend", target_column]
            drop_cols = [col for col in drop_cols if col in latest_row.columns]

            X_latest = latest_row.drop(columns=drop_cols, errors="ignore")
            X_latest = X_latest.select_dtypes(include=["number"])

            # Ensure model input matches training
            prediction = model.predict(X_latest)[0]

            print(f"🔮 Prediction for {ticker} on {latest_row['date'].values[0]}: {prediction}")

        except Exception as e:
            print(f"❌ Prediction error: {e}")
    else:
        print("⚠️ Not enough data or label variation to train model.")

    return render_template("index.html", message=f"✅ Features collected, model trained, and prediction printed for {ticker}")

# ------------------------ Run ------------------------

if __name__ == "__main__":
    app.run(debug=True)

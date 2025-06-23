"""Simple Flask front end for data collection."""
from __future__ import annotations

import os
import csv
import json
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, render_template, request

try:
    import openai
except ImportError as e:  # pragma: no cover - handled at runtime
    raise ImportError(
        "openai is required to run this app. Install via `pip install openai`."
    ) from e

from notebooks import labels, google_trends, historical_prices, reddit_scraper, sec_edgar_scraper

app = Flask(__name__)


def generate_keywords(ticker: str) -> list[str]:
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        return [ticker]
    prompt = f"Generate a short comma-separated list of keywords related to {ticker} for Reddit searches. Include the company and CEO names if known."
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=32,
        )
        text = resp.choices[0].message.content
        return [kw.strip() for kw in text.split(",") if kw.strip()]
    except Exception as exc:  # noqa: BLE001
        print(f"OpenAI error: {exc}")
        return [ticker]


def search_reddit(keywords: list[str], limit: int = 20):
    reddit = reddit_scraper.get_reddit_client()
    start_ts = int((datetime.utcnow() - timedelta(days=30)).timestamp())
    posts = []
    for kw in keywords:
        query = kw
        for submission in reddit.subreddit("all").search(
            query, sort="new", time_filter="month", limit=limit
        ):
            posts.append(
                {
                    "id": submission.id,
                    "title": submission.title,
                    "created_utc": submission.created_utc,
                    "score": submission.score,
                    "num_comments": submission.num_comments,
                }
            )
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
    trends = google_trends.fetch_daily_interest(
        google_trends.TrendReq(hl="en-US", tz=360), ticker
    )
    filings = sec_edgar_scraper.parse_entries(ticker)
    labels_data = labels.fetch_price_history(ticker)
    labels_data = labels.add_labels(labels_data)

    root = Path(__file__).resolve().parents[1]
    today = datetime.utcnow().strftime("%Y-%m-%d")
    out_dir = root / "data" / ticker / today
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%H%M%S")

    save_json(reddit_posts, out_dir / f"reddit_{timestamp}.json")
    save_json(trends, out_dir / f"trends_{timestamp}.json")
    save_json(filings, out_dir / f"edgar_{timestamp}.json")
    save_json(labels_data, out_dir / f"labels_{timestamp}.json")

    return render_template("index.html", message=f"Data collected for {ticker}")


if __name__ == "__main__":  # pragma: no cover - manual run
    app.run(debug=True)

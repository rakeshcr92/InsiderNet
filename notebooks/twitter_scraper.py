import os
import json
import csv
from datetime import datetime
from pathlib import Path

try:
    import snscrape.modules.twitter as sntwitter
except (ModuleNotFoundError, AttributeError) as e:
    raise ImportError(
        "snscrape is required and may not be compatible with Python 3.12. "
        "Install or upgrade via `pip install -U snscrape` and consider using Python 3.11 if issues persist."
    ) from e


# Sample tickers and CEO names to search for. Extend as needed.
TICKERS = ["AAPL", "MSFT", "AMZN"]
CEO_NAMES = ["Tim Cook", "Satya Nadella", "Andy Jassy"]

# Broad finance-related search terms to surface trending stocks
BASE_QUERIES = [
    "stocks to watch",
    "market movers",
    "hot stocks",
    "trending stocks",
    "earnings report",
    "stock analysis",
    "bullish",
    "bearish",
    "upgraded stock",
    "downgraded stock",
]


def build_queries():
    """Combine tickers, CEO names, and base finance queries."""
    ticker_queries = [f"${t}" for t in TICKERS]
    return ticker_queries + CEO_NAMES + BASE_QUERIES


def fetch_tweets(queries, max_tweets=100):
    """Fetch tweets for each query using snscrape."""
    tweets = []
    for query in queries:
        scraper = sntwitter.TwitterSearchScraper(query)
        for i, tweet in enumerate(scraper.get_items()):
            if i >= max_tweets:
                break
            tweets.append({
                "query": query,
                "id": tweet.id,
                "content": tweet.content,
                "retweet_count": tweet.retweetCount,
                "date": tweet.date.isoformat(),
                "user_id": tweet.user.id,
            })
    return tweets


def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_csv(data, path):
    fields = ["query", "id", "content", "retweet_count", "date", "user_id"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in data:
            row = {k: item.get(k) for k in fields}
            writer.writerow(row)


def main():
    queries = build_queries()
    tweets = fetch_tweets(queries, max_tweets=100)

    root_dir = Path(__file__).resolve().parents[1]
    today = datetime.utcnow().strftime("%Y-%m-%d")
    out_dir = root_dir / "data" / "twitter" / today
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%H%M%S")
    json_path = out_dir / f"twitter_{timestamp}.json"
    csv_path = out_dir / f"twitter_{timestamp}.csv"

    save_json(tweets, json_path)
    save_csv(tweets, csv_path)
    print(f"Saved {len(tweets)} tweets to {json_path} and {csv_path}")


if __name__ == "__main__":
    main()

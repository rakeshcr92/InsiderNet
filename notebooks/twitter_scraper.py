import os
import json
import csv
from datetime import datetime
from pathlib import Path

try:
    import snscrape.modules.twitter as sntwitter
except ImportError:
    raise ImportError("snscrape is required to run this script. Install via `pip install snscrape`. ")

# Default search queries: stock tickers and CEO names
QUERIES = ["AAPL", "TSLA", "GOOGL", "Elon Musk", "Satya Nadella"]


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
    tweets = fetch_tweets(QUERIES, max_tweets=100)

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

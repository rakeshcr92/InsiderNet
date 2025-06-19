import os
import json
import csv
from datetime import datetime
from pathlib import Path

try:
    import tweepy
except ImportError as e:
    raise ImportError(
        "tweepy is required to run this script. Install via `pip install tweepy`."
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


def get_twitter_client():
    """Return a Tweepy client using the bearer token from the environment."""
    token = os.getenv("TWITTER_BEARER_TOKEN")
    if not token:
        raise RuntimeError("TWITTER_BEARER_TOKEN environment variable is required")
    return tweepy.Client(bearer_token=token, wait_on_rate_limit=True)


def fetch_tweets(client, queries, max_tweets=100):
    """Fetch tweets for each query using the Twitter API."""
    tweets = []
    for query in queries:
        try:
            paginator = tweepy.Paginator(
                client.search_recent_tweets,
                query=query,
                tweet_fields=["public_metrics", "created_at", "author_id"],
                max_results=100,
            )
            for i, tweet in enumerate(paginator.flatten(limit=max_tweets)):
                tweets.append({
                    "query": query,
                    "id": tweet.id,
                    "content": tweet.text,
                    "retweet_count": tweet.public_metrics.get("retweet_count", 0),
                    "date": tweet.created_at.isoformat(),
                    "user_id": tweet.author_id,
                })
        except tweepy.TweepyException as e:
            print(f"Error fetching tweets for '{query}': {e}")
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
    client = get_twitter_client()
    tweets = fetch_tweets(client, queries, max_tweets=100)

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

import os
import json
import csv
from pathlib import Path
from datetime import datetime

try:
    import praw
except ImportError:
    raise ImportError("praw is required to run this script. Install via `pip install praw`." )

SUBREDDITS = ["stocks", "wallstreetbets", "investing"]


def get_reddit_client():
    """Initialize and return a Reddit API client using environment variables."""
    return praw.Reddit(
        client_id="yu0XBAb1pEW3qcFycIhaRA",
        client_secret="TWYPa49aXuT0DyU2SpiE1HVtx-Otsw",
        user_agent=os.getenv("REDDIT_USER_AGENT", "reddit_scraper")
    )


def fetch_posts(reddit, limit=50):
    """Fetch recent posts and comments from predefined subreddits."""
    posts = []
    for name in SUBREDDITS:
        subreddit = reddit.subreddit(name)
        for submission in subreddit.new(limit=limit):
            submission.comments.replace_more(limit=0)
            comments = [
                {"text": c.body, "length": len(c.body)}
                for c in submission.comments.list()
            ]
            posts.append({
                "subreddit": name,
                "id": submission.id,
                "title": submission.title,
                "selftext": submission.selftext,
                "created_utc": submission.created_utc,
                "upvotes": submission.score,
                "author": str(submission.author),
                "num_comments": submission.num_comments,
                "comments": comments,
            })
    return posts


def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_csv(data, path):
    fields = [
        "subreddit",
        "id",
        "title",
        "selftext",
        "created_utc",
        "upvotes",
        "author",
        "num_comments",
    ]
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for post in data:
            row = {k: post.get(k) for k in fields}
            writer.writerow(row)


def main():
    reddit = get_reddit_client()
    posts = fetch_posts(reddit, limit=50)

    root_dir = Path(__file__).resolve().parents[1]
    today = datetime.utcnow().strftime("%Y-%m-%d")
    out_dir = root_dir / "data" / "reddit" / today
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%H%M%S")
    json_path = out_dir / f"reddit_{timestamp}.json"
    csv_path = out_dir / f"reddit_{timestamp}.csv"

    save_json(posts, json_path)
    save_csv(posts, csv_path)
    print(f"Saved {len(posts)} posts to {json_path} and {csv_path}")


if __name__ == "__main__":
    main()

# InsiderNet

This project contains example scripts for scraping public finance data from Twitter/X, Reddit, the SEC EDGAR feed, Google Trends, and historical stock prices.  See the `notebooks/` directory for runnable scripts.

Data collected by the scripts is stored by date under the `data/` folder.  Each run outputs timestamped JSON and CSV files for reproducibility.

## Requirements
- Python 3.11 or compatible
- [`tweepy`](https://www.tweepy.org/)
- [`praw`](https://praw.readthedocs.io/en/latest/)
- [`feedparser`](https://pypi.org/project/feedparser/), `requests`, `beautifulsoup4`
- [`pytrends`](https://github.com/GeneralMills/pytrends)
- [`yfinance`](https://pypi.org/project/yfinance/)

Set the `TWITTER_BEARER_TOKEN` environment variable as well as the Reddit API credentials before running the scripts.

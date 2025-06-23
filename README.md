# InsiderNet

This project contains example scripts for scraping public finance data from Twitter/X, Reddit, the SEC EDGAR feed, Google Trends, and historical stock prices.  See the `notebooks/` directory for runnable scripts.

Data collected by the scripts is stored by date under the `data/` folder.  Each run outputs timestamped JSON and CSV files for reproducibility.

The `webapp/` directory includes a small Flask application with a Tailwind front end. It accepts a ticker symbol, expands Reddit search keywords using OpenAI, gathers data from Reddit, the SEC, Google Trends and Yahoo Finance, and saves both raw prices and labeled datasets. Labels are generated using the realtime `labels.py` logic as well as `labels_from_prices.py` on the stored prices.

## Requirements
- Python 3.11 or compatible
- [`tweepy`](https://www.tweepy.org/)
- [`praw`](https://praw.readthedocs.io/en/latest/)
- [`feedparser`](https://pypi.org/project/feedparser/), `requests`, `beautifulsoup4`
- [`pytrends`](https://github.com/GeneralMills/pytrends)
- [`yfinance`](https://pypi.org/project/yfinance/)
- [`openai`](https://pypi.org/project/openai/) for keyword generation
- [`flask`](https://flask.palletsprojects.com/) for the optional web front end

Set the `TWITTER_BEARER_TOKEN` environment variable as well as the Reddit API credentials before running the scripts.

The `labels_from_prices.py` script generates future price-change labels using price data collected by `historical_prices.py`.

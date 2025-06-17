# InsiderNet

This project contains example scripts for scraping public finance data from Twitter/X and Reddit.  See the `notebooks/` directory for runnable scripts.

Data collected by the scripts is stored by date under the `data/` folder.  Each run outputs timestamped JSON and CSV files for reproducibility.

## Requirements
- Python 3.11 or compatible
- [`tweepy`](https://www.tweepy.org/)
- [`praw`](https://praw.readthedocs.io/en/latest/)

Set the `TWITTER_BEARER_TOKEN` environment variable as well as the Reddit API credentials before running the scripts.

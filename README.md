# InsiderNet

This project contains example scripts for scraping public finance data from Twitter/X and Reddit.  See the `notebooks/` directory for runnable scripts.

Data collected by the scripts is stored by date under the `data/` folder.  Each run outputs timestamped JSON and CSV files for reproducibility.

## Requirements
- Python 3.11 or compatible
- [`snscrape`](https://github.com/JustAnotherArchivist/snscrape)
- [`praw`](https://praw.readthedocs.io/en/latest/)

`snscrape` has limited support for Python 3.12.  If you see an import error, upgrade the package (`pip install -U snscrape`) or run the script with Python 3.11.

import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from textblob import TextBlob

import pandas_ta as ta

def compute_price_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['daily_return'] = df['close'].pct_change()
    df['price_change_pct'] = (df['close'] - df['open']) / df['open']
    df['moving_avg_5'] = df['close'].rolling(window=5).mean()
    df['rolling_std_3'] = df['close'].rolling(window=3).std()
    df['volume_change'] = df['volume'].pct_change()
    df['volatility_spike'] = (df['volatility'] > df['volatility'].rolling(5).mean()).astype(int)
    df['gap_up'] = (df['open'] > df['close'].shift(1)).astype(int)
    df['gap_down'] = (df['open'] < df['close'].shift(1)).astype(int)

    # 🆕 RSI
    df['rsi_14'] = ta.rsi(df['close'], length=14)

    # 🆕 MACD, Signal, Histogram
    macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
    df['macd'] = macd['MACD_12_26_9']
    df['macd_signal'] = macd['MACDs_12_26_9']
    df['macd_hist'] = macd['MACDh_12_26_9']

    # 🆕 Bollinger Bands
    bb = ta.bbands(df['close'], length=20, std=2)
    df['bollinger_high'] = bb['BBU_20_2.0']
    df['bollinger_low'] = bb['BBL_20_2.0']
    df['bollinger_bandwidth'] = (df['bollinger_high'] - df['bollinger_low']) / df['close'].rolling(20).mean()

    df = df.dropna().reset_index(drop=True)
    return df


def compute_reddit_features(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["date", "reddit_mentions", "avg_upvotes", "avg_comments", "avg_sentiment", "sentiment_std"])

    df["date"] = pd.to_datetime(df["created_utc"], unit="s").dt.date
    df["sentiment"] = df["title"].fillna("").apply(lambda x: TextBlob(x).sentiment.polarity)

    grouped = df.groupby("date").agg(
        reddit_mentions=("id", "count"),
        avg_upvotes=("score", "mean"),
        avg_comments=("num_comments", "mean"),
        avg_sentiment=("sentiment", "mean"),
        sentiment_std=("sentiment", "std")
    ).reset_index()

    grouped["date"] = grouped["date"].astype(str)
    grouped = grouped.fillna(0)
    return grouped

def compute_trend_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["trend_momentum"] = df["interest"].diff()
    df["interest_spike"] = (df["interest"] > df["interest"].rolling(window=5).mean()).astype(int)
    df = df.dropna().reset_index(drop=True)
    df["date"] = df["date"].astype(str)
    return df

def compute_time_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["day_of_week"] = df["date"].dt.dayofweek
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    df["month"] = df["date"].dt.month
    df["date"] = df["date"].dt.date.astype(str)
    return df[["date", "day_of_week", "is_weekend", "month"]]



# Optional: Function to merge all into master feature set
def merge_all_features(price_df, reddit_df, trends_df):
    price = compute_price_features(price_df)
    reddit = compute_reddit_features(reddit_df)
    trends = compute_trend_features(trends_df)
    time = compute_time_features(price)

    # Merge all on "date"
    merged = price.merge(reddit, how="left", on="date")
    merged = merged.merge(trends, how="left", on="date")
    merged = merged.merge(time, how="left", on="date")

    # Fill missing values
    merged = merged.fillna(0)
    return merged

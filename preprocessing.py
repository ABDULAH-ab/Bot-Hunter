from dotenv import load_dotenv
load_dotenv()

import os
import json
import numpy as np
from pymongo import MongoClient
from datetime import datetime
import pandas as pd
import math
from datetime import datetime, timezone


class TweetPreprocessor:
    def __init__(self):
        """
        Connect to MongoDB and load the Tweets collection.
        """
        MONGO_URI = os.getenv("MONGO_URI")
        if not MONGO_URI:
            raise ValueError("MONGO_URI missing in environment")

        self.client = MongoClient(MONGO_URI)
        self.db = self.client["Tweets"]
        self.col = self.db["Tweets"]

        print("Connected to DB:", self.db.name)

    # ---------------------------
    # BASIC CLEANING UTILITIES
    # ---------------------------

    def safe_list(self, v):
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return []

    def safe_int(self, v):
        try:
            return int(v)
        except:
            return 0

    def safe_str(self, v):
        if v is None:
            return ""
        return str(v).strip()

    def parse_datetime(self, v):
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        except:
            return None

    def entropy(self, text):
        """
        Shannon entropy for text complexity.
        """
        if not text:
            return 0
        counts = {}
        for ch in text:
            counts[ch] = counts.get(ch, 0) + 1
        length = len(text)
        probs = [c / length for c in counts.values()]
        return -sum(p * math.log(p) for p in probs)

    def to_int(self, value):
        try:
            return int(value)
        except:
            return 0

    def safe_ratio(self, a, b):
        try:
            return a / b if b not in (0, None) else None
        except:
            return None


    # ------------------------------
    # FEATURE ENGINEERING PER TWEET
    # ------------------------------

    from datetime import datetime, timezone

    def engineer_features(self, tweet):
        """Create numeric/boolean features for ML/Bot detection."""

    # --- Timestamp handling (always UTC-aware) ---
        raw_ts = tweet.get("timestamp")
        timestamp = None
        if raw_ts:
            try:
                cleaned_ts = raw_ts.replace("Z", "+00:00")
                timestamp = datetime.fromisoformat(cleaned_ts)
            except:
                timestamp = None

        now = datetime.now(timezone.utc)

        tweet_age = (now - timestamp).days if timestamp else None

    # --- Convert numeric fields safely ---
        followers = self.to_int(tweet.get("followers_count", 0))
        following = self.to_int(tweet.get("following_count", 0))

    # --- Text and metadata features ---
        text = tweet.get("text", "")

        features = {
            "tweet_length": len(text),
            "hashtag_count": len(tweet.get("hashtags", [])),
            "mention_count": len(tweet.get("mentions", [])),
            "url_count": len(tweet.get("urls", [])),
            "is_verified": 1 if tweet.get("verified", False) else 0,

            "followers": followers,
            "following": following,
            "followers_to_following_ratio": self.safe_ratio(followers, following),

            "tweet_age_days": tweet_age,

            "retweet_count": self.to_int(tweet.get("retweet_count", 0)),
            "reply_count": self.to_int(tweet.get("reply_count", 0)),
            "quote_count": self.to_int(tweet.get("quote_count", 0)),
            "like_count": self.to_int(tweet.get("like_count", 0)),
        }

        tweet["features"] = features
        return tweet

    # ------------------------------------------
    # MAIN PIPELINE: CLEAN, NORMALIZE, ENGINEER
    # ------------------------------------------

    def process_all(self, save_to_mongo=False):
        """
        Process all tweets in the database and return a DataFrame.
        Optionally save processed results into a new collection.
        """

        print("Fetching tweets from DB...")
        tweets = list(self.col.find({}, {"_id": 0}))
        print("Fetched all Tweets!")

        processed = []
        for t in tweets:
            processed.append(self.engineer_features(t))

        df = pd.DataFrame(processed)
        print("Processed", len(df), "tweets")

        # Save locally
        df.to_csv("processed_tweets.csv", index=False)
        df.to_json("processed_tweets.json", orient="records")

        print("Saved processed features to CSV and JSON")

        # Optional: Store in new MongoDB collection
        if save_to_mongo:
            print("Saving to MongoDB collection: ProcessedTweets")
            out_col = self.db["ProcessedTweets"]
            out_col.delete_many({})  # clean existing
            out_col.insert_many(processed)
            print("Saved processed data to MongoDB")

        return df


def main():
    processor = TweetPreprocessor()
    processor.process_all(save_to_mongo=True)


if __name__ == "__main__":
    main()

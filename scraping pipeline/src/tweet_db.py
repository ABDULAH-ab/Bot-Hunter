from dotenv import load_dotenv
load_dotenv()

import os
import json
from pymongo import MongoClient, UpdateOne
from datetime import datetime


class TweetDB:
    def __init__(self):
        """
        Initialize the MongoDB connection.
        """
        self.MONGO_URI = os.getenv("MONGO_URI")

        if not self.MONGO_URI:
            raise ValueError("MONGO_URI not found in .env file")

        try:
            self.client = MongoClient(self.MONGO_URI)
            self.client.server_info()  # force connection check
            print("Connected to MongoDB")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to MongoDB: {e}")

        # Database and collection
        self.db = self.client["Tweets"]
        self.col = self.db["Tweets"]

        # Create unique index for tweet_id (prevents duplicates)
        self.col.create_index("tweet_id", unique=True)
        print("Using database:", self.db.name)
        print("Collection:", self.col.name)

    # Normalize a single tweet
    def normalize_tweet(self, tweet, scraped_date):
        def to_list(value):
            if isinstance(value, str):
                return [v.strip() for v in value.split(",") if v.strip()]
            return value

        tweet["hashtags"] = to_list(tweet.get("hashtags", ""))
        tweet["mentions"] = to_list(tweet.get("mentions", ""))
        tweet["urls"]     = to_list(tweet.get("urls", ""))

        # Add scraping date
        tweet["scraped_on"] = scraped_date
        return tweet

    # Save JSON file to MongoDB
    def save_json(self, json_path):
        """
        Reads a JSON file of tweets and inserts/updates them in MongoDB.
        """

        if not os.path.exists(json_path):
            print(f"File not found: {json_path}")
            return

        scraped_date = os.path.basename(json_path).replace("tweets_", "").replace(".json", "")

        with open(json_path, "r", encoding="utf-8") as f:
            tweets = json.load(f)

        ops = []
        for tweet in tweets:
            tweet_norm = self.normalize_tweet(tweet, scraped_date)

        
            # PREVENT DUPLICATES – only insert if tweet does not exist
            ops.append(
                UpdateOne(
                    {"tweet_id": tweet_norm["tweet_id"]},   # filter
                    {"$setOnInsert": tweet_norm},           # insert only if new
                    upsert=True
                )
            )

        if ops:
            result = self.col.bulk_write(ops)
            print(f"Processed {len(ops)} tweets")
            print(f"Inserted: {result.upserted_count}")
            print(f"Skipped duplicates (already existed): {len(ops) - result.upserted_count}")

        return True

def main():

        db=TweetDB()
        db.save_json("data/tweets_2025-12-08.json")

        

if __name__ == "__main__":
    main()

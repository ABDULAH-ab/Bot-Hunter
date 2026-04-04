from dotenv import load_dotenv
load_dotenv()

import os
import json
from pymongo import MongoClient, UpdateOne


class TweetDB:
    def __init__(self):
        """Initialize MongoDB connection and collections."""
        self.MONGO_URI = os.getenv("MONGO_URI")

        if not self.MONGO_URI:
            raise ValueError("MONGO_URI not found in .env file")

        try:
            self.client = MongoClient(self.MONGO_URI)
            self.client.server_info()  # force connection check
            print("Connected to MongoDB")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to MongoDB: {e}")

        # Database and collections
        self.db = self.client["Tweets"]
        self.raw_col = self.db["Raw"]
        self.user_cache_col = self.db["User_Cache"]

        # Indexes to prevent duplicates.
        self.raw_col.create_index("tweet_id", unique=True)
        self.user_cache_col.create_index("username", unique=True)
        print("Using database:", self.db.name)
        print("Collections:", self.raw_col.name, ",", self.user_cache_col.name)

    def normalize_tweet(self, tweet, scraped_date):
        """Normalize tweet document before MongoDB upsert."""
        def to_list(value):
            if isinstance(value, str):
                return [v.strip() for v in value.split(",") if v.strip()]
            if value is None:
                return []
            return value if isinstance(value, list) else [value]

        tweet_doc = dict(tweet)
        tweet_doc["hashtags"] = to_list(tweet_doc.get("hashtags", ""))
        tweet_doc["mentions"] = to_list(tweet_doc.get("mentions", ""))
        tweet_doc["urls"] = to_list(tweet_doc.get("urls", ""))
        tweet_doc["scraped_on"] = scraped_date
        return tweet_doc

    def upsert_tweets(self, tweets, scraped_date):
        """Insert new tweets into Tweets.Raw and skip existing tweet_id duplicates."""
        ops = []
        for tweet in tweets:
            tweet_id = tweet.get("tweet_id")
            if not tweet_id:
                continue

            tweet_norm = self.normalize_tweet(tweet, scraped_date)
            ops.append(
                UpdateOne(
                    {"tweet_id": tweet_id},
                    {"$setOnInsert": tweet_norm},
                    upsert=True,
                )
            )

        if not ops:
            print("No valid tweets to upsert into Tweets.Raw")
            return {"processed": 0, "inserted": 0, "skipped": 0}

        result = self.raw_col.bulk_write(ops, ordered=False)
        inserted = result.upserted_count
        processed = len(ops)
        skipped = processed - inserted

        print(f"[Tweets.Raw] Processed: {processed}")
        print(f"[Tweets.Raw] Inserted: {inserted}")
        print(f"[Tweets.Raw] Skipped duplicates: {skipped}")

        return {"processed": processed, "inserted": inserted, "skipped": skipped}

    def upsert_user_cache(self, user_cache, scraped_date, insert_only=False):
        """Upsert user profiles into Tweets.User_Cache keyed by username."""
        if not user_cache:
            print("No user profiles to upsert into Tweets.User_Cache")
            return {"processed": 0, "upserted": 0, "modified": 0}

        if isinstance(user_cache, dict):
            profiles = []
            for username, profile in user_cache.items():
                doc = dict(profile) if isinstance(profile, dict) else {"username": username}
                doc.setdefault("username", username)
                profiles.append(doc)
        elif isinstance(user_cache, list):
            profiles = [dict(p) for p in user_cache if isinstance(p, dict)]
        else:
            profiles = []

        ops = []
        for profile in profiles:
            username = profile.get("username")
            if not username:
                continue

            profile_doc = dict(profile)
            profile_doc["last_seen_scraped_on"] = scraped_date

            if insert_only:
                ops.append(
                    UpdateOne(
                        {"username": username},
                        {"$setOnInsert": profile_doc},
                        upsert=True,
                    )
                )
            else:
                ops.append(
                    UpdateOne(
                        {"username": username},
                        {"$set": profile_doc},
                        upsert=True,
                    )
                )

        if not ops:
            print("No valid user profiles to upsert into Tweets.User_Cache")
            return {"processed": 0, "upserted": 0, "modified": 0}

        result = self.user_cache_col.bulk_write(ops, ordered=False)
        processed = len(ops)
        upserted = result.upserted_count
        modified = result.modified_count
        skipped = processed - upserted if insert_only else 0

        print(f"[Tweets.User_Cache] Processed: {processed}")
        print(f"[Tweets.User_Cache] Upserted: {upserted}")
        print(f"[Tweets.User_Cache] Modified: {modified}")
        if insert_only:
            print(f"[Tweets.User_Cache] Skipped existing users: {skipped}")

        return {
            "processed": processed,
            "upserted": upserted,
            "modified": modified,
            "skipped": skipped,
        }

    def save_json(self, json_path):
        """Read scraped JSON and save tweets and users into MongoDB collections."""

        if not os.path.exists(json_path):
            print(f"File not found: {json_path}")
            return False

        scraped_date = os.path.basename(json_path).replace("tweets_", "").replace(".json", "")

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        tweets = data.get("tweets", data) if isinstance(data, dict) else data
        if not isinstance(tweets, list):
            print("Invalid JSON format: expected a list or {'tweets': [...]} structure")
            return False

        self.upsert_tweets(tweets, scraped_date)

        # Build a lightweight user cache snapshot from tweets for User_Cache collection.
        by_user = {}
        for tweet in tweets:
            username = tweet.get("username")
            if not username:
                continue
            if username not in by_user:
                by_user[username] = {
                    "username": username,
                    "user_id": tweet.get("user_id", username),
                    "bio": tweet.get("bio", ""),
                    "location": tweet.get("location", ""),
                    "user_created_at": tweet.get("user_created_at", ""),
                    "account_creation_date": tweet.get("account_creation_date", tweet.get("user_created_at", "")),
                    "followers_count": tweet.get("followers_count", 0),
                    "following_count": tweet.get("following_count", 0),
                    "tweet_count": tweet.get("tweet_count", 0),
                    "listed_count": tweet.get("listed_count", 0),
                    "verified": tweet.get("verified", False),
                    "default_profile_image": tweet.get("default_profile_image", False),
                }

        self.upsert_user_cache(by_user, scraped_date, insert_only=True)

        return True


def main():
    db = TweetDB()
    db.save_json("data/tweets_2025-12-08.json")

if __name__ == "__main__":
    main()
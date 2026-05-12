from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from dotenv import load_dotenv
import os
from datetime import datetime
from typing import Optional

# SSL certificate handling for production (Amazon Linux / OpenSSL 3.x)
try:
    import certifi
    MONGO_TLS_OPTS = {"tlsCAFile": certifi.where()}
except ImportError:
    MONGO_TLS_OPTS = {"tlsAllowInvalidCertificates": True}

# Load environment variables
load_dotenv()

# MongoDB connection strings from environment variables
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "bot_hunter")

# Scrape data MongoDB cluster (separate)
MONGODB_SCRAPE_URL = os.getenv("MONGODB_SCRAPE_URL", "mongodb://localhost:27017/")
SCRAPE_DATABASE_NAME = os.getenv("SCRAPE_DATABASE_NAME", "scrape_data")

# Global MongoDB clients
_client: Optional[MongoClient] = None
_db = None
_scrape_client: Optional[MongoClient] = None
_scrape_db = None

def get_database():
    """Get MongoDB database instance for web app (users, auth, etc.)"""
    global _client, _db
    if _db is None:
        try:
            _client = MongoClient(MONGODB_URL, **MONGO_TLS_OPTS)
            _db = _client[DATABASE_NAME]
            # Test connection
            _client.admin.command('ping')
            print("Connected to MongoDB (web app cluster) successfully")
        except ConnectionFailure as e:
            print(f"Failed to connect to MongoDB (web app): {e}")
            raise
    return _db


def get_scrape_database():
    """Get MongoDB database instance for scrape data cluster"""
    global _scrape_client, _scrape_db
    if _scrape_db is None:
        try:
            _scrape_client = MongoClient(MONGODB_SCRAPE_URL, **MONGO_TLS_OPTS)
            _scrape_db = _scrape_client[SCRAPE_DATABASE_NAME]
            # Test connection
            _scrape_client.admin.command('ping')
            print("Connected to MongoDB (scrape data cluster) successfully")
        except ConnectionFailure as e:
            print(f"Failed to connect to MongoDB (scrape data): {e}")
            # Don't raise—allow app to start even if scrape cluster is unavailable
            return None
    return _scrape_db

def close_connection():
    """Close both MongoDB connections"""
    global _client, _scrape_client
    if _client:
        _client.close()
        print("MongoDB connection (web app) closed")
    if _scrape_client:
        _scrape_client.close()
        print("MongoDB connection (scrape data) closed")

def init_db():
    """Initialize database collections and indexes"""
    db = get_database()
    
    # Users collection
    users_collection = db.users
    
    # Create indexes for users collection
    users_collection.create_index("username", unique=True)
    users_collection.create_index("email", unique=True)
    
    # Tweets collection (for future use)
    tweets_collection = db.tweets
    tweets_collection.create_index("tweet_id", unique=True)
    tweets_collection.create_index("hashtag")
    
    # Hashtags collection (for future use)
    hashtags_collection = db.hashtags
    hashtags_collection.create_index("hashtag", unique=True)
    
    # Analysis results collection (for future use)
    analysis_collection = db.analysis_results
    analysis_collection.create_index("hashtag")
    analysis_collection.create_index("analyzed_at")
    
    print("Database collections initialized successfully")

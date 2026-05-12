from fastapi import APIRouter, HTTPException, Query
from database import get_database, get_scrape_database
from models import (
    HashtagAccountResult,
    HashtagScanResponse,
    HashtagSuggestionsResponse,
    ManualScanRequest,
    ManualScanResponse,
)
from bot_predictor import get_predictor
import re


router = APIRouter()


@router.post("/manual", response_model=ManualScanResponse)
async def manual_prediction(payload: ManualScanRequest):
    try:
        predictor = get_predictor()
        result = predictor.predict(payload)
        return ManualScanResponse(
            label=result.label,
            confidence=result.confidence,
            bot_probability=result.bot_probability,
            human_probability=result.human_probability,
            signals=result.signals,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}")


@router.get("/from-mongodb", response_model=ManualScanResponse)
async def predict_from_mongodb(
    username: str = Query(..., description="Username to query from MongoDB"),
    collection: str = Query("User_Cache", description="MongoDB collection name"),
    use_scrape_cluster: bool = Query(True, description="Use scrape data cluster (True) or web app cluster (False)"),
):
    """
    Query a user profile from MongoDB and run prediction on it.
    Supports collections like 'twitter_profiles', 'scraped_users', etc.
    
    Set use_scrape_cluster=True to query from MONGODB_SCRAPE_URL (default)
    Set use_scrape_cluster=False to query from MONGODB_URL (web app cluster)
    """
    try:
        # Choose which database to query
        if use_scrape_cluster:
            db = get_scrape_database()
            if db is None:
                raise HTTPException(status_code=503, detail="Scrape data cluster is unavailable")
        else:
            db = get_database()
        
        normalized_username = (username or "").strip().lstrip("@")
        if not normalized_username:
            raise HTTPException(status_code=400, detail="Username cannot be empty")

        # Query the collection for the user
        user_doc = db[collection].find_one({"username": normalized_username}) or db[collection].find_one({"screen_name": normalized_username})
        
        if not user_doc:
            raise HTTPException(status_code=404, detail=f"User '{normalized_username}' not found in collection '{collection}'")
        
        # Map MongoDB document to ManualScanRequest
        # Adjust field names based on your MongoDB schema
        payload = ManualScanRequest(
            username=user_doc.get("username") or user_doc.get("screen_name", normalized_username),
            display_name=user_doc.get("display_name") or user_doc.get("name", username),
            description=user_doc.get("description", ""),
            followers_count=int(user_doc.get("followers_count", 0)),
            following_count=int(user_doc.get("following_count", 0)) or int(user_doc.get("friends_count", 0)),
            tweet_count=int(user_doc.get("tweet_count", 0)) or int(user_doc.get("statuses_count", 0)),
            listed_count=int(user_doc.get("listed_count", 0)),
            created_year=int(user_doc.get("created_year", 2024)),
            verified=bool(user_doc.get("verified", False)),
            protected=bool(user_doc.get("protected", False)),
            has_location=bool(user_doc.get("location")),
            has_url=bool(user_doc.get("url")),
            default_profile_image=bool(user_doc.get("default_profile_image", True)),
            has_pinned_tweet=bool(user_doc.get("pinned_tweet_id")),
            sample_tweets=user_doc.get("tweets", []) or user_doc.get("tweet_texts", []),
        )
        
        predictor = get_predictor()
        result = predictor.predict(payload)
        
        return ManualScanResponse(
            label=result.label,
            confidence=result.confidence,
            bot_probability=result.bot_probability,
            human_probability=result.human_probability,
            signals=result.signals,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prediction from MongoDB failed: {exc}")


def _year_from_doc(doc: dict) -> int:
    for key in ["account_creation_date", "user_created_at", "created_at"]:
        value = doc.get(key)
        if isinstance(value, str) and len(value) >= 4 and value[:4].isdigit():
            return int(value[:4])
    return 2024


@router.get("/hashtag", response_model=HashtagScanResponse)
async def predict_hashtag_activity(
    tag: str = Query(..., description="Hashtag text (with or without #)"),
    max_accounts: int = Query(100, ge=1, le=500, description="Max unique accounts to analyze"),
    top_k: int = Query(10, ge=1, le=50, description="How many suspicious accounts to return"),
):
    """Aggregate account-level predictions for users participating in a hashtag."""
    try:
        db = get_scrape_database()
        if db is None:
            raise HTTPException(status_code=503, detail="Scrape data cluster is unavailable")

        clean_tag = tag.strip().lstrip("#")
        if not clean_tag:
            raise HTTPException(status_code=400, detail="Hashtag cannot be empty")

        scraped_collection = db["Scraped-data"]
        user_cache_collection = db["User_Cache"]

        escaped = re.escape(clean_tag)
        query = {
            "$or": [
                {"source_hashtag": {"$regex": f"^{escaped}$", "$options": "i"}},
                {"hashtags": {"$regex": f"^{escaped}$", "$options": "i"}},
            ]
        }

        tweet_docs = list(scraped_collection.find(query))
        if not tweet_docs:
            raise HTTPException(status_code=404, detail=f"No scraped data found for hashtag '{clean_tag}'")

        tweets_by_user = {}
        for doc in tweet_docs:
            username = (doc.get("username") or doc.get("user_id") or "").strip()
            if not username:
                continue
            if username not in tweets_by_user:
                tweets_by_user[username] = []
            text = (doc.get("text") or "").strip()
            if text:
                tweets_by_user[username].append(text)

        usernames = list(tweets_by_user.keys())[:max_accounts]
        if not usernames:
            raise HTTPException(status_code=404, detail="No valid user records found for this hashtag")

        user_docs = list(user_cache_collection.find({"username": {"$in": usernames}}))
        user_map = {str(doc.get("username")): doc for doc in user_docs}

        predictor = get_predictor()
        account_results = []
        for username in usernames:
            cache_doc = user_map.get(username, {})
            tweet_list = tweets_by_user.get(username, [])

            payload = ManualScanRequest(
                username=username,
                display_name=cache_doc.get("display_name") or cache_doc.get("name") or username,
                description=cache_doc.get("bio", ""),
                followers_count=int(cache_doc.get("followers_count", 0) or 0),
                following_count=int(cache_doc.get("following_count", 0) or 0),
                tweet_count=int(cache_doc.get("tweet_count", 0) or len(tweet_list)),
                listed_count=int(cache_doc.get("listed_count", 0) or 0),
                created_year=_year_from_doc(cache_doc),
                verified=bool(cache_doc.get("verified", False)),
                protected=bool(cache_doc.get("protected", False)),
                has_location=bool(cache_doc.get("location")),
                has_url=bool(cache_doc.get("urls")) or bool(cache_doc.get("url")),
                default_profile_image=bool(cache_doc.get("default_profile_image", True)),
                has_pinned_tweet=bool(cache_doc.get("pinned_tweet_id")),
                sample_tweets=tweet_list[:20],
            )

            result = predictor.predict(payload)
            account_results.append(
                HashtagAccountResult(
                    username=username,
                    label=result.label,
                    confidence=result.confidence,
                    bot_probability=result.bot_probability,
                    human_probability=result.human_probability,
                    signals=result.signals,
                    tweets_used=min(len(tweet_list), 20),
                )
            )

        bots_detected = sum(1 for x in account_results if x.label == "bot")
        humans_detected = sum(1 for x in account_results if x.label == "human")
        analyzed_accounts = len(account_results)
        bot_ratio = (bots_detected / analyzed_accounts) if analyzed_accounts else 0.0

        top_accounts = sorted(
            account_results,
            key=lambda x: (x.bot_probability, x.confidence),
            reverse=True,
        )[:top_k]

        return HashtagScanResponse(
            hashtag=clean_tag,
            total_tweets=len(tweet_docs),
            total_accounts=len(set(tweets_by_user.keys())),
            analyzed_accounts=analyzed_accounts,
            bots_detected=bots_detected,
            humans_detected=humans_detected,
            bot_ratio=bot_ratio,
            top_suspicious_accounts=top_accounts,
            note=(
                "Data is limited and differs from TwiBot-22 schema. Results should be treated as indicative, "
                "not a final benchmark."
            ),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Hashtag analysis failed: {exc}")


@router.get("/hashtag-suggestions", response_model=HashtagSuggestionsResponse)
async def get_hashtag_suggestions(
    limit: int = Query(8, ge=1, le=30, description="Number of random hashtag suggestions"),
):
    """Return random hashtags currently available in scrape DB for click-to-scan UX."""
    try:
        db = get_scrape_database()
        if db is None:
            raise HTTPException(status_code=503, detail="Scrape data cluster is unavailable")

        scraped_collection = db["Scraped-data"]

        pipeline = [
            {
                "$project": {
                    "tags": {
                        "$concatArrays": [
                            {
                                "$cond": [
                                    {
                                        "$and": [
                                            {"$ne": ["$source_hashtag", None]},
                                            {"$ne": ["$source_hashtag", ""]},
                                        ]
                                    },
                                    ["$source_hashtag"],
                                    [],
                                ]
                            },
                            {"$ifNull": ["$hashtags", []]},
                        ]
                    },
                    "scraped_on": 1,
                }
            },
            {"$unwind": "$tags"},
            {"$match": {"tags": {"$type": "string", "$ne": ""}}},
            {
                "$group": {
                    "_id": {"$toLower": "$tags"},
                    "tag": {"$first": "$tags"},
                    "tweets": {"$sum": 1},
                    "last_scraped": {"$max": "$scraped_on"},
                }
            },
            {"$sample": {"size": limit}},
            {
                "$project": {
                    "_id": 0,
                    "tag": "$tag",
                    "tweets": "$tweets",
                    "last_scraped": "$last_scraped",
                }
            },
        ]

        suggestions = list(scraped_collection.aggregate(pipeline))
        return HashtagSuggestionsResponse(suggestions=suggestions)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load hashtag suggestions: {exc}")
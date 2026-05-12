from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# User Models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str  # Can contain any characters, but must be <= 72 bytes

class UserLogin(BaseModel):
    username: str  # Can be username or email
    password: str

class UserResponse(BaseModel):
    id: str = Field(alias="_id")
    username: str
    email: str
    profile_picture: Optional[str] = None
    google_id: Optional[str] = None
    auth_provider: Optional[str] = None
    created_at: datetime
    is_active: bool = True
    is_admin: bool = False
    
    class Config:
        from_attributes = True
        populate_by_name = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None


class ManualScanRequest(BaseModel):
    username: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    followers_count: int = 0
    following_count: int = 0
    tweet_count: int = 0
    listed_count: int = 0
    created_year: int = 2024
    verified: bool = False
    protected: bool = False
    has_location: bool = False
    has_url: bool = False
    default_profile_image: bool = True
    has_pinned_tweet: bool = False
    sample_tweets: List[str] = Field(default_factory=list)


class ManualScanResponse(BaseModel):
    label: str
    confidence: float
    bot_probability: float
    human_probability: float
    signals: List[str] = Field(default_factory=list)


class HashtagAccountResult(BaseModel):
    username: str
    label: str
    confidence: float
    bot_probability: float
    human_probability: float
    signals: List[str] = Field(default_factory=list)
    tweets_used: int = 0


class HashtagScanResponse(BaseModel):
    hashtag: str
    total_tweets: int
    total_accounts: int
    analyzed_accounts: int
    bots_detected: int
    humans_detected: int
    bot_ratio: float
    top_suspicious_accounts: List[HashtagAccountResult] = Field(default_factory=list)
    note: str = "Hashtag-level detection is aggregated from account-level predictions."


class HashtagSuggestionItem(BaseModel):
    tag: str
    tweets: int = 0
    last_scraped: Optional[str] = None


class HashtagSuggestionsResponse(BaseModel):
    suggestions: List[HashtagSuggestionItem] = Field(default_factory=list)
    note: str = "Suggestions are sampled from hashtags currently present in the scrape database."

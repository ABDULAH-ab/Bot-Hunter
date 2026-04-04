# Twitter Data Collection Pipeline

Automated scraping pipeline for collecting trending hashtags and tweets from Twitter/X.

## 🎯 Features

- ✅ **Hashtag Scraper**: Collects top 5 trending US hashtags
- ✅ **Tweet Scraper**: Collects 2,000 tweets per hashtag (10k total/day)
- ✅ **Cookie-Based Auth**: Login once, reuse session (no repeated logins)
- ✅ **English-Only Filter**: Filters out non-English tweets
- ✅ **Twibot-22 Compatible**: CSV output ready for bot detection models
- ✅ **VPN Support**: Configure region via VPN
- ✅ **Comprehensive Logging**: Track every step

## 📁 Project Structure

```
scraping pipeline/
├── src/
│   ├── hashtag_scraper.py      # Scrapes trending hashtags
│   ├── tweet_scraper.py        # Scrapes tweets for hashtags
│   ├── scraping_pipeline.py    # Master pipeline (integrates both)
│   └── __init__.py
├── data/
│   ├── trending_hashtags.txt   # Output: trending hashtags
│   ├── tweets_YYYY-MM-DD.csv   # Output: scraped tweets
│   └── twitter_cookies.pkl     # Saved login session
├── logs/
│   ├── scraper.log             # Hashtag scraper logs
│   ├── tweet_scraper.log       # Tweet scraper logs
│   └── pipeline.log            # Master pipeline logs
├── .env                        # Configuration (credentials, settings)
├── requirements.txt            # Python dependencies
├── run_pipeline.py             # Quick launcher
└── README.md                   # This file
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file with your Twitter credentials:

```env
# Twitter/X Login Credentials
EMAIL=your_email@example.com
EMAIL_PASSWORD=your_email_password
USERNAME=your_twitter_username
PASSWORD=your_twitter_password

# Scraper Settings
HEADLESS_MODE=False
MAX_RETRIES=3
TWEETS_PER_HASHTAG=2000

# Scheduler (Optional - for automated daily runs)
SCHEDULE_TIME=02:00

# Target Region (use VPN to match this location)
REGION=United States
```

### 3. Connect VPN (Important!)

- Connect to a **US VPN server** to get US trending hashtags
- Keep VPN connected while running the scraper

### 4. Run Complete Pipeline

```bash
python run_pipeline.py
```

## 📝 What Happens

The pipeline executes in 2 steps:

### Step 1: Hashtag Scraping
1. Opens browser with undetected-chromedriver
2. Logs in to Twitter (first time only)
3. Scrapes top 5 US trending hashtags
4. Saves to `data/trending_hashtags.txt`
5. Saves cookies for future use

### Step 2: Tweet Scraping
1. Loads saved cookies (no login needed!)
2. Reads hashtags from file
3. For each hashtag:
   - Searches on Twitter
   - Scrolls and collects up to 2k English tweets
   - Extracts tweet data (text, engagement, user info)
4. Saves all tweets to `data/tweets_YYYY-MM-DD.csv`

## 📊 Output Format

### Hashtags File (`data/trending_hashtags.txt`)
```
# Trending Hashtags - 2025-10-19 23:45:12
# Total: 5

1. #Trending1
2. #Trending2
3. #Trending3
4. #Trending4
5. #Trending5
```

### Tweets CSV (`data/tweets_YYYY-MM-DD.csv`)

Twibot-22 compatible format with fields:

**Tweet Data:**
- `tweet_id`, `timestamp`, `text`, `retweet_count`, `like_count`, `reply_count`
- `quote_count`, `hashtags`, `mentions`, `urls`, `language`, `source_hashtag`

**User Data:**
- `user_id`, `username`, `display_name`, `bio`, `location`, `user_created_at`
- `followers_count`, `following_count`, `tweet_count`, `listed_count`, `verified`

## 🔧 Individual Scrapers

### Run Hashtag Scraper Only
```bash
python src/hashtag_scraper.py
```

### Run Tweet Scraper Only
```bash
# Requires hashtags file and cookies from hashtag scraper
python src/tweet_scraper.py
```

## ⚙️ Configuration Options

### Headless Mode
Run browser in background (no visible window):
```env
HEADLESS_MODE=True
```

### Adjust Tweet Limit
Change tweets per hashtag:
```env
TWEETS_PER_HASHTAG=1000  # Default: 2000
```

### Change Region
Update `.env` (remember to connect VPN to match):
```env
REGION=United Kingdom  # or Canada, Australia, etc.
```

## 🕒 Daily Automation (Scheduler)

### Run Once Daily Automatically

```bash
python scheduler.py
```

**What it does:**
- Runs the complete pipeline daily at your specified time (default: 2:00 AM local time)
- Keeps running in background
- Logs all executions

**Configure Schedule Time:**

Edit `.env` file:
```env
SCHEDULE_TIME=02:00    # 2 AM in YOUR LOCAL TIME (24-hour format)
```

**Examples:**
- `SCHEDULE_TIME=02:00` - Run at 2:00 AM
- `SCHEDULE_TIME=14:30` - Run at 2:30 PM
- `SCHEDULE_TIME=23:00` - Run at 11:00 PM

**Keep Scheduler Running:**
- Leave the terminal window open
- For production: Use Windows Service, systemd, or PM2

## 📋 Requirements

- Python 3.7+
- Chrome browser installed
- VPN (for US trends)
- Twitter/X account

## ⏱️ Expected Performance

- **Hashtag Scraping**: ~2-3 minutes
- **Tweet Scraping**: ~10-15 hours for 10k tweets
- **Total Pipeline**: ~10-15 hours (can run overnight)

## 🔒 Security Notes

- `.env` file is gitignored (never commit credentials)
- `twitter_cookies.pkl` is gitignored (session data)
- Use VPN to protect your IP
- Avoid running multiple times per day (rate limiting)

## 🐛 Troubleshooting

### "Cookie file not found"
- Run `python src/hashtag_scraper.py` first to login and save cookies

### "Cookies expired or invalid"
- Delete `data/twitter_cookies.pkl`
- Run hashtag scraper again to re-login

### "Wrong region trends"
- Check VPN is connected to correct region
- Delete cookies and re-run with VPN active

### Browser detection errors
- Update `undetected-chromedriver`: `pip install --upgrade undetected-chromedriver`

## 📊 Daily Usage

For daily data collection, run the pipeline once per day:

```bash
# Morning scrape (with VPN connected)
python run_pipeline.py
```

## 🤝 Contributing

This pipeline is designed for research and educational purposes. Use responsibly and ethically.

## 📄 License

MIT License - Use for research and educational purposes only.

---

**Note**: Always respect Twitter's Terms of Service and use this tool responsibly.



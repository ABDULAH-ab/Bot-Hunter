"""
Selenium-based tweet scraper for collecting tweets from trending hashtags
Uses undetected-chromedriver to bypass bot detection
Aligned with Twibot-22 dataset structure
"""

import os
import csv
import time
import random
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import pandas as pd
from langdetect import detect, LangDetectException
from dotenv import load_dotenv
from tweet_db import TweetDB 

# Load environment variables
load_dotenv()

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/tweet_scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Fix console encoding for Unicode characters (Windows)
import sys
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass


class SeleniumTweetScraper:
    """
    Tweet scraper using Selenium with undetected-chromedriver
    Reuses cookies from hashtag scraper - no repeated login!
    """
    
    def __init__(self):
        """Initialize the tweet scraper"""
        self.driver = None
        self.tweets_per_hashtag = int(os.getenv('TWEETS_PER_HASHTAG', 2000))
        self.headless = os.getenv('HEADLESS_MODE', 'False').lower() == 'true'
        self.cookies_file = 'data/twitter_cookies.pkl'
        
        logger.info(f"Tweet scraper initialized. Target: {self.tweets_per_hashtag} tweets per hashtag")
        logger.info(f"Headless mode: {self.headless}")
    
    def setup_driver(self):
        """
        Initialize Chrome WebDriver with undetected-chromedriver
        
        Returns:
            webdriver: Configured Chrome WebDriver instance
        """
        try:
            logger.info("Setting up Undetected Chrome WebDriver...")
            
            options = uc.ChromeOptions()
            
            if self.headless:
                options.add_argument('--headless=new')
                logger.info("Running in headless mode")
            
            # Additional options for stability
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            
            # Initialize undetected chromedriver
            self.driver = uc.Chrome(options=options, version_main=None)
            self.driver.maximize_window()
            
            logger.info("Undetected WebDriver setup successful")
            return self.driver
            
        except Exception as e:
            logger.error(f"Failed to setup WebDriver: {str(e)}")
            raise
    
    def load_cookies(self):
        """
        Load cookies from hashtag scraper (reuse existing session!)
        
        Returns:
            bool: True if cookies loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(self.cookies_file):
                logger.error(f"Cookie file not found: {self.cookies_file}")
                logger.error("Please run hashtag_scraper.py first to login and save cookies!")
                return False
            
            logger.info("Loading saved cookies from hashtag scraper...")
            
            # Navigate to Twitter first (required before adding cookies)
            self.driver.get('https://twitter.com')
            time.sleep(2)
            
            # Load and add cookies
            import pickle
            with open(self.cookies_file, 'rb') as file:
                cookies = pickle.load(file)
            
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    logger.warning(f"Could not add cookie: {str(e)}")
            
            logger.info("✓ Cookies loaded successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error loading cookies: {str(e)}")
            return False
    
    def is_logged_in(self):
        """
        Check if user is already logged in
        
        Returns:
            bool: True if logged in, False otherwise
        """
        try:
            self.driver.get('https://twitter.com/home')
            time.sleep(3)
            
            current_url = self.driver.current_url
            if 'home' in current_url:
                logger.info("✓ Already logged in via cookies!")
                return True
            else:
                logger.error("✗ Cookies expired or invalid")
                return False
                
        except Exception as e:
            logger.error(f"Error checking login status: {str(e)}")
            return False
    
    def is_english(self, text):
        """
        Check if text is in English
        
        Args:
            text (str): Text to check
            
        Returns:
            bool: True if English, False otherwise
        """
        try:
            if not text or len(text) < 3:
                return False
            return detect(text) == 'en'
        except LangDetectException:
            return False
    
    def extract_tweet_data(self, tweet_element):
        """
        Extract tweet data from a tweet element
        
        Args:
            tweet_element: Selenium WebElement of tweet
            
        Returns:
            dict: Tweet data dictionary or None
        """
        try:
            tweet_data = {}
            
            # Extract tweet text
            try:
                text_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
                tweet_data['text'] = text_element.text.strip()
            except:
                tweet_data['text'] = ''
            
            # Skip if no text or not English
            if not tweet_data['text'] or not self.is_english(tweet_data['text']):
                return None
            
            # Extract username
            try:
                user_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Name"]')
                # Username is in format @username
                username_spans = user_element.find_elements(By.TAG_NAME, 'span')
                for span in username_spans:
                    if span.text.startswith('@'):
                        tweet_data['username'] = span.text.replace('@', '')
                        break
                if 'username' not in tweet_data:
                    tweet_data['username'] = ''
            except:
                tweet_data['username'] = ''
            
            # Extract display name
            try:
                display_name_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Name"]')
                tweet_data['display_name'] = display_name_element.text.split('\n')[0]
            except:
                tweet_data['display_name'] = ''
            
            # Extract timestamp/tweet link (contains tweet ID)
            try:
                time_element = tweet_element.find_element(By.TAG_NAME, 'time')
                tweet_data['timestamp'] = time_element.get_attribute('datetime')
                
                # Get tweet ID from link
                link_element = time_element.find_element(By.XPATH, '..')
                tweet_url = link_element.get_attribute('href')
                if tweet_url:
                    tweet_data['tweet_id'] = tweet_url.split('/')[-1]
                else:
                    tweet_data['tweet_id'] = ''
            except:
                tweet_data['timestamp'] = ''
                tweet_data['tweet_id'] = ''
            
            # Extract engagement metrics (likes, retweets, replies)
            try:
                # Likes
                like_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="like"]')
                like_text = like_element.get_attribute('aria-label') or ''
                tweet_data['like_count'] = self.parse_count(like_text)
            except:
                tweet_data['like_count'] = 0
            
            try:
                # Retweets
                retweet_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="retweet"]')
                retweet_text = retweet_element.get_attribute('aria-label') or ''
                tweet_data['retweet_count'] = self.parse_count(retweet_text)
            except:
                tweet_data['retweet_count'] = 0
            
            try:
                # Replies
                reply_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="reply"]')
                reply_text = reply_element.get_attribute('aria-label') or ''
                tweet_data['reply_count'] = self.parse_count(reply_text)
            except:
                tweet_data['reply_count'] = 0
            
            # Extract hashtags and mentions from text
            tweet_data['hashtags'] = ','.join([word[1:] for word in tweet_data['text'].split() if word.startswith('#')])
            tweet_data['mentions'] = ','.join([word[1:] for word in tweet_data['text'].split() if word.startswith('@')])
            
            # Default values for fields we can't easily get
            tweet_data['quote_count'] = 0
            tweet_data['urls'] = ''
            tweet_data['language'] = 'en'
            tweet_data['user_id'] = tweet_data['username']
            tweet_data['bio'] = ''
            tweet_data['location'] = ''
            tweet_data['user_created_at'] = ''
            tweet_data['followers_count'] = 0
            tweet_data['following_count'] = 0
            tweet_data['tweet_count'] = 0
            tweet_data['listed_count'] = 0
            tweet_data['verified'] = False
            
            return tweet_data
            
        except Exception as e:
            logger.debug(f"Error extracting tweet data: {str(e)}")
            return None
    
    def parse_count(self, text):
        """
        Parse engagement count from text (e.g., "1.2K likes" -> 1200)
        
        Args:
            text (str): Text containing count
            
        Returns:
            int: Parsed count
        """
        try:
            # Extract numbers from text
            import re
            numbers = re.findall(r'[\d,\.]+[KMB]?', text)
            if not numbers:
                return 0
            
            num_str = numbers[0].replace(',', '')
            
            if 'K' in num_str:
                return int(float(num_str.replace('K', '')) * 1000)
            elif 'M' in num_str:
                return int(float(num_str.replace('M', '')) * 1000000)
            elif 'B' in num_str:
                return int(float(num_str.replace('B', '')) * 1000000000)
            else:
                return int(float(num_str))
        except:
            return 0
    
    def check_for_retry_button(self):
        """
        Check if Twitter shows a retry/rate limit button and handle it
        
        Returns:
            bool: True if retry button was found and clicked, False otherwise
        """
        try:
            # Look for retry button
            retry_buttons = self.driver.find_elements(By.XPATH, 
                "//*[contains(text(), 'Retry') or contains(text(), 'Try again')]")
            
            if retry_buttons:
                logger.warning("⚠ Retry button detected - Twitter rate limiting detected!")
                logger.info("Waiting 30 seconds before retrying...")
                time.sleep(30)
                
                # Click retry button
                retry_buttons[0].click()
                logger.info("✓ Clicked retry button, waiting for page to load...")
                time.sleep(random.uniform(5, 8))
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Error checking retry button: {str(e)}")
            return False
    
    def scrape_tweets_for_hashtag(self, hashtag, max_tweets=2000):
        """
        Scrape tweets for a specific hashtag
        
        Args:
            hashtag (str): Hashtag to scrape
            max_tweets (int): Maximum number of tweets to collect
            
        Returns:
            list: List of tweet data dictionaries
        """
        try:
            logger.info(f"="*50)
            logger.info(f"Scraping tweets for hashtag: {hashtag}")
            logger.info(f"="*50)
            
            # Clean hashtag for search
            search_query = hashtag if hashtag.startswith('#') else f"#{hashtag}"
            search_url = f"https://twitter.com/search?q={search_query.replace('#', '%23')}&src=typed_query&f=live"
            
            logger.info(f"Navigating to search: {search_query}")
            self.driver.get(search_url)
            
            # Wait longer for initial page load
            initial_wait = random.uniform(5, 8)
            logger.info(f"Waiting {initial_wait:.1f}s for page to load...")
            time.sleep(initial_wait)
            
            # Check for retry button immediately
            self.check_for_retry_button()
            
            tweets_data = []
            seen_tweet_ids = set()
            scroll_attempts = 0
            max_scroll_attempts = 150  # Increased from 100 to 150
            no_new_tweets_count = 0
            max_no_new_tweets = 8  # Increased from 5 to 8 (even more patient)
            consecutive_errors = 0
            max_consecutive_errors = 3
            
            while len(tweets_data) < max_tweets and scroll_attempts < max_scroll_attempts:
                try:
                    # Check for retry button periodically
                    if scroll_attempts % 10 == 0 and scroll_attempts > 0:
                        self.check_for_retry_button()
                    
                    # Find all tweet elements
                    tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
                    
                    # If no tweets found, check for retry button
                    if len(tweet_elements) == 0:
                        logger.warning("No tweets found on page, checking for issues...")
                        if self.check_for_retry_button():
                            continue
                    
                    logger.info(f"Found {len(tweet_elements)} tweet elements on page, collected {len(tweets_data)}/{max_tweets} tweets")
                    
                    initial_count = len(tweets_data)
                    
                    # Extract data from each tweet
                    for tweet_element in tweet_elements:
                        if len(tweets_data) >= max_tweets:
                            break
                        
                        try:
                            tweet_data = self.extract_tweet_data(tweet_element)
                            
                            if tweet_data and tweet_data['tweet_id']:
                                # Avoid duplicates
                                if tweet_data['tweet_id'] not in seen_tweet_ids:
                                    tweet_data['source_hashtag'] = hashtag
                                    tweets_data.append(tweet_data)
                                    seen_tweet_ids.add(tweet_data['tweet_id'])
                                    
                                    if len(tweets_data) % 50 == 0:
                                        logger.info(f"✓ Collected {len(tweets_data)} English tweets")
                        
                        except StaleElementReferenceException:
                            continue
                        except Exception as e:
                            logger.debug(f"Error processing tweet: {str(e)}")
                            continue
                    
                    # Check if we got new tweets
                    if len(tweets_data) == initial_count:
                        no_new_tweets_count += 1
                        logger.info(f"No new tweets this scroll ({no_new_tweets_count}/{max_no_new_tweets})")
                        
                        # If stuck, try checking for retry button
                        if no_new_tweets_count == 3:
                            logger.info("Checking if page has issues...")
                            self.check_for_retry_button()
                        
                        if no_new_tweets_count >= max_no_new_tweets:
                            logger.info(f"No new tweets found after {max_no_new_tweets} scrolls, stopping for this hashtag")
                            break
                    else:
                        no_new_tweets_count = 0
                        consecutive_errors = 0  # Reset error count on success
                    
                    # Scroll down to load more tweets
                    if len(tweets_data) < max_tweets:
                        # Vary scroll amount to appear more human
                        scroll_amount = random.randint(500, 1000)
                        self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                        
                        # Increased wait time for slow loading pages - more human-like
                        wait_time = random.uniform(4, 8)  # Increased from 3-6 to 4-8 seconds
                        logger.info(f"Scrolling... waiting {wait_time:.1f}s for tweets to load")
                        time.sleep(wait_time)
                        scroll_attempts += 1
                    
                except Exception as e:
                    consecutive_errors += 1
                    logger.error(f"Error during scrolling (attempt {consecutive_errors}/{max_consecutive_errors}): {str(e)}")
                    
                    # Check for retry button on errors
                    self.check_for_retry_button()
                    
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error("Too many consecutive errors, stopping for this hashtag")
                        break
                    
                    scroll_attempts += 1
                    time.sleep(5)
            
            logger.info(f"✓ Successfully collected {len(tweets_data)} English tweets for {hashtag}")
            return tweets_data
            
        except Exception as e:
            logger.error(f"Error scraping tweets for {hashtag}: {str(e)}")
            return []
    
    def read_hashtags(self, filepath='data/trending_hashtags.txt'):
        """
        Read hashtags from file
        
        Args:
            filepath (str): Path to hashtags file
            
        Returns:
            list: List of hashtags
        """
        try:
            hashtags = []
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if line and not line.startswith('#'):
                        # Extract hashtag (remove numbering like "1. ")
                        if '. ' in line:
                            hashtag = line.split('. ', 1)[1]
                        else:
                            hashtag = line
                        hashtags.append(hashtag)
            
            logger.info(f"Read {len(hashtags)} hashtags from {filepath}")
            return hashtags
            
        except Exception as e:
            logger.error(f"Error reading hashtags: {str(e)}")
            return []
    
    def save_to_csv(self, tweets_data, output_file):
        """
        Save tweets data to CSV file in Twibot-22 format
        
        Args:
            tweets_data (list): List of tweet dictionaries
            output_file (str): Output CSV file path
        """
        try:
            if not tweets_data:
                logger.warning("No tweets to save")
                return
            
            # Create output directory if doesn't exist
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            
            # Define CSV fields (Twibot-22 compatible)
            fieldnames = [
                'tweet_id', 'timestamp', 'text', 'retweet_count', 'like_count', 
                'reply_count', 'quote_count', 'hashtags', 'mentions', 'urls', 
                'language', 'source_hashtag',
                'user_id', 'username', 'display_name', 'bio', 'location', 
                'user_created_at', 'followers_count', 'following_count', 
                'tweet_count', 'listed_count', 'verified'
            ]
            
            # Write to CSV
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(tweets_data)
            
            logger.info(f"✓ Saved {len(tweets_data)} tweets to {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")
    
    def scrape_all_hashtags(self):
        """
        Main method to scrape tweets for all hashtags
        
        Returns:
            str: Path to output CSV file
        """
        try:
            # Setup driver
            self.setup_driver()
            
            # Load cookies (reuse from hashtag scraper!)
            if not self.load_cookies():
                raise Exception("Could not load cookies. Please run hashtag_scraper.py first!")
            
            # Verify login
            if not self.is_logged_in():
                raise Exception("Not logged in. Cookies may have expired. Run hashtag_scraper.py again.")
            
            # Read hashtags
            hashtags = self.read_hashtags()
            
            if not hashtags:
                raise Exception("No hashtags found to scrape")
            
            # Collect all tweets
            all_tweets = []
            
            for idx, hashtag in enumerate(hashtags, 1):
                logger.info("")
                logger.info(f"█ Processing hashtag {idx}/{len(hashtags)}: {hashtag}")
                
                tweets = self.scrape_tweets_for_hashtag(hashtag, self.tweets_per_hashtag)
                all_tweets.extend(tweets)
                
                logger.info(f"Total tweets collected so far: {len(all_tweets)}")
                
                # Longer delay between hashtags to avoid rate limiting
                if idx < len(hashtags):
                    # Random delay between 60-120 seconds (1-2 minutes)
                    wait_time = random.uniform(60, 120)
                    logger.info(f"⏸ Waiting {int(wait_time)} seconds before next hashtag (rate limit prevention)...")
                    logger.info(f"   You can safely minimize this window. Next hashtag starts at: {datetime.now() + timedelta(seconds=wait_time)}")
                    time.sleep(wait_time)
            
            # Generate output filename with timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d')
            output_file = f"data/tweets_{timestamp}.json"

            # Save to JSON
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(all_tweets, f, ensure_ascii=False, indent=4)

            logger.info(f"Saved {len(all_tweets)} tweets to {output_file}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"Error in scraping process: {str(e)}")
            raise
        
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("WebDriver closed")


def main():
    """Main execution function"""
    logger.info("="*50)
    logger.info("Starting Tweet Scraper (Selenium)")
    logger.info("="*50)
   
    
    try:
        scraper = SeleniumTweetScraper()
        output_file = scraper.scrape_all_hashtags()
        
        logger.info("="*50)
        logger.info("Tweet scraping completed successfully!")
        logger.info(f"Data saved to: {output_file}")
        logger.info("="*50)

        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise


if __name__ == "__main__":
    main()

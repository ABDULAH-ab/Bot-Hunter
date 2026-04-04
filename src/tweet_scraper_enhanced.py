# import os
# import json
# import time
# import random
# import logging
# import re
# from datetime import datetime, timedelta
# from pathlib import Path
# import undetected_chromedriver as uc
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
# import pandas as pd
# from langdetect import detect, LangDetectException
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()

# # Configure logging with UTF-8 encoding
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler('logs/tweet_scraper_enhanced.log', encoding='utf-8'),
#         logging.StreamHandler()
#     ]
# )
# logger = logging.getLogger(__name__)

# # Fix console encoding for Unicode characters (Windows)
# import sys
# if sys.platform == 'win32':
#     try:
#         sys.stdout.reconfigure(encoding='utf-8')
#     except:
#         pass


# class EnhancedTweetScraper:
#     """
#     ENHANCED tweet scraper with complete user profile extraction
#     Collects ALL data needed for bot detection research
#     """
    
#     def __init__(self):
#         """Initialize the enhanced tweet scraper"""
#         self.driver = None
#         self.tweets_per_hashtag = int(os.getenv('TWEETS_PER_HASHTAG', 2000))
#         self.headless = os.getenv('HEADLESS_MODE', 'False').lower() == 'true'
#         self.cookies_file = 'data/twitter_cookies.pkl'
        
#         # NEW: User profile cache to avoid repeated visits
#         self.user_cache = {}
#         self.users_scraped = 0
#         self.max_tweets_per_user = 50  # NEW: Limit tweets per user for diversity
#         self.user_tweet_count = {}  # NEW: Track tweets per user
        
#         logger.info(f"Enhanced tweet scraper initialized. Target: {self.tweets_per_hashtag} tweets per hashtag")
#         logger.info(f"Headless mode: {self.headless}")
#         logger.info(f"✨ NEW: User profile extraction ENABLED")
#         logger.info(f"✨ NEW: Max {self.max_tweets_per_user} tweets per user for diversity")
    
#     def setup_driver(self):
#         """Initialize Chrome WebDriver with undetected-chromedriver"""
#         try:
#             logger.info("Setting up Undetected Chrome WebDriver...")
            
#             options = uc.ChromeOptions()
            
#             if self.headless:
#                 options.add_argument('--headless=new')
#                 logger.info("Running in headless mode")
            
#             options.add_argument('--no-sandbox')
#             options.add_argument('--disable-dev-shm-usage')
#             options.add_argument('--disable-gpu')
#             options.add_argument('--window-size=1920,1080')
            
#             self.driver = uc.Chrome(options=options)
#             self.driver.maximize_window()
            
#             logger.info("Undetected WebDriver setup successful")
#             return self.driver
            
#         except Exception as e:
#             logger.error(f"Failed to setup WebDriver: {str(e)}")
#             raise
    
#     def load_cookies(self):
#         """Load cookies from hashtag scraper (reuse existing session!)"""
#         try:
#             if not os.path.exists(self.cookies_file):
#                 logger.error(f"Cookie file not found: {self.cookies_file}")
#                 logger.error("Please run hashtag_scraper.py first to login and save cookies!")
#                 return False
            
#             logger.info("Loading saved cookies from hashtag scraper...")
            
#             self.driver.get('https://twitter.com')
#             time.sleep(2)
            
#             import pickle
#             with open(self.cookies_file, 'rb') as file:
#                 cookies = pickle.load(file)
            
#             for cookie in cookies:
#                 try:
#                     self.driver.add_cookie(cookie)
#                 except Exception as e:
#                     logger.warning(f"Could not add cookie: {str(e)}")
            
#             logger.info("✓ Cookies loaded successfully!")
#             return True
            
#         except Exception as e:
#             logger.error(f"Error loading cookies: {str(e)}")
#             return False
    
#     def is_logged_in(self):
#         """Check if user is already logged in"""
#         try:
#             self.driver.get('https://twitter.com/home')
#             time.sleep(3)
            
#             current_url = self.driver.current_url
#             if 'home' in current_url:
#                 logger.info("✓ Already logged in via cookies!")
#                 return True
#             else:
#                 logger.error("✗ Cookies expired or invalid")
#                 return False
                
#         except Exception as e:
#             logger.error(f"Error checking login status: {str(e)}")
#             return False
    
#     def is_english(self, text):
#         """Check if text is in English"""
#         try:
#             if not text or len(text) < 3:
#                 return False
#             return detect(text) == 'en'
#         except LangDetectException:
#             return False
    
#     def extract_user_profile(self, username):
#         """
#         NEW: Extract complete user profile data by visiting user page
        
#         Args:
#             username (str): Twitter username
            
#         Returns:
#             dict: Complete user profile data
#         """
#         try:
#             logger.info(f"   → Extracting profile for @{username}")
            
#             profile_url = f"https://twitter.com/{username}"
#             self.driver.get(profile_url)
            
#             # Random wait to appear human-like
#             time.sleep(random.uniform(2, 4))
            
#             user_data = {'username': username}
            
#             # Extract followers count
#             try:
#                 followers_link = self.driver.find_element(
#                     By.XPATH, "//a[contains(@href, '/verified_followers') or contains(@href, '/followers')]/span/span"
#                 )
#                 followers_text = followers_link.text
#                 user_data['followers_count'] = self.parse_count_text(followers_text)
#                 logger.debug(f"     Followers: {user_data['followers_count']}")
#             except Exception as e:
#                 logger.debug(f"     Could not extract followers: {e}")
#                 user_data['followers_count'] = 0
            
#             # Extract following count
#             try:
#                 following_link = self.driver.find_element(
#                     By.XPATH, "//a[contains(@href, '/following')]/span/span"
#                 )
#                 following_text = following_link.text
#                 user_data['following_count'] = self.parse_count_text(following_text)
#                 logger.debug(f"     Following: {user_data['following_count']}")
#             except Exception as e:
#                 logger.debug(f"     Could not extract following: {e}")
#                 user_data['following_count'] = 0
            
#             # Extract total tweet count from profile
#             try:
#                 # Look for text like "1,234 posts" or "5.6K posts"
#                 profile_info = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='UserProfileHeader_Items']")
#                 profile_text = profile_info.text
                
#                 # Try to find post count
#                 import re
#                 post_match = re.search(r'([\d,\.]+[KMB]?)\s+[Pp]osts?', profile_text)
#                 if post_match:
#                     user_data['tweet_count'] = self.parse_count_text(post_match.group(1))
#                 else:
#                     user_data['tweet_count'] = 0
#                 logger.debug(f"     Tweets: {user_data['tweet_count']}")
#             except Exception as e:
#                 logger.debug(f"     Could not extract tweet count: {e}")
#                 user_data['tweet_count'] = 0
            
#             # Extract bio/description
#             try:
#                 bio_elem = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='UserDescription']")
#                 user_data['bio'] = bio_elem.text.strip()
#                 logger.debug(f"     Bio: {user_data['bio'][:50]}...")
#             except:
#                 user_data['bio'] = ''
            
#             # Extract location
#             try:
#                 location_elem = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='UserLocation']")
#                 user_data['location'] = location_elem.text.strip()
#                 logger.debug(f"     Location: {user_data['location']}")
#             except:
#                 user_data['location'] = ''
            
#             # Extract joined date (user_created_at)
#             try:
#                 joined_elem = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='UserJoinDate']")
#                 joined_date = joined_elem.get_attribute('title')
#                 if not joined_date:
#                     joined_date = joined_elem.text
#                 user_data['user_created_at'] = joined_date
#                 logger.debug(f"     Joined: {user_data['user_created_at']}")
#             except:
#                 user_data['user_created_at'] = ''
            
#             # Extract verified status (blue checkmark)
#             try:
#                 verified_elem = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='UserVerifiedBadge']")
#                 user_data['verified'] = True
#                 logger.debug(f"     Verified: ✓")
#             except:
#                 user_data['verified'] = False
            
#             # Extract user_id from page source or profile URL
#             try:
#                 # Try to get numeric user ID from REST_ID in page source
#                 page_source = self.driver.page_source
#                 id_match = re.search(r'"rest_id":"(\d+)"', page_source)
#                 if id_match:
#                     user_data['user_id'] = id_match.group(1)
#                     logger.debug(f"     User ID: {user_data['user_id']}")
#                 else:
#                     user_data['user_id'] = username
#             except:
#                 user_data['user_id'] = username
            
#             # Default values for fields not easily accessible
#             user_data['listed_count'] = 0
            
#             self.users_scraped += 1
#             logger.info(f"   ✓ Profile extracted ({self.users_scraped} users total)")
            
#             return user_data
            
#         except Exception as e:
#             logger.error(f"   ✗ Error extracting profile for @{username}: {str(e)}")
#             # Return default data structure
#             return {
#                 'username': username,
#                 'user_id': username,
#                 'followers_count': 0,
#                 'following_count': 0,
#                 'tweet_count': 0,
#                 'bio': '',
#                 'location': '',
#                 'user_created_at': '',
#                 'verified': False,
#                 'listed_count': 0
#             }
    
#     def get_user_data(self, username):
#         """
#         Get user data from cache or scrape if not cached
        
#         Args:
#             username (str): Twitter username
            
#         Returns:
#             dict: User profile data
#         """
#         if username not in self.user_cache:
#             user_data = self.extract_user_profile(username)
#             if user_data:
#                 self.user_cache[username] = user_data
        
#         return self.user_cache.get(username, {})
    
#     def parse_count_text(self, text):
#         """
#         Parse count from text like "1.2K", "5M", "123,456"
        
#         Args:
#             text (str): Text containing count
            
#         Returns:
#             int: Parsed count
#         """
#         try:
#             text = text.strip().replace(',', '')
            
#             if 'K' in text.upper():
#                 return int(float(text.upper().replace('K', '')) * 1000)
#             elif 'M' in text.upper():
#                 return int(float(text.upper().replace('M', '')) * 1000000)
#             elif 'B' in text.upper():
#                 return int(float(text.upper().replace('B', '')) * 1000000000)
#             else:
#                 return int(float(text))
#         except:
#             return 0
    
#     def extract_tweet_data(self, tweet_element):
#         """
#         Extract tweet data from a tweet element
#         NOW WITH COMPLETE USER PROFILE DATA!
#         """
#         try:
#             tweet_data = {}
            
#             # Extract tweet text
#             try:
#                 text_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
#                 tweet_data['text'] = text_element.text.strip()
#             except:
#                 tweet_data['text'] = ''
            
#             # Skip if no text or not English
#             if not tweet_data['text'] or not self.is_english(tweet_data['text']):
#                 return None
            
#             # Extract username
#             try:
#                 user_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Name"]')
#                 username_spans = user_element.find_elements(By.TAG_NAME, 'span')
#                 for span in username_spans:
#                     if span.text.startswith('@'):
#                         tweet_data['username'] = span.text.replace('@', '')
#                         break
#                 if 'username' not in tweet_data:
#                     tweet_data['username'] = ''
#             except:
#                 tweet_data['username'] = ''
            
#             # Skip if no username
#             if not tweet_data['username']:
#                 return None
            
#             # Extract display name
#             try:
#                 display_name_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Name"]')
#                 tweet_data['display_name'] = display_name_element.text.split('\n')[0]
#             except:
#                 tweet_data['display_name'] = ''
            
#             # Extract timestamp/tweet link
#             try:
#                 time_element = tweet_element.find_element(By.TAG_NAME, 'time')
#                 tweet_data['timestamp'] = time_element.get_attribute('datetime')
                
#                 link_element = time_element.find_element(By.XPATH, '..')
#                 tweet_url = link_element.get_attribute('href')
#                 if tweet_url:
#                     tweet_data['tweet_id'] = tweet_url.split('/')[-1]
#                 else:
#                     tweet_data['tweet_id'] = ''
#             except:
#                 tweet_data['timestamp'] = ''
#                 tweet_data['tweet_id'] = ''
            
#             # Extract engagement metrics
#             try:
#                 like_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="like"]')
#                 like_text = like_element.get_attribute('aria-label') or ''
#                 tweet_data['like_count'] = self.parse_count(like_text)
#             except:
#                 tweet_data['like_count'] = 0
            
#             try:
#                 retweet_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="retweet"]')
#                 retweet_text = retweet_element.get_attribute('aria-label') or ''
#                 tweet_data['retweet_count'] = self.parse_count(retweet_text)
#             except:
#                 tweet_data['retweet_count'] = 0
            
#             try:
#                 reply_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="reply"]')
#                 reply_text = reply_element.get_attribute('aria-label') or ''
#                 tweet_data['reply_count'] = self.parse_count(reply_text)
#             except:
#                 tweet_data['reply_count'] = 0
            
#             # Extract quote count (if visible)
#             try:
#                 # Sometimes visible in the tweet element
#                 tweet_data['quote_count'] = 0  # Still hard to get reliably
#             except:
#                 tweet_data['quote_count'] = 0
            
#             # Extract hashtags from text
#             tweet_data['hashtags'] = ','.join([word[1:] for word in tweet_data['text'].split() if word.startswith('#')])
            
#             # Extract mentions from text
#             tweet_data['mentions'] = ','.join([word[1:] for word in tweet_data['text'].split() if word.startswith('@')])
            
#             # NEW: Extract URLs from text
#             url_pattern = r'https?://[^\s]+'
#             urls = re.findall(url_pattern, tweet_data['text'])
#             tweet_data['urls'] = ','.join(urls)
            
#             tweet_data['language'] = 'en'
            
#             # MODIFIED: Don't fetch profile yet - just store username
#             # Profiles will be fetched in batch AFTER collecting all tweets
#             # This prevents navigating away from search results
#             if not tweet_data['username']:
#                 return None  # Skip tweets without username
            
#             # Set temporary default values (will be filled later)
#             tweet_data['user_id'] = tweet_data['username']
#             tweet_data['bio'] = ''
#             tweet_data['location'] = ''
#             tweet_data['user_created_at'] = ''
#             tweet_data['followers_count'] = 0
#             tweet_data['following_count'] = 0
#             tweet_data['tweet_count'] = 0
#             tweet_data['listed_count'] = 0
#             tweet_data['verified'] = False
            
#             return tweet_data
            
#         except Exception as e:
#             logger.debug(f"Error extracting tweet data: {str(e)}")
#             return None
    
#     def parse_count(self, text):
#         """Parse engagement count from aria-label text"""
#         try:
#             import re
#             numbers = re.findall(r'[\d,\.]+[KMB]?', text)
#             if not numbers:
#                 return 0
            
#             num_str = numbers[0].replace(',', '')
            
#             if 'K' in num_str:
#                 return int(float(num_str.replace('K', '')) * 1000)
#             elif 'M' in num_str:
#                 return int(float(num_str.replace('M', '')) * 1000000)
#             elif 'B' in num_str:
#                 return int(float(num_str.replace('B', '')) * 1000000000)
#             else:
#                 return int(float(num_str))
#         except:
#             return 0
    
#     def check_for_retry_button(self):
#         """Check if Twitter shows a retry/rate limit button"""
#         try:
#             retry_buttons = self.driver.find_elements(By.XPATH, 
#                 "//*[contains(text(), 'Retry') or contains(text(), 'Try again')]")
            
#             if retry_buttons:
#                 logger.warning("⚠ Retry button detected - Twitter rate limiting detected!")
#                 logger.info("Waiting 30 seconds before retrying...")
#                 time.sleep(30)
#                 retry_buttons[0].click()
#                 logger.info("✓ Clicked retry button")
#                 time.sleep(random.uniform(5, 8))
#                 return True
            
#             return False
            
#         except Exception as e:
#             logger.debug(f"Error checking retry button: {str(e)}")
#             return False
    
#     def scrape_tweets_for_hashtag(self, hashtag, max_tweets=2000):
#         """Scrape tweets for a specific hashtag with diversity control"""
#         try:
#             logger.info(f"="*50)
#             logger.info(f"Scraping tweets for hashtag: {hashtag}")
#             logger.info(f"Max tweets per user: {self.max_tweets_per_user} (for diversity)")
#             logger.info(f"="*50)
            
#             # Reset user tweet count for this hashtag
#             self.user_tweet_count = {}
            
#             search_query = hashtag if hashtag.startswith('#') else f"#{hashtag}"
#             search_url = f"https://twitter.com/search?q={search_query.replace('#', '%23')}&src=typed_query&f=live"
            
#             logger.info(f"Navigating to search: {search_query}")
#             self.driver.get(search_url)
            
#             initial_wait = random.uniform(5, 8)
#             logger.info(f"Waiting {initial_wait:.1f}s for page to load...")
#             time.sleep(initial_wait)
            
#             self.check_for_retry_button()
            
#             tweets_data = []
#             seen_tweet_ids = set()
#             scroll_attempts = 0
#             max_scroll_attempts = 150
#             no_new_tweets_count = 0
#             max_no_new_tweets = 8
            
#             while len(tweets_data) < max_tweets and scroll_attempts < max_scroll_attempts:
#                 try:
#                     if scroll_attempts % 10 == 0 and scroll_attempts > 0:
#                         self.check_for_retry_button()
                    
#                     tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
                    
#                     if len(tweet_elements) == 0:
#                         logger.warning("No tweets found on page, checking for issues...")
#                         if self.check_for_retry_button():
#                             continue
                    
#                     unique_count = len(self.user_tweet_count)
#                     logger.info(f"Found {len(tweet_elements)} tweet elements, collected {len(tweets_data)}/{max_tweets} tweets from {unique_count} unique users")
                    
#                     initial_count = len(tweets_data)
                    
#                     for tweet_element in tweet_elements:
#                         if len(tweets_data) >= max_tweets:
#                             break
                        
#                         try:
#                             tweet_data = self.extract_tweet_data(tweet_element)
                            
#                             if tweet_data and tweet_data['tweet_id']:
#                                 if tweet_data['tweet_id'] not in seen_tweet_ids:
#                                     # NEW: Check diversity - limit tweets per user
#                                     username = tweet_data.get('username', '')
#                                     user_count = self.user_tweet_count.get(username, 0)
                                    
#                                     if user_count >= self.max_tweets_per_user:
#                                         logger.debug(f"Skipping @{username} - already have {user_count} tweets")
#                                         continue
                                    
#                                     tweet_data['source_hashtag'] = hashtag
#                                     tweets_data.append(tweet_data)
#                                     seen_tweet_ids.add(tweet_data['tweet_id'])
                                    
#                                     # Track tweets per user
#                                     self.user_tweet_count[username] = user_count + 1
                                    
#                                     if len(tweets_data) % 25 == 0:
#                                         unique_users = len(self.user_tweet_count)
#                                         logger.info(f"✓ Collected {len(tweets_data)} tweets from {unique_users} unique users")
                        
#                         except StaleElementReferenceException:
#                             continue
#                         except Exception as e:
#                             logger.debug(f"Error processing tweet: {str(e)}")
#                             continue
                    
#                     if len(tweets_data) == initial_count:
#                         no_new_tweets_count += 1
#                         logger.info(f"No new tweets this scroll ({no_new_tweets_count}/{max_no_new_tweets})")
                        
#                         if no_new_tweets_count == 3:
#                             self.check_for_retry_button()
                        
#                         if no_new_tweets_count >= max_no_new_tweets:
#                             logger.info(f"No new tweets after {max_no_new_tweets} scrolls, stopping")
#                             break
#                     else:
#                         no_new_tweets_count = 0
                    
#                     if len(tweets_data) < max_tweets:
#                         scroll_amount = random.randint(500, 1000)
#                         self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                        
#                         # Wait for new tweets to load
#                         wait_time = random.uniform(3, 6)
#                         logger.info(f"Scrolling... waiting {wait_time:.1f}s")
#                         time.sleep(wait_time)
#                         scroll_attempts += 1
                    
#                 except Exception as e:
#                     logger.error(f"Error during scrolling: {str(e)}")
#                     self.check_for_retry_button()
#                     scroll_attempts += 1
#                     time.sleep(5)
            
#             # NEW: Extract user profiles in batch AFTER collecting all tweets
#             logger.info(f"\n{'='*50}")
#             logger.info(f"✓ Tweet collection complete: {len(tweets_data)} tweets")
#             logger.info(f"{'='*50}")
            
#             # Get unique usernames
#             unique_usernames = list(set([tweet['username'] for tweet in tweets_data if tweet.get('username')]))
#             logger.info(f" Found {len(unique_usernames)} unique users")
#             logger.info(f"🔄 Now extracting user profiles...")
            
#             # Extract profiles for each unique user
#             for idx, username in enumerate(unique_usernames, 1):
#                 if username not in self.user_cache:
#                     logger.info(f"  [{idx}/{len(unique_usernames)}] Extracting profile: @{username}")
#                     user_data = self.extract_user_profile(username)
#                     if user_data:
#                         self.user_cache[username] = user_data
                    
#                     # Small delay between profile visits
#                     if idx < len(unique_usernames):
#                         time.sleep(random.uniform(2, 4))
#                 else:
#                     logger.info(f"  [{idx}/{len(unique_usernames)}] Using cached profile: @{username}")
            
#             # Update all tweets with user profile data
#             logger.info(f"📝 Merging user profiles with tweets...")
#             for tweet in tweets_data:
#                 username = tweet.get('username')
#                 if username and username in self.user_cache:
#                     user_data = self.user_cache[username]
#                     tweet['user_id'] = user_data.get('user_id', username)
#                     tweet['bio'] = user_data.get('bio', '')
#                     tweet['location'] = user_data.get('location', '')
#                     tweet['user_created_at'] = user_data.get('user_created_at', '')
#                     tweet['followers_count'] = user_data.get('followers_count', 0)
#                     tweet['following_count'] = user_data.get('following_count', 0)
#                     tweet['tweet_count'] = user_data.get('tweet_count', 0)
#                     tweet['listed_count'] = user_data.get('listed_count', 0)
#                     tweet['verified'] = user_data.get('verified', False)
            
#             logger.info(f"✅ Complete: {len(tweets_data)} tweets with full profiles from {len(self.user_cache)} users")
#             return tweets_data
            
#         except Exception as e:
#             logger.error(f"Error scraping tweets for {hashtag}: {str(e)}")
#             return []
    
#     def read_hashtags(self, filepath='data/trending_hashtags.txt'):
#         """Read hashtags from file"""
#         try:
#             hashtags = []
#             with open(filepath, 'r', encoding='utf-8') as f:
#                 for line in f:
#                     line = line.strip()
#                     if line and not line.startswith('#'):
#                         if '. ' in line:
#                             hashtag = line.split('. ', 1)[1]
#                         else:
#                             hashtag = line
#                         hashtags.append(hashtag)
            
#             logger.info(f"Read {len(hashtags)} hashtags from {filepath}")
#             return hashtags
            
#         except Exception as e:
#             logger.error(f"Error reading hashtags: {str(e)}")
#             return []
    
#     def save_to_json(self, tweets_data, output_file):
#         """Save tweets data to JSON file"""
#         try:
#             if not tweets_data:
#                 logger.warning("No tweets to save")
#                 return
            
#             Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            
#             # Create output structure
#             output_data = {
#                 'metadata': {
#                     'total_tweets': len(tweets_data),
#                     'unique_users': len(set([t['username'] for t in tweets_data if t.get('username')])),
#                     'collection_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
#                     'scraper_version': 'enhanced_v1.0'
#                 },
#                 'tweets': tweets_data
#             }
            
#             # Save as JSON with pretty formatting
#             with open(output_file, 'w', encoding='utf-8') as f:
#                 json.dump(output_data, f, ensure_ascii=False, indent=2)
            
#             logger.info(f"✓ Saved {len(tweets_data)} tweets to {output_file}")
#             logger.info(f"  Format: JSON with metadata")
            
#         except Exception as e:
#             logger.error(f"Error saving to JSON: {str(e)}")
    
#     def scrape_all_hashtags(self):
#         """Main method to scrape tweets for all hashtags"""
#         try:
#             self.setup_driver()
            
#             if not self.load_cookies():
#                 raise Exception("Could not load cookies. Run hashtag_scraper.py first!")
            
#             if not self.is_logged_in():
#                 raise Exception("Not logged in. Cookies expired. Run hashtag_scraper.py again.")
            
#             hashtags = self.read_hashtags()
            
#             if not hashtags:
#                 raise Exception("No hashtags found to scrape")
            
#             all_tweets = []
            
#             for idx, hashtag in enumerate(hashtags, 1):
#                 logger.info("")
#                 logger.info(f"█ Processing hashtag {idx}/{len(hashtags)}: {hashtag}")
                
#                 tweets = self.scrape_tweets_for_hashtag(hashtag, self.tweets_per_hashtag)
#                 all_tweets.extend(tweets)
                
#                 logger.info(f" Total: {len(all_tweets)} tweets, {len(self.user_cache)} unique users")
                
#                 if idx < len(hashtags):
#                     wait_time = random.uniform(60, 120)
#                     logger.info(f"⏸ Waiting {int(wait_time)}s before next hashtag...")
#                     time.sleep(wait_time)
            
#             timestamp = datetime.now().strftime('%Y-%m-%d')
#             output_file = f"data/tweets_{timestamp}_enhanced.json"
            
#             self.save_to_json(all_tweets, output_file)
            
#             logger.info(f"✨ Scraping completed!")
#             logger.info(f"   Total tweets: {len(all_tweets)}")
#             logger.info(f"   Unique users: {len(self.user_cache)}")
#             logger.info(f"   Output: {output_file}")
            
#             return output_file
            
#         except Exception as e:
#             logger.error(f"Error in scraping process: {str(e)}")
#             raise
        
#         finally:
#             if self.driver:
#                 self.driver.quit()
#                 logger.info("WebDriver closed")


# def main():
#     """Main execution function"""
#     logger.info("="*50)
#     logger.info("Starting ENHANCED Tweet Scraper")
#     logger.info("="*50)
    
#     try:
#         scraper = EnhancedTweetScraper()
#         output_file = scraper.scrape_all_hashtags()
        
#         logger.info("="*50)
#         logger.info("✨ Enhanced scraping completed!")
#         logger.info(f"Data saved to: {output_file}")
#         logger.info("="*50)
        
#     except Exception as e:
#         logger.error(f"Fatal error: {str(e)}")
#         raise


# if __name__ == "__main__":
#     main()

#################################################################################################################################

import os
import json
import time
import random
import logging
import re
import pickle
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import undetected_chromedriver as uc
from chrome_version import chrome_major_version
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import pandas as pd
from langdetect import detect, LangDetectException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/tweet_scraper_enhanced.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

try:
    from tweet_db import TweetDB
except Exception:
    TweetDB = None

# Fix console encoding for Unicode characters (Windows)
import sys
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass


class EnhancedTweetScraper:
    """
    ENHANCED tweet scraper with complete user profile extraction.
    FIXED:
      1. Retry logic on profile visit failure
      2. Persistent profile cache (saved to disk so crashes don't lose progress)
      3. Proper user_created_at date parsing → ISO format string
      4. Fixed tweet_count extraction (updated CSS selectors for X/Twitter 2024+)
    """

    def __init__(self):
        self.driver = None
        self.tweets_per_hashtag = int(os.getenv('TWEETS_PER_HASHTAG', 2000))
        self.headless = os.getenv('HEADLESS_MODE', 'False').lower() == 'true'
        self.cookies_file = 'data/twitter_cookies.pkl'

        self.mongo_db = None
        self.mongo_enabled = False
        self._setup_mongo()

        # FIX 2: Persistent cache file — survives crashes
        self.profile_cache_file = 'data/user_profile_cache.json'
        self.cache_write_enabled = True
        self.cache_load_error = None
        self.user_cache = self._load_profile_cache()

        self.users_scraped = 0
        self.max_tweets_per_user = 50
        self.user_tweet_count = {}
        self.new_users_this_run = {}

        # FIX 1: Retry settings
        self.max_profile_retries = 3
        self.retry_wait = 15  # seconds between retries

        logger.info(f"Enhanced tweet scraper initialized. Target: {self.tweets_per_hashtag} tweets/hashtag")
        logger.info(f"Loaded {len(self.user_cache)} profiles from cache")
        if not self.cache_write_enabled:
            logger.warning("Cache writes are disabled because the existing cache file could not be loaded safely.")

    def _setup_mongo(self):
        """Initialize MongoDB integration if dependencies and connection are available."""
        mongo_uri = os.getenv('MONGO_URI')
        if not mongo_uri:
            logger.info("MongoDB integration disabled: MONGO_URI not set")
            return

        if TweetDB is None:
            logger.warning("MongoDB integration disabled: tweet_db/pymongo import failed")
            return

        try:
            self.mongo_db = TweetDB()
            self.mongo_enabled = True
            logger.info("MongoDB integration enabled (Tweets.Raw + Tweets.User_Cache)")
        except Exception as e:
            logger.warning(f"MongoDB integration disabled due to connection error: {e}")
            self.mongo_db = None
            self.mongo_enabled = False

    # -------------------------------------------------------------------------
    # FIX 2: Persistent cache helpers
    # -------------------------------------------------------------------------

    def _load_profile_cache(self):
        """Load existing profile cache from disk (so we don't re-scrape on restart)"""
        cache_file_exists = os.path.exists(self.profile_cache_file)
        try:
            if cache_file_exists:
                with open(self.profile_cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)

                # Backfill newly added fields for old cache entries.
                for profile in cache.values():
                    if not isinstance(profile, dict):
                        continue
                    profile.setdefault('default_profile_image', False)
                    profile.setdefault('account_creation_date', profile.get('user_created_at', ''))

                logger.info(f"✓ Loaded {len(cache)} cached profiles from {self.profile_cache_file}")
                return cache
        except Exception as e:
            self.cache_write_enabled = False
            self.cache_load_error = str(e)

            if cache_file_exists:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = f"{self.profile_cache_file}.corrupt_{timestamp}"
                try:
                    shutil.copy2(self.profile_cache_file, backup_path)
                    logger.error(f"Cache file appears corrupted. Backup saved to {backup_path}")
                except Exception as backup_error:
                    logger.error(f"Cache file appears corrupted and backup failed: {backup_error}")

            logger.error(
                "Could not load profile cache; disabling cache writes to avoid overwriting existing data. "
                f"Error: {e}"
            )
        return {}

    def _save_profile_cache(self):
        """Save profile cache to disk after every new profile scraped"""
        if not self.cache_write_enabled:
            logger.warning("Skipping cache save because cache loading failed earlier; existing cache file is left untouched.")
            return

        try:
            Path(self.profile_cache_file).parent.mkdir(parents=True, exist_ok=True)
            temp_file = f"{self.profile_cache_file}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_cache, f, ensure_ascii=False, indent=2)
            os.replace(temp_file, self.profile_cache_file)
        except Exception as e:
            logger.warning(f"Could not save profile cache: {e}")

    # -------------------------------------------------------------------------
    # FIX 3: Date parsing helper
    # -------------------------------------------------------------------------

    def _parse_joined_date(self, raw_date_str):
        """
        Convert scraped joined date string to ISO format (YYYY-MM-DD).

        Handles formats like:
          "Joined October 2014"        → "2014-10-01"
          "Joined Oct 2014"            → "2014-10-01"
          "October 2014"               → "2014-10-01"
          "January 1, 2020"            → "2020-01-01"
          "2014-10-01" (already ISO)   → "2014-10-01"
        Returns "" if parsing fails.
        """
        if not raw_date_str:
            return ""

        raw = raw_date_str.strip()

        # Already ISO format
        if re.match(r'^\d{4}-\d{2}-\d{2}', raw):
            return raw[:10]

        # Remove "Joined" prefix
        raw = re.sub(r'^[Jj]oined\s+', '', raw).strip()

        formats_to_try = [
            "%B %Y",       # October 2014
            "%b %Y",       # Oct 2014
            "%B %d, %Y",   # January 1, 2020
            "%b %d, %Y",   # Jan 1, 2020
            "%d %B %Y",    # 1 October 2014
            "%Y",          # 2014 (year only)
        ]

        for fmt in formats_to_try:
            try:
                parsed = datetime.strptime(raw, fmt)
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue

        logger.debug(f"Could not parse date: '{raw_date_str}'")
        return ""

    def _is_default_profile_image(self, image_url):
        """Return True when the avatar URL appears to be a default X/Twitter placeholder image."""
        if not image_url:
            return False

        normalized = image_url.lower()
        default_markers = (
            'default_profile_images',
            'default_profile_normal',
            'default_profile_400x400',
            'abs.twimg.com/sticky/default_profile_images',
        )
        return any(marker in normalized for marker in default_markers)

    # -------------------------------------------------------------------------
    # FIX 1 + 4: extract_user_profile with retries and fixed tweet_count
    # -------------------------------------------------------------------------

    def extract_user_profile(self, username):
        """
        Extract complete user profile data by visiting the user's page.
        FIXED:
          - Retries up to self.max_profile_retries times on failure
          - Parses user_created_at to ISO date string
          - Uses updated selectors for tweet/post count
          - Saves cache to disk after each successful scrape
        """
        for attempt in range(1, self.max_profile_retries + 1):
            try:
                logger.info(f"   → Extracting profile for @{username} (attempt {attempt}/{self.max_profile_retries})")

                profile_url = f"https://twitter.com/{username}"
                self.driver.get(profile_url)
                time.sleep(random.uniform(2, 4))

                # Check if profile page loaded properly (not an error/suspended page)
                page_source = self.driver.page_source
                if "This account doesn't exist" in page_source or "Account suspended" in page_source:
                    logger.warning(f"   ⚠ @{username} account not found or suspended — skipping")
                    return self._empty_profile(username)

                user_data = {'username': username}

                # --- Followers ---
                try:
                    followers_link = self.driver.find_element(
                        By.XPATH,
                        "//a[contains(@href, '/verified_followers') or contains(@href, '/followers')]/span/span"
                    )
                    user_data['followers_count'] = self.parse_count_text(followers_link.text)
                except Exception:
                    user_data['followers_count'] = 0

                # --- Following ---
                try:
                    following_link = self.driver.find_element(
                        By.XPATH,
                        "//a[contains(@href, '/following')]/span/span"
                    )
                    user_data['following_count'] = self.parse_count_text(following_link.text)
                except Exception:
                    user_data['following_count'] = 0

                # --- FIX 4: Tweet / Post count (multiple selector fallbacks) ---
                tweet_count = 0
                try:
                    # Method 1: aria-label on the Posts tab (most reliable in 2024)
                    posts_tab = self.driver.find_element(
                        By.XPATH,
                        "//a[@role='tab' and contains(@href, '/with_replies') or @role='tab']//span[contains(@class,'r-')]"
                    )
                    tweet_count = self.parse_count_text(posts_tab.text)
                except Exception:
                    pass

                if tweet_count == 0:
                    try:
                        # Method 2: Look for "X posts" text anywhere in page header area
                        header_div = self.driver.find_element(By.CSS_SELECTOR, 'div[data-testid="UserProfileHeader_Items"]')
                        header_text = header_div.text
                        match = re.search(r'([\d,\.]+[KMB]?)\s+[Pp]osts?', header_text)
                        if match:
                            tweet_count = self.parse_count_text(match.group(1))
                    except Exception:
                        pass

                if tweet_count == 0:
                    try:
                        # Method 3: Scan all visible stat spans for a number adjacent to "Posts"
                        all_spans = self.driver.find_elements(By.CSS_SELECTOR, 'span')
                        for i, span in enumerate(all_spans):
                            if span.text.lower() in ('posts', 'post'):
                                # The count is usually in the span just before this one
                                if i > 0:
                                    tweet_count = self.parse_count_text(all_spans[i - 1].text)
                                    if tweet_count > 0:
                                        break
                    except Exception:
                        pass

                user_data['tweet_count'] = tweet_count

                # --- Bio ---
                try:
                    bio_elem = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='UserDescription']")
                    user_data['bio'] = bio_elem.text.strip()
                except Exception:
                    user_data['bio'] = ''

                # --- Location ---
                try:
                    location_elem = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='UserLocation']")
                    user_data['location'] = location_elem.text.strip()
                except Exception:
                    user_data['location'] = ''

                # --- FIX 3: Joined date → ISO format ---
                raw_date = ''
                try:
                    joined_elem = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='UserJoinDate']")
                    raw_date = joined_elem.get_attribute('title') or joined_elem.text
                except Exception:
                    pass
                user_data['user_created_at'] = self._parse_joined_date(raw_date)
                user_data['account_creation_date'] = user_data['user_created_at']

                # --- Default profile image (egg/placeholder equivalent) ---
                user_data['default_profile_image'] = False
                try:
                    avatar_selectors = [
                        "img[alt*='profile picture']",
                        "img[src*='profile_images']",
                        "[data-testid='UserAvatar-Container'] img",
                    ]
                    avatar_url = ''
                    for selector in avatar_selectors:
                        candidates = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for candidate in candidates:
                            src = candidate.get_attribute('src') or ''
                            if src and ('profile_images' in src or 'twimg.com' in src):
                                avatar_url = src
                                break
                        if avatar_url:
                            break
                    user_data['default_profile_image'] = self._is_default_profile_image(avatar_url)
                except Exception:
                    user_data['default_profile_image'] = False

                # --- Verified ---
                try:
                    self.driver.find_element(By.CSS_SELECTOR, "[data-testid='UserVerifiedBadge']")
                    user_data['verified'] = True
                except Exception:
                    user_data['verified'] = False

                # --- Numeric user ID ---
                try:
                    id_match = re.search(r'"rest_id":"(\d+)"', self.driver.page_source)
                    user_data['user_id'] = id_match.group(1) if id_match else username
                except Exception:
                    user_data['user_id'] = username

                user_data['listed_count'] = 0

                self.users_scraped += 1
                logger.info(
                    f"   ✓ @{username}: followers={user_data['followers_count']}, "
                    f"following={user_data['following_count']}, "
                    f"tweets={user_data['tweet_count']}, "
                    f"joined={user_data['user_created_at']}, "
                    f"default_profile_image={user_data['default_profile_image']}"
                )

                # FIX 2: Save cache to disk immediately after success
                self.user_cache[username] = user_data
                self.new_users_this_run[username] = dict(user_data)
                self._save_profile_cache()

                return user_data

            except Exception as e:
                logger.warning(f"   ✗ Attempt {attempt} failed for @{username}: {e}")
                if attempt < self.max_profile_retries:
                    logger.info(f"   ⏳ Waiting {self.retry_wait}s before retry...")
                    time.sleep(self.retry_wait)
                else:
                    logger.error(f"   ✗ All {self.max_profile_retries} attempts failed for @{username} — using empty profile")

        return self._empty_profile(username)

    def _empty_profile(self, username):
        """Return a blank profile structure when scraping fails"""
        return {
            'username': username,
            'user_id': username,
            'followers_count': 0,
            'following_count': 0,
            'tweet_count': 0,
            'bio': '',
            'location': '',
            'user_created_at': '',
            'account_creation_date': '',
            'default_profile_image': False,
            'verified': False,
            'listed_count': 0
        }

    # -------------------------------------------------------------------------
    # Everything below is UNCHANGED from your original file
    # -------------------------------------------------------------------------

    def setup_driver(self):
        """Initialize Chrome WebDriver with undetected-chromedriver"""
        try:
            logger.info("Setting up Undetected Chrome WebDriver...")
            options = uc.ChromeOptions()
            if self.headless:
                options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            vm = chrome_major_version()
            logger.info(f"Chrome major version (for ChromeDriver): {vm}")
            self.driver = uc.Chrome(options=options, version_main=vm)
            self.driver.maximize_window()
            logger.info("WebDriver setup successful")
            return self.driver
        except Exception as e:
            logger.error(f"Failed to setup WebDriver: {str(e)}")
            raise

    def load_cookies(self):
        """Load cookies from hashtag scraper"""
        try:
            if not os.path.exists(self.cookies_file):
                logger.error("Cookie file not found. Run hashtag_scraper.py first!")
                return False
            self.driver.get('https://twitter.com')
            time.sleep(2)
            with open(self.cookies_file, 'rb') as file:
                cookies = pickle.load(file)
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    logger.warning(f"Could not add cookie: {e}")
            logger.info("✓ Cookies loaded!")
            return True
        except Exception as e:
            logger.error(f"Error loading cookies: {e}")
            return False

    def is_logged_in(self):
        """Check if user is logged in"""
        try:
            self.driver.get('https://twitter.com/home')
            time.sleep(3)
            return 'home' in self.driver.current_url
        except Exception:
            return False

    def is_english(self, text):
        """Check if text is English"""
        try:
            if not text or len(text) < 3:
                return False
            return detect(text) == 'en'
        except LangDetectException:
            return False

    def get_user_data(self, username):
        """Get user data from cache or scrape"""
        if username not in self.user_cache:
            user_data = self.extract_user_profile(username)
            if user_data:
                self.user_cache[username] = user_data
                self._save_profile_cache()
        return self.user_cache.get(username, {})

    def parse_count_text(self, text):
        """Parse count from text like 1.2K, 5M, 123,456"""
        try:
            text = text.strip().replace(',', '')
            if 'K' in text.upper():
                return int(float(text.upper().replace('K', '')) * 1000)
            elif 'M' in text.upper():
                return int(float(text.upper().replace('M', '')) * 1_000_000)
            elif 'B' in text.upper():
                return int(float(text.upper().replace('B', '')) * 1_000_000_000)
            else:
                return int(float(text))
        except Exception:
            return 0

    def extract_tweet_data(self, tweet_element):
        """Extract tweet data from a tweet element"""
        try:
            tweet_data = {}

            try:
                text_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
                tweet_data['text'] = text_element.text.strip()
            except Exception:
                tweet_data['text'] = ''

            if not tweet_data['text'] or not self.is_english(tweet_data['text']):
                return None

            try:
                user_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Name"]')
                username_spans = user_element.find_elements(By.TAG_NAME, 'span')
                for span in username_spans:
                    if span.text.startswith('@'):
                        tweet_data['username'] = span.text.replace('@', '')
                        break
                if 'username' not in tweet_data:
                    tweet_data['username'] = ''
            except Exception:
                tweet_data['username'] = ''

            if not tweet_data['username']:
                return None

            try:
                display_name_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Name"]')
                tweet_data['display_name'] = display_name_element.text.split('\n')[0]
            except Exception:
                tweet_data['display_name'] = ''

            try:
                time_element = tweet_element.find_element(By.TAG_NAME, 'time')
                tweet_data['timestamp'] = time_element.get_attribute('datetime')
                link_element = time_element.find_element(By.XPATH, '..')
                tweet_url = link_element.get_attribute('href')
                tweet_data['tweet_id'] = tweet_url.split('/')[-1] if tweet_url else ''
            except Exception:
                tweet_data['timestamp'] = ''
                tweet_data['tweet_id'] = ''

            try:
                like_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="like"]')
                tweet_data['like_count'] = self.parse_count(like_element.get_attribute('aria-label') or '')
            except Exception:
                tweet_data['like_count'] = 0

            try:
                retweet_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="retweet"]')
                tweet_data['retweet_count'] = self.parse_count(retweet_element.get_attribute('aria-label') or '')
            except Exception:
                tweet_data['retweet_count'] = 0

            try:
                reply_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="reply"]')
                tweet_data['reply_count'] = self.parse_count(reply_element.get_attribute('aria-label') or '')
            except Exception:
                tweet_data['reply_count'] = 0

            tweet_data['quote_count'] = 0
            tweet_data['hashtags'] = ','.join([w[1:] for w in tweet_data['text'].split() if w.startswith('#')])
            tweet_data['mentions'] = ','.join([w[1:] for w in tweet_data['text'].split() if w.startswith('@')])
            url_pattern = r'https?://[^\s]+'
            tweet_data['urls'] = ','.join(re.findall(url_pattern, tweet_data['text']))
            tweet_data['language'] = 'en'

            # Temporary defaults — filled in batch after all tweets collected
            tweet_data['user_id'] = tweet_data['username']
            tweet_data['bio'] = ''
            tweet_data['location'] = ''
            tweet_data['user_created_at'] = ''
            tweet_data['account_creation_date'] = ''
            tweet_data['default_profile_image'] = False
            tweet_data['followers_count'] = 0
            tweet_data['following_count'] = 0
            tweet_data['tweet_count'] = 0
            tweet_data['listed_count'] = 0
            tweet_data['verified'] = False

            return tweet_data

        except Exception as e:
            logger.debug(f"Error extracting tweet data: {e}")
            return None

    def parse_count(self, text):
        """Parse engagement count from aria-label text"""
        try:
            numbers = re.findall(r'[\d,\.]+[KMB]?', text)
            if not numbers:
                return 0
            num_str = numbers[0].replace(',', '')
            if 'K' in num_str:
                return int(float(num_str.replace('K', '')) * 1000)
            elif 'M' in num_str:
                return int(float(num_str.replace('M', '')) * 1_000_000)
            elif 'B' in num_str:
                return int(float(num_str.replace('B', '')) * 1_000_000_000)
            else:
                return int(float(num_str))
        except Exception:
            return 0

    def check_for_retry_button(self):
        """Check if Twitter shows a retry/rate limit button"""
        try:
            retry_buttons = self.driver.find_elements(
                By.XPATH, "//*[contains(text(), 'Retry') or contains(text(), 'Try again')]"
            )
            if retry_buttons:
                logger.warning("⚠ Rate limiting detected! Waiting 30s...")
                time.sleep(30)
                retry_buttons[0].click()
                time.sleep(random.uniform(5, 8))
                return True
            return False
        except Exception:
            return False

    def scrape_tweets_for_hashtag(self, hashtag, max_tweets=2000):
        """Scrape tweets for a specific hashtag"""
        try:
            logger.info("=" * 50)
            logger.info(f"Scraping: {hashtag}")
            logger.info("=" * 50)

            self.user_tweet_count = {}

            search_query = hashtag if hashtag.startswith('#') else f"#{hashtag}"
            search_url = f"https://twitter.com/search?q={search_query.replace('#', '%23')}&src=typed_query&f=live"
            self.driver.get(search_url)
            time.sleep(random.uniform(5, 8))
            self.check_for_retry_button()

            tweets_data = []
            seen_tweet_ids = set()
            scroll_attempts = 0
            max_scroll_attempts = 150
            no_new_tweets_count = 0
            max_no_new_tweets = 8

            while len(tweets_data) < max_tweets and scroll_attempts < max_scroll_attempts:
                try:
                    if scroll_attempts % 10 == 0 and scroll_attempts > 0:
                        self.check_for_retry_button()

                    tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')

                    if not tweet_elements:
                        logger.warning("No tweets found on page...")
                        if self.check_for_retry_button():
                            continue

                    logger.info(f"Found {len(tweet_elements)} elements | collected {len(tweets_data)}/{max_tweets}")

                    initial_count = len(tweets_data)

                    for tweet_element in tweet_elements:
                        if len(tweets_data) >= max_tweets:
                            break
                        try:
                            tweet_data = self.extract_tweet_data(tweet_element)
                            if tweet_data and tweet_data['tweet_id']:
                                if tweet_data['tweet_id'] not in seen_tweet_ids:
                                    username = tweet_data.get('username', '')
                                    if self.user_tweet_count.get(username, 0) >= self.max_tweets_per_user:
                                        continue
                                    tweet_data['source_hashtag'] = hashtag
                                    tweets_data.append(tweet_data)
                                    seen_tweet_ids.add(tweet_data['tweet_id'])
                                    self.user_tweet_count[username] = self.user_tweet_count.get(username, 0) + 1
                                    if len(tweets_data) % 25 == 0:
                                        logger.info(f"✓ {len(tweets_data)} tweets from {len(self.user_tweet_count)} users")
                        except StaleElementReferenceException:
                            continue
                        except Exception as e:
                            logger.debug(f"Error processing tweet: {e}")
                            continue

                    if len(tweets_data) == initial_count:
                        no_new_tweets_count += 1
                        if no_new_tweets_count >= max_no_new_tweets:
                            logger.info("No new tweets — stopping scroll")
                            break
                    else:
                        no_new_tweets_count = 0

                    if len(tweets_data) < max_tweets:
                        self.driver.execute_script(f"window.scrollBy(0, {random.randint(500, 1000)});")
                        time.sleep(random.uniform(3, 6))
                        scroll_attempts += 1

                except Exception as e:
                    logger.error(f"Scroll error: {e}")
                    self.check_for_retry_button()
                    scroll_attempts += 1
                    time.sleep(5)

            # Batch profile extraction
            logger.info(f"\n{'=' * 50}")
            logger.info(f"✓ Tweets collected: {len(tweets_data)}")
            logger.info("🔄 Extracting user profiles...")

            unique_usernames = list(set([t['username'] for t in tweets_data if t.get('username')]))
            logger.info(f" {len(unique_usernames)} unique users to process")

            for idx, username in enumerate(unique_usernames, 1):
                if username not in self.user_cache:
                    logger.info(f"  [{idx}/{len(unique_usernames)}] Scraping @{username}")
                    user_data = self.extract_user_profile(username)
                    if user_data:
                        self.user_cache[username] = user_data
                        self._save_profile_cache()  # FIX 2: save after each profile
                    if idx < len(unique_usernames):
                        time.sleep(random.uniform(2, 4))
                else:
                    logger.info(f"  [{idx}/{len(unique_usernames)}] Cache hit: @{username}")

            # Merge profiles into tweets
            logger.info("📝 Merging profiles into tweets...")
            for tweet in tweets_data:
                username = tweet.get('username')
                if username and username in self.user_cache:
                    profile = self.user_cache[username]
                    tweet['user_id'] = profile.get('user_id', username)
                    tweet['bio'] = profile.get('bio', '')
                    tweet['location'] = profile.get('location', '')
                    tweet['user_created_at'] = profile.get('user_created_at', '')  # Now ISO date
                    tweet['account_creation_date'] = profile.get('account_creation_date', profile.get('user_created_at', ''))
                    tweet['default_profile_image'] = profile.get('default_profile_image', False)
                    tweet['followers_count'] = profile.get('followers_count', 0)
                    tweet['following_count'] = profile.get('following_count', 0)
                    tweet['tweet_count'] = profile.get('tweet_count', 0)
                    tweet['listed_count'] = profile.get('listed_count', 0)
                    tweet['verified'] = profile.get('verified', False)

            logger.info(f"✅ Done: {len(tweets_data)} tweets with profiles from {len(self.user_cache)} users")
            return tweets_data

        except Exception as e:
            logger.error(f"Error scraping {hashtag}: {e}")
            return []

    def read_hashtags(self, filepath='data/trending_hashtags.txt'):
        """Read hashtags from file"""
        try:
            hashtags = []
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        hashtag = line.split('. ', 1)[1] if '. ' in line else line
                        hashtags.append(hashtag)
            logger.info(f"Read {len(hashtags)} hashtags")
            return hashtags
        except Exception as e:
            logger.error(f"Error reading hashtags: {e}")
            return []

    def save_to_json(self, tweets_data, output_file):
        """Save tweets data to JSON file"""
        try:
            if not tweets_data:
                logger.warning("No tweets to save")
                return
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            output_data = {
                'metadata': {
                    'total_tweets': len(tweets_data),
                    'unique_users': len(set([t['username'] for t in tweets_data if t.get('username')])),
                    'collection_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'scraper_version': 'enhanced_v1.2_profile_flags'
                },
                'tweets': tweets_data
            }
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            logger.info(f"✓ Saved {len(tweets_data)} tweets to {output_file}")
        except Exception as e:
            logger.error(f"Error saving JSON: {e}")

    def scrape_all_hashtags(self):
        """Main method to scrape tweets for all hashtags"""
        try:
            self.setup_driver()
            if not self.load_cookies():
                raise Exception("Could not load cookies. Run hashtag_scraper.py first!")
            if not self.is_logged_in():
                raise Exception("Not logged in. Cookies expired. Run hashtag_scraper.py again.")

            hashtags = self.read_hashtags()
            if not hashtags:
                raise Exception("No hashtags found")

            all_tweets = []
            for idx, hashtag in enumerate(hashtags, 1):
                logger.info(f"\n█ Hashtag {idx}/{len(hashtags)}: {hashtag}")
                tweets = self.scrape_tweets_for_hashtag(hashtag, self.tweets_per_hashtag)
                all_tweets.extend(tweets)
                logger.info(f" Total so far: {len(all_tweets)} tweets, {len(self.user_cache)} users cached")
                if idx < len(hashtags):
                    wait = random.uniform(60, 120)
                    logger.info(f"⏸ Waiting {int(wait)}s before next hashtag...")
                    time.sleep(wait)

            timestamp = datetime.now().strftime('%Y-%m-%d')
            output_file = f"data/tweets_{timestamp}_enhanced.json"
            self.save_to_json(all_tweets, output_file)

            if self.mongo_enabled and self.mongo_db:
                try:
                    self.mongo_db.upsert_tweets(all_tweets, timestamp)
                    self.mongo_db.upsert_user_cache(self.new_users_this_run, timestamp, insert_only=True)
                    logger.info("✓ MongoDB sync complete (Tweets.Raw, Tweets.User_Cache)")
                except Exception as mongo_error:
                    logger.error(f"MongoDB sync failed: {mongo_error}")
            else:
                logger.info("MongoDB sync skipped (integration disabled)")

            logger.info(f"✨ Complete! {len(all_tweets)} tweets, {len(self.user_cache)} users")
            return output_file

        except Exception as e:
            logger.error(f"Error in scraping: {e}")
            raise
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("WebDriver closed")


def main():
    logger.info("=" * 50)
    logger.info("Starting Tweet Scraper")
    logger.info("=" * 50)
    try:
        scraper = EnhancedTweetScraper()
        output_file = scraper.scrape_all_hashtags()
        logger.info(f"Done! Data saved to: {output_file}")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()

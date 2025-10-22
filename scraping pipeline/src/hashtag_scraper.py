"""
Selenium script for scraping trending hashtags from X/Twitter
Uses undetected-chromedriver to bypass bot detection
"""

import os
import time
import logging
import random
import pickle
from datetime import datetime
from pathlib import Path
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scraper.log', encoding='utf-8'),
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


class TwitterHashtagScraper:
    """
    Scraper class for extracting trending hashtags from Twitter/X
    """
    
    def __init__(self, headless=False):
        """
        Initialize the scraper
        
        Args:
            headless (bool): Run browser in headless mode
        """
        self.headless = headless
        self.driver = None
        self.username = os.getenv('TWITTER_USERNAME')
        self.password = os.getenv('TWITTER_PASSWORD')
        self.region = os.getenv('REGION', 'United States')  # For documentation only
        self.max_retries = int(os.getenv('MAX_RETRIES', 3))
        self.cookies_file = 'data/twitter_cookies.pkl'
        
        if not self.username or not self.password:
            raise ValueError("Twitter credentials not found. Please set TWITTER_USERNAME and TWITTER_PASSWORD in .env file")
        
        logger.info(f"Target region: {self.region} (Use VPN to match this location)")
    
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
    
    def human_type(self, element, text):
        """
        Type text with human-like delays
        
        Args:
            element: Web element to type into
            text: Text to type
        """
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
    
    def save_cookies(self):
        """
        Save browser cookies to file for future sessions
        """
        try:
            cookies = self.driver.get_cookies()
            Path(self.cookies_file).parent.mkdir(parents=True, exist_ok=True)
            with open(self.cookies_file, 'wb') as file:
                pickle.dump(cookies, file)
            logger.info(f"Cookies saved to {self.cookies_file}")
        except Exception as e:
            logger.error(f"Error saving cookies: {str(e)}")
    
    def load_cookies(self):
        """
        Load cookies from file and add them to the browser
        
        Returns:
            bool: True if cookies loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(self.cookies_file):
                logger.info("No saved cookies found. Will need to login.")
                return False
            
            logger.info("Loading saved cookies...")
            with open(self.cookies_file, 'rb') as file:
                cookies = pickle.load(file)
            
            # Navigate to Twitter first (required before adding cookies)
            self.driver.get('https://twitter.com')
            time.sleep(2)
            
            # Add each cookie to the browser
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    logger.warning(f"Could not add cookie: {str(e)}")
            
            logger.info("Cookies loaded successfully")
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
            
            # Check if we're on the home page (logged in) or redirected to login
            current_url = self.driver.current_url
            if 'home' in current_url:
                logger.info("Already logged in via cookies!")
                return True
            else:
                logger.info("Cookies expired or invalid. Need to login.")
                return False
                
        except Exception as e:
            logger.error(f"Error checking login status: {str(e)}")
            return False
    
    def login_to_twitter(self):
        """
        Authenticate to Twitter/X with human-like behavior
        
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            logger.info("Navigating to Twitter login page...")
            self.driver.get('https://twitter.com/i/flow/login')
            time.sleep(random.uniform(3, 5))
            
            # Wait for username field
            logger.info("Entering username...")
            username_input = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]'))
            )
            time.sleep(random.uniform(0.5, 1.5))
            self.human_type(username_input, self.username)
            time.sleep(random.uniform(0.5, 1))
            username_input.send_keys(Keys.RETURN)
            time.sleep(random.uniform(2, 4))
            
            # Check for unusual activity (phone/email verification)
            try:
                unusual_activity = self.driver.find_element(By.XPATH, '//*[contains(text(), "Enter your phone number") or contains(text(), "unusual")]')
                logger.warning("Unusual activity detected. Manual intervention may be required.")
                time.sleep(5)
                # Could add logic here to handle verification if needed
            except NoSuchElementException:
                pass
            
            # Wait for password field
            logger.info("Entering password...")
            password_input = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="password"]'))
            )
            time.sleep(random.uniform(0.5, 1.5))
            self.human_type(password_input, self.password)
            time.sleep(random.uniform(0.5, 1))
            password_input.send_keys(Keys.RETURN)
            time.sleep(random.uniform(5, 7))
            
            # Verify login success by checking URL or home page element
            WebDriverWait(self.driver, 30).until(
                EC.url_contains('home')
            )
            
            logger.info("Login successful!")
            time.sleep(random.uniform(2, 3))
            
            # Save cookies for future use
            self.save_cookies()
            
            return True
            
        except TimeoutException as e:
            logger.error(f"Login timeout: {str(e)}")
            logger.info(f"Current URL: {self.driver.current_url}")
            return False
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return False
    
    def get_trending_hashtags(self, count=5):
        """
        Scrape trending hashtags from Twitter/X
        
        Args:
            count (int): Number of trending hashtags to retrieve
            
        Returns:
            list: List of trending hashtags
        """
        try:
            logger.info(f"Navigating to trending page...")
            self.driver.get('https://twitter.com/explore/tabs/trending')
            time.sleep(5)
            
            hashtags = []
            
            # Wait for trending section to load
            logger.info("Waiting for trending section to load...")
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, '//div[@data-testid="trend"]'))
            )
            
            # Find all trending items
            trending_elements = self.driver.find_elements(By.XPATH, '//div[@data-testid="trend"]')
            
            logger.info(f"Found {len(trending_elements)} trending items")
            
            # Extract hashtags
            skip_phrases = [
                'Trending in', 'Only on X', 'Trending', 'posts', 'post', 
                'K posts', 'M posts', '·', 'Promoted'
            ]
            
            for idx, element in enumerate(trending_elements):
                try:
                    # Get all text from spans
                    spans = element.find_elements(By.TAG_NAME, 'span')
                    
                    # Look for the main trending topic (usually a larger, prominent span)
                    for span in spans:
                        text = span.text.strip()
                        
                        # Skip empty or very short text
                        if not text or len(text) < 2:
                            continue
                        
                        # Skip UI labels and metadata
                        if any(skip in text for skip in skip_phrases):
                            continue
                        
                        # Skip pure numbers or numbers with K/M
                        if text.replace('.', '').replace('K', '').replace('M', '').replace(',', '').isdigit():
                            continue
                        
                        # Valid trending topic found
                        if text not in hashtags:
                            hashtags.append(text)
                            logger.info(f"Found trending topic {len(hashtags)}: {text}")
                            break
                    
                    if len(hashtags) >= count:
                        break
                        
                except Exception as e:
                    logger.warning(f"Error extracting hashtag {idx + 1}: {str(e)}")
                    continue
            
            logger.info(f"Successfully extracted {len(hashtags)} trending hashtags")
            return hashtags[:count]
            
        except TimeoutException:
            logger.error("Timeout waiting for trending section to load")
            return []
        except Exception as e:
            logger.error(f"Error getting trending hashtags: {str(e)}")
            return []
    
    def save_hashtags(self, hashtags, filepath='data/trending_hashtags.txt'):
        """
        Save hashtags to text file
        
        Args:
            hashtags (list): List of hashtags to save
            filepath (str): Path to output file
        """
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# Trending Hashtags - {timestamp}\n")
                f.write(f"# Total: {len(hashtags)}\n\n")
                
                for idx, hashtag in enumerate(hashtags, 1):
                    f.write(f"{idx}. {hashtag}\n")
            
            logger.info(f"Saved {len(hashtags)} hashtags to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving hashtags: {str(e)}")
            raise
    
    def scrape_with_retry(self, count=5):
        """
        Main scraping method with retry logic
        
        Args:
            count (int): Number of hashtags to scrape
            
        Returns:
            list: List of trending hashtags
        """
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Scraping attempt {attempt + 1}/{self.max_retries}")
                
                # Setup driver
                self.setup_driver()
                
                # Try to use saved cookies first
                cookies_loaded = self.load_cookies()
                
                if cookies_loaded and self.is_logged_in():
                    logger.info("Using saved session (no login required)")
                else:
                    # Login if cookies don't work
                    logger.info("Logging in with credentials...")
                    if not self.login_to_twitter():
                        raise Exception("Login failed")
                
                # Get trending hashtags (location determined by VPN/IP)
                hashtags = self.get_trending_hashtags(count)
                
                if not hashtags:
                    raise Exception("No hashtags found")
                
                return hashtags
                
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < self.max_retries - 1:
                    wait_time = (attempt + 1) * 10
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error("All retry attempts exhausted")
                    return []
            
            finally:
                if self.driver:
                    self.driver.quit()
                    logger.info("WebDriver closed")
    
    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")


def main():
    """
    Main execution function
    """
    logger.info("="*50)
    logger.info("Starting Twitter Hashtag Scraper")
    logger.info("="*50)
    logger.info("NOTE: Connect to VPN in your target region before running!")
    logger.info("="*50)
    
    try:
        # Get headless mode from environment or default to False
        headless_mode = os.getenv('HEADLESS_MODE', 'False').lower() == 'true'
        
        # Initialize scraper
        scraper = TwitterHashtagScraper(headless=headless_mode)
        
        # Scrape trending hashtags
        hashtags = scraper.scrape_with_retry(count=5)
        
        if hashtags:
            # Save to file
            scraper.save_hashtags(hashtags)
            
            logger.info("="*50)
            logger.info("Scraping completed successfully!")
            logger.info(f"Collected {len(hashtags)} trending hashtags:")
            for idx, hashtag in enumerate(hashtags, 1):
                logger.info(f"  {idx}. {hashtag}")
            logger.info("="*50)
        else:
            logger.error("Failed to collect any hashtags")
    
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise
    
    finally:
        logger.info("Scraper execution finished")


if __name__ == "__main__":
    main()


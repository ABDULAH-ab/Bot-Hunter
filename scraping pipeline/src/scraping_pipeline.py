"""
Master Scraping Pipeline - Integrates hashtag and tweet scrapers
Runs the complete data collection workflow:
1. Scrape trending hashtags
2. Scrape tweets for those hashtags
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our scrapers
from hashtag_scraper import TwitterHashtagScraper
from tweet_scraper import SeleniumTweetScraper
from tweet_db import TweetDB 

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pipeline.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Fix console encoding (Windows)
import sys
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass


class ScrapingPipeline:
    """
    Master pipeline that orchestrates hashtag and tweet scraping
    """
    
    def __init__(self):
        """Initialize the pipeline"""
        self.hashtags_file = 'data/trending_hashtags.txt'
        self.tweets_output = None
        
    def run_hashtag_scraper(self):
        """
        Step 1: Run hashtag scraper to get trending hashtags
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("="*70)
            logger.info("STEP 1: SCRAPING TRENDING HASHTAGS")
            logger.info("="*70)
            
            # Get headless mode from env
            headless_mode = os.getenv('HEADLESS_MODE', 'False').lower() == 'true'
            
            # Initialize hashtag scraper
            scraper = TwitterHashtagScraper(headless=headless_mode)
            
            # Scrape hashtags
            hashtags = scraper.scrape_with_retry(count=15)
            
            if hashtags and len(hashtags) > 0:
                # Save to file
                scraper.save_hashtags(hashtags, self.hashtags_file)
                
                logger.info("="*70)
                logger.info(f"✓ STEP 1 COMPLETED: Collected {len(hashtags)} trending hashtags")
                logger.info("="*70)
                return True
            else:
                logger.error("✗ STEP 1 FAILED: No hashtags collected")
                return False
                
        except Exception as e:
            logger.error(f"✗ STEP 1 FAILED: {str(e)}")
            return False
    
    def run_tweet_scraper(self):
        """
        Step 2: Run tweet scraper to collect tweets for hashtags
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("")
            logger.info("="*70)
            logger.info("STEP 2: SCRAPING TWEETS FOR HASHTAGS")
            logger.info("="*70)
            
            # Check if hashtags file exists
            if not os.path.exists(self.hashtags_file):
                logger.error(f"✗ Hashtags file not found: {self.hashtags_file}")
                return False
            
            # Initialize tweet scraper
            scraper = SeleniumTweetScraper()
            
            # Scrape tweets
            self.tweets_output = scraper.scrape_all_hashtags()
            
            if self.tweets_output and os.path.exists(self.tweets_output):
                logger.info("="*70)
                logger.info(f"✓ STEP 2 COMPLETED: Tweets saved to {self.tweets_output}")
                logger.info("="*70)
                logger.info("STEP 3 : Saving data in Database")
                logger.info("="*70)
                db = TweetDB()
                db.save_json(self.tweets_output)
                logger.info("="*70)
                return True
            else:
                logger.error("✗ STEP 2 FAILED: No tweets collected")
                return False
                
        except Exception as e:
            logger.error(f"✗ STEP 2 FAILED: {str(e)}")
            return False
    
    def run(self):
        """
        Execute the complete scraping pipeline
        
        Returns:
            dict: Results summary
        """
        start_time = datetime.now()
        
        logger.info("")
        logger.info("╔"+"═"*68+"╗")
        logger.info("║" + " "*15 + "TWITTER SCRAPING PIPELINE STARTED" + " "*20 + "║")
        logger.info("╚"+"═"*68+"╝")
        logger.info("")
        logger.info(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Target: 15 trending hashtags → 2000 tweets each = 10,000 tweets")
        logger.info("")
        
        results = {
            'success': False,
            'hashtags_collected': False,
            'tweets_collected': False,
            'tweets_file': None,
            'start_time': start_time,
            'end_time': None,
            'duration': None
        }
        
        try:
            # Step 1: Scrape hashtags
            hashtags_success = self.run_hashtag_scraper()
            results['hashtags_collected'] = hashtags_success
            
            if not hashtags_success:
                logger.error("Pipeline stopped: Hashtag scraping failed")
                return results
            
            # Small delay between steps
            import time
            logger.info("⏸ Waiting 10 seconds before starting tweet scraping...")
            time.sleep(10)
            
            # Step 2: Scrape tweets
            tweets_success = self.run_tweet_scraper()
            results['tweets_collected'] = tweets_success
            results['tweets_file'] = self.tweets_output
            
            if tweets_success:
                results['success'] = True
            
        except Exception as e:
            logger.error(f"Pipeline error: {str(e)}")
            results['success'] = False
        
        finally:
            # Calculate duration
            end_time = datetime.now()
            results['end_time'] = end_time
            results['duration'] = end_time - start_time
            
            # Print summary
            self.print_summary(results)
        
        return results
    
    def print_summary(self, results):
        """
        Print pipeline execution summary
        
        Args:
            results (dict): Results dictionary
        """
        logger.info("")
        logger.info("╔"+"═"*68+"╗")
        logger.info("║" + " "*20 + "PIPELINE SUMMARY" + " "*32 + "║")
        logger.info("╚"+"═"*68+"╝")
        logger.info("")
        
        # Status
        if results['success']:
            logger.info("Status: ✓ SUCCESS - Pipeline completed successfully!")
        else:
            logger.info("Status: ✗ FAILED - Pipeline encountered errors")
        
        logger.info("")
        logger.info("Steps Completed:")
        logger.info(f"  1. Hashtag Scraping: {'✓ Success' if results['hashtags_collected'] else '✗ Failed'}")
        logger.info(f"  2. Tweet Scraping:   {'✓ Success' if results['tweets_collected'] else '✗ Failed'}")
        
        logger.info("")
        logger.info("Output Files:")
        logger.info(f"  - Hashtags: data/trending_hashtags.txt")
        if results['tweets_file']:
            logger.info(f"  - Tweets:   {results['tweets_file']}")
        
        logger.info("")
        logger.info("Timing:")
        logger.info(f"  - Start:    {results['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"  - End:      {results['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"  - Duration: {results['duration']}")
        
        logger.info("")
        logger.info("╔"+"═"*68+"╗")
        logger.info("║" + " "*18 + "PIPELINE EXECUTION FINISHED" + " "*23 + "║")
        logger.info("╚"+"═"*68+"╝")
        logger.info("")


def main():
    """Main execution function"""
    try:
        # Create logs directory if doesn't exist
        Path('logs').mkdir(exist_ok=True)
        
        # Initialize and run pipeline
        pipeline = ScrapingPipeline()
        results = pipeline.run()
        
        # Exit with appropriate code
        sys.exit(0 if results['success'] else 1)
        
    except KeyboardInterrupt:
        logger.info("")
        logger.warning("⚠ Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()


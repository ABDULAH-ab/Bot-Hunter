"""
Daily Scheduler for Twitter Scraping Pipeline
Runs the pipeline at a specified time in US timezone
"""

import os
import sys
import time
import logging
import schedule
from datetime import datetime
import pytz
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Fix console encoding (Windows)
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass


class PipelineScheduler:
    """
    Scheduler for running the scraping pipeline daily at a specific time
    """
    
    def __init__(self, schedule_time="02:00"):
        """
        Initialize scheduler
        
        Args:
            schedule_time (str): Time to run in HH:MM format (24-hour) in your LOCAL time
        """
        self.schedule_time = schedule_time
        self.is_running = False
        
        logger.info(f"Scheduler initialized: {schedule_time} (Local Time)")
    
    def run_pipeline(self):
        """
        Execute the scraping pipeline
        """
        if self.is_running:
            logger.warning("Pipeline is already running, skipping this execution")
            return
        
        try:
            self.is_running = True
            
            # Get current local time
            now = datetime.now()
            logger.info("="*70)
            logger.info(f"SCHEDULED RUN STARTED: {now.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("="*70)
            
            # Import and run pipeline
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
            from scraping_pipeline import ScrapingPipeline
            
            pipeline = ScrapingPipeline()
            results = pipeline.run()
            
            if results['success']:
                logger.info("✓ Scheduled pipeline run completed successfully!")
            else:
                logger.error("✗ Scheduled pipeline run failed!")
            
        except Exception as e:
            logger.error(f"Error during scheduled run: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        
        finally:
            self.is_running = False
            logger.info("="*70)
            logger.info("Scheduled run finished. Waiting for next run...")
            logger.info("="*70)
    
    def start(self):
        """
        Start the scheduler (runs continuously)
        """
        logger.info("")
        logger.info("╔"+"═"*68+"╗")
        logger.info("║" + " "*15 + "TWITTER SCRAPING SCHEDULER" + " "*27 + "║")
        logger.info("╚"+"═"*68+"╝")
        logger.info("")
        
        logger.info(f"Scheduled Time: {self.schedule_time} (Your Local Time)")
        logger.info("Press Ctrl+C to stop the scheduler")
        logger.info("")
        
        # Schedule the daily job using LOCAL time
        schedule.every().day.at(self.schedule_time).do(self.run_pipeline)
        
        # Show next run time
        next_run = schedule.next_run()
        if next_run:
            logger.info(f"Next scheduled run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        
        logger.info("")
        logger.info("Scheduler is now running... (Keep this window open)")
        logger.info("")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        except KeyboardInterrupt:
            logger.info("")
            logger.warning("⚠ Scheduler stopped by user")
            logger.info("")


def main():
    """Main execution function"""
    try:
        # Create logs directory
        Path('logs').mkdir(exist_ok=True)
        
        # Get schedule time from environment or use default
        schedule_time = os.getenv('SCHEDULE_TIME', '02:00')  # 2 AM by default (Local Time)
        
        # Initialize and start scheduler
        scheduler = PipelineScheduler(schedule_time=schedule_time)
        scheduler.start()
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()



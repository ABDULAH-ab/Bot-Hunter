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
    
    def __init__(self, schedule_time="02:00", timezone="America/New_York"):
        """
        Initialize scheduler
        
        Args:
            schedule_time (str): Time to run in HH:MM format (24-hour)
            timezone (str): Timezone for scheduling (US timezones)
        """
        self.schedule_time = schedule_time
        self.timezone = pytz.timezone(timezone)
        self.is_running = False
        
        logger.info(f"Scheduler initialized: {schedule_time} {timezone}")
    
    def run_pipeline(self):
        """
        Execute the scraping pipeline
        """
        if self.is_running:
            logger.warning("Pipeline is already running, skipping this execution")
            return
        
        try:
            self.is_running = True
            
            # Get current time in specified timezone
            now = datetime.now(self.timezone)
            logger.info("="*70)
            logger.info(f"SCHEDULED RUN STARTED: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
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
    
    def convert_to_local_time(self):
        """
        Convert the target timezone's schedule time to local system time
        
        Returns:
            str: Local time in HH:MM format
        """
        from datetime import datetime, timedelta
        
        # Get current date
        now = datetime.now()
        
        # Parse the schedule time
        hour, minute = map(int, self.schedule_time.split(':'))
        
        # Create a datetime in the target timezone
        target_time = self.timezone.localize(
            datetime(now.year, now.month, now.day, hour, minute, 0)
        )
        
        # Convert to local timezone
        local_time = target_time.astimezone()
        
        # Return in HH:MM format
        return local_time.strftime('%H:%M')
    
    def start(self):
        """
        Start the scheduler (runs continuously)
        """
        logger.info("")
        logger.info("╔"+"═"*68+"╗")
        logger.info("║" + " "*15 + "TWITTER SCRAPING SCHEDULER" + " "*27 + "║")
        logger.info("╚"+"═"*68+"╝")
        logger.info("")
        
        # Convert target time to local time
        local_schedule_time = self.convert_to_local_time()
        
        logger.info(f"Target Schedule: {self.schedule_time} {self.timezone}")
        logger.info(f"Your Local Time: {local_schedule_time} (Pakistan Time)")
        logger.info("Press Ctrl+C to stop the scheduler")
        logger.info("")
        
        # Schedule the daily job using LOCAL time
        schedule.every().day.at(local_schedule_time).do(self.run_pipeline)
        
        # Show next run time
        next_run = schedule.next_run()
        if next_run:
            logger.info(f"Next scheduled run: {next_run.strftime('%Y-%m-%d %H:%M:%S')} (Local Time)")
        
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
        schedule_time = os.getenv('SCHEDULE_TIME', '02:00')  # 2 AM by default
        timezone = os.getenv('SCHEDULE_TIMEZONE', 'America/New_York')  # EST/EDT
        
        # Available US timezones:
        # America/New_York      - Eastern Time (EST/EDT)
        # America/Chicago       - Central Time (CST/CDT)
        # America/Denver        - Mountain Time (MST/MDT)
        # America/Los_Angeles   - Pacific Time (PST/PDT)
        
        # Initialize and start scheduler
        scheduler = PipelineScheduler(schedule_time=schedule_time, timezone=timezone)
        scheduler.start()
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()



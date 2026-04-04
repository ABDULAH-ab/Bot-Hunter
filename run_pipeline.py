"""
Quick launcher for the scraping pipeline
Run this file to execute the complete workflow
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run pipeline
from scraping_pipeline import main

if __name__ == "__main__":
    main()



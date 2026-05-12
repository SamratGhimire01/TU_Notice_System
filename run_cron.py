"""
run_cron.py — Run the scraper manually from the command line.

Usage:
    python run_cron.py
"""
import asyncio
from app.scraper import run_scraper


if __name__ == "__main__":
    result = asyncio.run(run_scraper())
    print(result)
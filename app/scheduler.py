"""
Background task scheduler for periodic scraping.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timezone
from loguru import logger
from typing import Optional

from app.config import settings
from app.scraper import scraper
from app.database import db
from app.models import ScrapeStats


class TaskScheduler:
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.last_scrape: Optional[datetime] = None
        self.last_stats: Optional[ScrapeStats] = None
        self.is_running = False
        logger.info("TaskScheduler initialized")
    
    def scrape_job(self):
        logger.info("Starting scheduled scrape job")
        
        try:
    
            articles, stats = scraper.scrape_sync()
            
            new_count = db.add_articles(articles)
            
            stats.new_articles = new_count
            
            db_stats = db.get_stats()
            stats.total_articles = db_stats.get('total_articles', 0)
            
            # Store metadata
            self.last_scrape = datetime.utcnow()
            self.last_stats = stats
            
            logger.success(
                f"Scrape job completed: {new_count} new articles added, "
                f"{stats.total_articles} total in database"
            )
            
        except Exception as e:
            logger.error(f"Scrape job failed: {e}", exc_info=True)
    
    def start(self, run_immediately: bool = True):

        if self.is_running:
            logger.warning("Scheduler already running")
            return
        
        # Add scraping job
        self.scheduler.add_job(
            self.scrape_job,
            trigger=IntervalTrigger(hours=settings.scrape_interval_hours),
            id='scrape_feeds',
            name='Scrape RSS Feeds',
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=3600  # 1 hour grace time
        )
        
        # Start scheduler
        self.scheduler.start()
        self.is_running = True
        
        logger.info(
            f"Scheduler started with interval: {settings.scrape_interval_hours} hours"
        )
        
       
        if run_immediately:
            logger.info("Running initial scrape...")
            self.scrape_job()
    
    def stop(self):
        if not self.is_running:
            logger.warning("Scheduler not running")
            return
        
        self.scheduler.shutdown(wait=True)
        self.is_running = False
        logger.info("Scheduler stopped")
    
    def trigger_manual_scrape(self) -> ScrapeStats:
        logger.info("Manual scrape triggered")
        self.scrape_job()
        return self.last_stats
    
    def get_next_run_time(self) -> Optional[datetime]:
        job = self.scheduler.get_job('scrape_feeds')
        if job:
            return job.next_run_time
        return None
    
    def get_status(self) -> dict:
        next_run = self.get_next_run_time()
        
        return {
            'is_running': self.is_running,
            'last_scrape': self.last_scrape.isoformat() if self.last_scrape else None,
            'next_scrape': next_run.isoformat() if next_run else None,
            'interval_hours': settings.scrape_interval_hours,
            'last_stats': self.last_stats.dict() if self.last_stats else None
        }


# Global scheduler instance
task_scheduler = TaskScheduler()
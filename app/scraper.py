"""
Web scraper for cybersecurity RSS feeds.
"""
import feedparser
import requests
import asyncio
import aiohttp
import nest_asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from loguru import logger
from time import time


nest_asyncio.apply()

from app.config import settings
from app.models import VulnerabilityArticle, CategoryEnum, ScrapeStats
from app.utils import generate_article_id, categorize_article, sanitize_text, parse_date


class FeedScraper:    
    def __init__(self):
        self.feeds = settings.rss_feeds
        self.timeout = settings.request_timeout
        self.max_retries = settings.max_retries
        self.retry_delay = settings.retry_delay
        logger.info(f"FeedScraper initialized with {len(self.feeds)} feeds")
    
    async def fetch_feed(self, session: aiohttp.ClientSession, feed_url: str) -> Optional[Dict[str, Any]]:
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Fetching feed: {feed_url} (attempt {attempt + 1})")
                
                async with session.get(
                    feed_url,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    headers={'User-Agent': 'CybersecNewsAggregator/1.0'}
                ) as response:
                    if response.status == 200:
                        content = await response.text()
                        feed = feedparser.parse(content)
                        
                        if feed.bozo:
                            logger.warning(f"Feed parsing warning for {feed_url}: {feed.bozo_exception}")
                        
                        logger.success(f"Successfully fetched {feed_url}")
                        return feed
                    else:
                        logger.warning(f"HTTP {response.status} for {feed_url}")
                        
            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching {feed_url} (attempt {attempt + 1})")
            except Exception as e:
                logger.error(f"Error fetching {feed_url}: {e}")
            
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay)
        
        logger.error(f"Failed to fetch {feed_url} after {self.max_retries} attempts")
        return None
    
    def parse_entry(self, entry: Dict, source_name: str) -> Optional[VulnerabilityArticle]:
        try:
            # Extract basic fields
            title = sanitize_text(entry.get('title', 'No Title'), max_length=500)
            link = entry.get('link', '')
            
            if not link:
                logger.warning(f"Entry missing link: {title}")
                return None
            
            # Parse published date - BULLETPROOF
            published_str = entry.get('published', entry.get('updated', ''))
            published = parse_date(published_str) if published_str else datetime.now(timezone.utc).replace(tzinfo=None)
            
            # Extract description/summary
            description = entry.get('summary', entry.get('description', ''))
            if hasattr(description, 'value'):
                description = description.value
            description = sanitize_text(description, max_length=2000)
            
            # Generate unique ID
            article_id = generate_article_id(title, link)
            
            # Categorize
            category = categorize_article(title, description)
            
            # Current time in naive UTC
            scraped_at = datetime.now(timezone.utc).replace(tzinfo=None)
            
            article = VulnerabilityArticle(
                id=article_id,
                title=title,
                link=link,
                published=published,
                source=source_name,
                description=description,
                scraped_at=scraped_at,
                category=category
            )
            
            return article
            
        except Exception as e:
            logger.error(f"Failed to parse entry: {e}")
            return None
    
    async def scrape_all_feeds(self) -> tuple[List[VulnerabilityArticle], ScrapeStats]:

        start_time = time()
        all_articles = []
        successful_feeds = 0
        failed_feeds = 0
        
        # Calculate date range: today and yesterday
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)
        
        logger.info(f"Starting scrape of {len(self.feeds)} feeds")
        logger.info(f"Filtering articles from {yesterday_start.date()} to {today_start.date()}")
        
        async with aiohttp.ClientSession() as session:
            # Fetch all feeds concurrently
            tasks = [self.fetch_feed(session, feed_url) for feed_url in self.feeds]
            feeds = await asyncio.gather(*tasks)
            
            # Process each feed
            for feed_url, feed in zip(self.feeds, feeds):
                if feed is None:
                    failed_feeds += 1
                    continue
                
                try:
                    # Get source name from feed
                    source_name = feed.feed.get('title', feed_url.split('/')[2])
                    
                    # Parse entries
                    entries = feed.entries[:50]  # Limit to 50 most recent
                    logger.info(f"Processing {len(entries)} entries from {source_name}")
                    
                    filtered_count = 0
                    for entry in entries:
                        article = self.parse_entry(entry, source_name)
                        if article:
                            # Filter: only include articles from today or yesterday
                            article_date = article.published.replace(tzinfo=None)
                            if article_date >= yesterday_start:
                                all_articles.append(article)
                                filtered_count += 1
                    
                    logger.info(f"Kept {filtered_count} articles from last 2 days from {source_name}")
                    successful_feeds += 1
                    
                except Exception as e:
                    logger.error(f"Error processing feed {feed_url}: {e}")
                    failed_feeds += 1
        
        duration = time() - start_time
        
        stats = ScrapeStats(
            total_feeds=len(self.feeds),
            successful_feeds=successful_feeds,
            failed_feeds=failed_feeds,
            new_articles=len(all_articles),
            total_articles=0,  # Will be updated after DB insertion
            scraped_at=datetime.utcnow(),
            duration_seconds=round(duration, 2)
        )
        
        logger.info(
            f"Scrape completed: {successful_feeds}/{len(self.feeds)} feeds successful, "
            f"{len(all_articles)} articles found in {duration:.2f}s"
        )
        
        return all_articles, stats
    
    def scrape_sync(self) -> tuple[List[VulnerabilityArticle], ScrapeStats]:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.scrape_all_feeds())


# Global scraper instance
scraper = FeedScraper()
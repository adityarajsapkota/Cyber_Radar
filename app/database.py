"""
CSV database management with thread-safe operations and bulletproof date handling.
"""
import pandas as pd
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from threading import Lock
from loguru import logger
from app.config import settings
from app.models import VulnerabilityArticle, CategoryEnum


class CSVDatabase:
    """Thread-safe CSV database manager."""
    
    def __init__(self, file_path: str = None):
        """
        Initialize database manager.
        
        Args:
            file_path: Path to CSV file (uses settings default if None)
        """
        self.file_path = Path(file_path or settings.csv_file_path)
        self.lock = Lock()
        self._ensure_file_exists()
        logger.info(f"CSV Database initialized: {self.file_path}")
    
    def _ensure_file_exists(self):
        """Create CSV file with headers if it doesn't exist."""
        if not self.file_path.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            df = pd.DataFrame(columns=[
                'id', 'title', 'link', 'published', 'source',
                'description', 'scraped_at', 'category'
            ])
            df.to_csv(self.file_path, index=False)
            logger.info(f"Created new CSV file: {self.file_path}")
    
    def add_articles(self, articles: List[VulnerabilityArticle]) -> int:
        """
        Add new articles to the database.
        
        Args:
            articles: List of articles to add
        
        Returns:
            Number of new articles added (excluding duplicates)
        """
        if not articles:
            return 0
        
        with self.lock:
            try:
                # Read existing data
                existing_df = pd.read_csv(self.file_path)
                existing_ids = set(existing_df['id'].tolist()) if not existing_df.empty else set()
                
                # Filter out duplicates
                new_articles = [
                    article for article in articles
                    if article.id not in existing_ids
                ]
                
                if not new_articles:
                    logger.info("No new articles to add (all duplicates)")
                    return 0
                
                # Convert to DataFrame
                new_df = pd.DataFrame([
                    {
                        'id': article.id,
                        'title': article.title,
                        'link': str(article.link),
                        'published': article.published.isoformat(),
                        'source': article.source,
                        'description': article.description,
                        'scraped_at': article.scraped_at.isoformat(),
                        'category': article.category.value
                    }
                    for article in new_articles
                ])
                
                # Append new articles
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                
                # Sort by published date (newest first) - BULLETPROOF DATE PARSING
                try:
                    combined_df['published'] = pd.to_datetime(
                        combined_df['published'], 
                        format='ISO8601',
                        errors='coerce'
                    )
                except:
                    # Fallback to mixed format
                    combined_df['published'] = pd.to_datetime(
                        combined_df['published'], 
                        errors='coerce'
                    )
                
                # Remove rows with invalid dates (NaT)
                before_drop = len(combined_df)
                combined_df = combined_df.dropna(subset=['published'])
                after_drop = len(combined_df)
                if before_drop > after_drop:
                    logger.warning(f"Dropped {before_drop - after_drop} articles with invalid dates")
                
                combined_df = combined_df.sort_values('published', ascending=False)
                
                # Keep only max_records
                if len(combined_df) > settings.max_records:
                    combined_df = combined_df.head(settings.max_records)
                    logger.info(f"Trimmed database to {settings.max_records} records")
                
                # Save back to CSV
                combined_df.to_csv(self.file_path, index=False)
                
                logger.info(f"Added {len(new_articles)} new articles to database")
                return len(new_articles)
                
            except Exception as e:
                logger.error(f"Failed to add articles: {e}")
                raise
    
    def get_articles(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        source: Optional[str] = None,
        category: Optional[CategoryEnum] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        search: Optional[str] = None
    ) -> tuple[List[VulnerabilityArticle], int]:
        """
        Retrieve articles with filtering options.
        
        Args:
            limit: Maximum number of articles to return
            offset: Number of articles to skip
            source: Filter by source
            category: Filter by category
            start_date: Filter by start date
            end_date: Filter by end date
            search: Search in title and description
        
        Returns:
            Tuple of (articles list, total count)
        """
        with self.lock:
            try:
                df = pd.read_csv(self.file_path)
                
                if df.empty:
                    return [], 0
                
                # Convert date columns - BULLETPROOF DATE PARSING
                try:
                    df['published'] = pd.to_datetime(
                        df['published'], 
                        format='ISO8601',
                        errors='coerce'
                    )
                    df['scraped_at'] = pd.to_datetime(
                        df['scraped_at'], 
                        format='ISO8601',
                        errors='coerce'
                    )
                except:
                    # Fallback
                    df['published'] = pd.to_datetime(df['published'], errors='coerce')
                    df['scraped_at'] = pd.to_datetime(df['scraped_at'], errors='coerce')
                
                # Drop rows with invalid dates
                df = df.dropna(subset=['published'])
                
                # Apply filters
                if source:
                    df = df[df['source'].str.lower() == source.lower()]
                
                if category:
                    df = df[df['category'] == category.value]
                
                if start_date:
                    df = df[df['published'] >= start_date]
                
                if end_date:
                    df = df[df['published'] <= end_date]
                
                if search:
                    search_lower = search.lower()
                    df = df[
                        df['title'].str.lower().str.contains(search_lower, na=False) |
                        df['description'].str.lower().str.contains(search_lower, na=False)
                    ]
                
                total_count = len(df)
                
                # Apply pagination
                df = df.iloc[offset:]
                if limit:
                    df = df.head(limit)
                
                # Convert to models
                articles = []
                for _, row in df.iterrows():
                    try:
                        article = VulnerabilityArticle(
                            id=row['id'],
                            title=row['title'],
                            link=row['link'],
                            published=row['published'],
                            source=row['source'],
                            description=row['description'],
                            scraped_at=row['scraped_at'],
                            category=CategoryEnum(row['category'])
                        )
                        articles.append(article)
                    except Exception as e:
                        logger.warning(f"Failed to parse article: {e}")
                        continue
                
                return articles, total_count
                
            except Exception as e:
                logger.error(f"Failed to retrieve articles: {e}")
                raise
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self.lock:
            try:
                df = pd.read_csv(self.file_path)
                
                if df.empty:
                    return {
                        'total_articles': 0,
                        'sources': [],
                        'categories': {},
                        'oldest_article': None,
                        'newest_article': None
                    }
                
                # BULLETPROOF DATE PARSING
                try:
                    df['published'] = pd.to_datetime(
                        df['published'], 
                        format='ISO8601',
                        errors='coerce'
                    )
                except:
                    df['published'] = pd.to_datetime(df['published'], errors='coerce')
                
                df = df.dropna(subset=['published'])
                
                return {
                    'total_articles': len(df),
                    'sources': df['source'].unique().tolist(),
                    'categories': df['category'].value_counts().to_dict(),
                    'oldest_article': df['published'].min().isoformat() if len(df) > 0 else None,
                    'newest_article': df['published'].max().isoformat() if len(df) > 0 else None
                }
                
            except Exception as e:
                logger.error(f"Failed to get stats: {e}")
                return {}
    
    def clear(self):
        """Clear all data from the database."""
        with self.lock:
            df = pd.DataFrame(columns=[
                'id', 'title', 'link', 'published', 'source',
                'description', 'scraped_at', 'category'
            ])
            df.to_csv(self.file_path, index=False)
            logger.warning("Database cleared")


# Global database instance
db = CSVDatabase() 
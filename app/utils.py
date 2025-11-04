"""
Utility functions for logging, hashing, and common operations.
"""
import hashlib
import sys
import datetime
from datetime import datetime as dt
from loguru import logger
from pathlib import Path
from typing import Optional
from app.config import settings
from app.models import CategoryEnum


def setup_logging():
    # Remove default logger
    logger.remove()
    
    # Console handler with colors
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True,
    )
    
    # File handler with rotation
    logger.add(
        settings.log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.log_level,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
    )
    
    logger.info("Logging configured successfully")


def generate_article_id(title: str, link: str) -> str:
    content = f"{title}{link}".encode('utf-8')
    return hashlib.sha256(content).hexdigest()[:16]


def categorize_article(title: str, description: str) -> CategoryEnum:
    text = f"{title} {description}".lower()
    
    # Define keywords for each category
    category_keywords = {
        CategoryEnum.VULNERABILITY: ['cve', 'vulnerability', 'vuln', 'flaw', 'weakness'],
        CategoryEnum.THREAT: ['threat', 'attack', 'campaign', 'apt', 'actor'],
        CategoryEnum.BREACH: ['breach', 'leak', 'data breach', 'compromised', 'hacked'],
        CategoryEnum.ADVISORY: ['advisory', 'alert', 'warning', 'bulletin'],
        CategoryEnum.MALWARE: ['malware', 'ransomware', 'trojan', 'virus', 'backdoor'],
        CategoryEnum.EXPLOIT: ['exploit', 'poc', 'proof of concept', '0-day', 'zero-day'],
    }
    
    # Score each category
    scores = {}
    for category, keywords in category_keywords.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > 0:
            scores[category] = score
    
    # Return category with highest score, or OTHER if no matches
    if scores:
        return max(scores, key=scores.get)
    return CategoryEnum.OTHER


def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    if not text:
        return ""
    
    # Remove excess whitespace
    text = ' '.join(text.split())
    
    # Truncate if needed
    if max_length and len(text) > max_length:
        text = text[:max_length-3] + "..."
    
    return text


def parse_date(date_str: str) -> dt:
    from dateutil import parser
    
    # Handle empty/None
    if not date_str or not isinstance(date_str, str):
        logger.warning(f"Empty or invalid date string, using current UTC time")
        return dt.now(datetime.timezone.utc).replace(tzinfo=None)
    
    try:
        # Parse with dateutil (handles 99% of formats)
        parsed = parser.parse(date_str)
        
        # Convert to UTC and remove timezone info (naive)
        if parsed.tzinfo is not None:
            # Has timezone - convert to UTC
            utc_time = parsed.astimezone(datetime.timezone.utc)
            return utc_time.replace(tzinfo=None)
        else:
            # No timezone - assume UTC
            return parsed
            
    except (ValueError, TypeError, parser.ParserError) as e:
        logger.warning(f"Failed to parse date '{date_str}': {e}, using current UTC time")
        return dt.now(datetime.timezone.utc).replace(tzinfo=None)


def get_uptime(start_time: datetime) -> float:
    return (datetime.utcnow() - start_time).total_seconds()


def validate_url(url: str) -> bool:
    from urllib.parse import urlparse
    
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False
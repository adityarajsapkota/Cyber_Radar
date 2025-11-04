"""
Configuration management using Pydantic Settings.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    app_name: str = Field(default="Cybersecurity News Scraper")
    app_version: str = Field(default="1.0.0")
    environment: str = Field(default="Development")
    
    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    reload: bool = Field(default=False)
    
    # Data
    csv_file_path: str = Field(default="data/vulnerabilities.csv")
    max_records: int = Field(default=10000)
    scrape_interval_hours: int = Field(default=24)
    
    # Logging
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="logs/app.log")
    
    # API Security
    api_key_enabled: bool = Field(default=True)
    api_key: str = Field(default="")
    rate_limit_requests: int = Field(default=100)
    rate_limit_period: int = Field(default=60)

    #Time Frame
    scrape_days_back: int = Field(default=2, description="Number of days back to scrape")
    
    # RSS Feed Sources
    rss_feeds: List[str] = Field(default=[
        "https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss.xml",
        "https://www.bleepingcomputer.com/feed/",
        "https://www.securityweek.com/feed/",
        "https://thehackernews.com/feeds/posts/default",
        "https://www.cisa.gov/cybersecurity-advisories/all.xml",
        "https://krebsonsecurity.com/feed/",
    ])
    
    # Request timeouts and retries
    request_timeout: int = Field(default=30)
    max_retries: int = Field(default=3)
    retry_delay: int = Field(default=5)
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"
    
    def create_directories(self):
        """Create necessary directories if they don't exist."""
        Path("data").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        
        # Create empty CSV with headers if it doesn't exist
        csv_path = Path(self.csv_file_path)
        if not csv_path.exists():
            import pandas as pd
            df = pd.DataFrame(columns=[
                'id', 'title', 'link', 'published', 'source', 
                'description', 'scraped_at', 'category'
            ])
            df.to_csv(csv_path, index=False)


# Global settings instance
settings = Settings()
settings.create_directories()
"""
Pydantic models for data validation and API schemas.
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum


class CategoryEnum(str, Enum):
    VULNERABILITY = "vulnerability"
    THREAT = "threat"
    BREACH = "breach"
    ADVISORY = "advisory"
    NEWS = "news"
    MALWARE = "malware"
    EXPLOIT = "exploit"
    OTHER = "other"


class VulnerabilityArticle(BaseModel):
    id: str = Field(..., description="Unique identifier for the article")
    title: str = Field(..., description="Article title")
    link: HttpUrl = Field(..., description="URL to the full article")
    published: datetime = Field(..., description="Publication date")
    source: str = Field(..., description="Source feed name")
    description: str = Field(..., description="Article summary/description")
    scraped_at: datetime = Field(..., description="When the article was scraped")
    category: CategoryEnum = Field(default=CategoryEnum.OTHER, description="Article category")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "nvd_cve_2024_12345",
                "title": "CVE-2024-12345: Critical Vulnerability in Popular Framework",
                "link": "https://nvd.nist.gov/vuln/detail/CVE-2024-12345",
                "published": "2024-01-15T10:30:00Z",
                "source": "NVD",
                "description": "A critical vulnerability has been discovered...",
                "scraped_at": "2024-01-15T12:00:00Z",
                "category": "vulnerability"
            }
        }


class VulnerabilityResponse(BaseModel):

    total: int = Field(..., description="Total number of articles")
    count: int = Field(..., description="Number of articles returned")
    articles: List[VulnerabilityArticle] = Field(..., description="List of articles")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 1500,
                "count": 10,
                "articles": []
            }
        }


class ScrapeStats(BaseModel):

    total_feeds: int = Field(..., description="Total number of feeds processed")
    successful_feeds: int = Field(..., description="Number of successful feeds")
    failed_feeds: int = Field(..., description="Number of failed feeds")
    new_articles: int = Field(..., description="Number of new articles added")
    total_articles: int = Field(..., description="Total articles in database")
    scraped_at: datetime = Field(..., description="When scraping was performed")
    duration_seconds: float = Field(..., description="Time taken to scrape")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_feeds": 6,
                "successful_feeds": 5,
                "failed_feeds": 1,
                "new_articles": 42,
                "total_articles": 1500,
                "scraped_at": "2024-01-15T12:00:00Z",
                "duration_seconds": 15.5
            }
        }


class HealthResponse(BaseModel):

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    last_scrape: Optional[datetime] = Field(None, description="Last scraping time")
    total_articles: int = Field(..., description="Total articles in database")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "uptime_seconds": 3600.5,
                "last_scrape": "2024-01-15T12:00:00Z",
                "total_articles": 1500
            }
        }


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Invalid API key",
                "error_code": "AUTH_001",
                "timestamp": "2024-01-15T12:00:00Z"
            }
        }
"""
FastAPI application with endpoints for vulnerability news.
"""
from fastapi import FastAPI, HTTPException, Query, Depends, Security, status
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional, List
from loguru import logger

from app.config import settings
from app.models import (
    VulnerabilityResponse, VulnerabilityArticle, ScrapeStats,
    HealthResponse, ErrorResponse, CategoryEnum
)
from app.database import db
from app.scheduler import task_scheduler
from app.utils import setup_logging, get_uptime

# Setup logging
setup_logging()

# Application start time
APP_START_TIME = datetime.utcnow()

# API Key security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key if enabled."""
    if not settings.api_key_enabled:
        return None
    
    if api_key is None or api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )
    return api_key


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    task_scheduler.start(run_immediately=True)
    yield
    # Shutdown
    logger.info("Shutting down application")
    task_scheduler.stop()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API for cybersecurity vulnerability news aggregation",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "documentation": "/docs",
        "health_check": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    stats = db.get_stats()
    
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        uptime_seconds=get_uptime(APP_START_TIME),
        last_scrape=task_scheduler.last_scrape,
        total_articles=stats.get('total_articles', 0)
    )


@app.get(
    "/api/v1/vulnerabilities",
    response_model=VulnerabilityResponse,
    tags=["Vulnerabilities"]
)
async def get_vulnerabilities(
    limit: int = Query(default=100, ge=1, le=1000, description="Number of articles to return"),
    offset: int = Query(default=0, ge=0, description="Number of articles to skip"),
    source: Optional[str] = Query(default=None, description="Filter by source name"),
    category: Optional[CategoryEnum] = Query(default=None, description="Filter by category"),
    start_date: Optional[str] = Query(default=None, description="Filter by start date (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"),
    end_date: Optional[str] = Query(default=None, description="Filter by end date (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"),
    search: Optional[str] = Query(default=None, description="Search in title and description"),
    api_key: str = Depends(verify_api_key)
):
    """
    - **start_date**: Filter articles published after this date (formats: "2025-11-05" or "2025-11-05T10:30:00")
    - **end_date**: Filter articles published before this date (formats: "2025-11-05" or "2025-11-05T23:59:59")
    """
    try:
       
        parsed_start_date = None
        parsed_end_date = None
        
        if start_date:
            try:
                
                parsed_start_date = datetime.fromisoformat(start_date)
            except ValueError:
                try:
                   
                    parsed_start_date = datetime.fromisoformat(f"{start_date}T00:00:00")
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid start_date format. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS"
                    )
        
        if end_date:
            try:
                
                parsed_end_date = datetime.fromisoformat(end_date)
            except ValueError:
                try:
                    
                    parsed_end_date = datetime.fromisoformat(f"{end_date}T23:59:59")
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid end_date format. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS"
                    )
        
        articles, total = db.get_articles(
            limit=limit,
            offset=offset,
            source=source,
            category=category,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            search=search
        )
        
        return VulnerabilityResponse(
            total=total,
            count=len(articles),
            articles=articles
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving vulnerabilities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve vulnerabilities"
        )


@app.get(
    "/api/v1/vulnerabilities/{article_id}",
    response_model=VulnerabilityArticle,
    tags=["Vulnerabilities"]
)
async def get_vulnerability_by_id(
    article_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get a specific vulnerability article by ID."""
    try:
        articles, _ = db.get_articles(limit=1)
        
        # Find article by ID
        for article in articles:
            if article.id == article_id:
                return article
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with ID '{article_id}' not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving article: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve article"
        )


@app.get("/api/v1/sources", response_model=List[str], tags=["Sources"])
async def get_sources(api_key: str = Depends(verify_api_key)):
    """Get list of all available sources."""
    try:
        stats = db.get_stats()
        return stats.get('sources', [])
    except Exception as e:
        logger.error(f"Error retrieving sources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sources"
        )


@app.get("/api/v1/categories", response_model=List[str], tags=["Categories"])
async def get_categories(api_key: str = Depends(verify_api_key)):
    """Get list of all available categories."""
    return [category.value for category in CategoryEnum]


@app.get("/api/v1/stats", tags=["Statistics"])
async def get_statistics(api_key: str = Depends(verify_api_key)):
    """Get database and scraping statistics."""
    try:
        db_stats = db.get_stats()
        scheduler_status = task_scheduler.get_status()
        
        return {
            "database": db_stats,
            "scheduler": scheduler_status,
            "uptime_seconds": get_uptime(APP_START_TIME)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )


@app.post("/api/v1/scrape", response_model=ScrapeStats, tags=["Admin"])
async def trigger_manual_scrape(api_key: str = Depends(verify_api_key)):
    """
    Manually trigger a scrape operation (admin only).
    
    This will scrape all configured feeds immediately.
    """
    try:
        logger.info("Manual scrape triggered via API")
        stats = task_scheduler.trigger_manual_scrape()
        return stats
        
    except Exception as e:
        logger.error(f"Error during manual scrape: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute scrape"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )
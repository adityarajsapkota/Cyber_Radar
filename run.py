"""
Application entry point.
"""
import uvicorn
from app.config import settings
from app.utils import setup_logging

if __name__ == "__main__":
    # Setup logging
    setup_logging()
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
        access_log=True
    )
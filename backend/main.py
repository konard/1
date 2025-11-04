"""
Main FastAPI application for YouTube Analytics System.
"""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from backend.storage import init_db, get_session
from backend.api import router
from backend.alerts import AlertService
from backend.data_ingestion import DataIngestionService
from backend.storage.models import Channel, Video
from sqlmodel import Session, select

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Background scheduler for periodic tasks
scheduler = BackgroundScheduler()


def check_alerts_job():
    """Background job to check all alerts"""
    logger.info("Running alerts check job...")
    try:
        with next(get_session()) as session:
            alert_service = AlertService(session)
            alert_service.check_all_alerts()
    except Exception as e:
        logger.error(f"Error in alerts check job: {e}")


def refresh_channels_job():
    """Background job to refresh channel data"""
    logger.info("Running channel refresh job...")
    try:
        with next(get_session()) as session:
            channels = session.exec(select(Channel)).all()
            ingestion = DataIngestionService(session)

            for channel in channels:
                try:
                    ingestion.refresh_channel(channel)
                except Exception as e:
                    logger.error(f"Error refreshing channel {channel.id}: {e}")

    except Exception as e:
        logger.error(f"Error in channel refresh job: {e}")


def refresh_videos_job():
    """Background job to refresh video stats (create snapshots)"""
    logger.info("Running video refresh job...")
    try:
        with next(get_session()) as session:
            videos = session.exec(select(Video)).all()
            ingestion = DataIngestionService(session)

            for video in videos:
                try:
                    ingestion.refresh_video(video)
                except Exception as e:
                    logger.error(f"Error refreshing video {video.id}: {e}")

    except Exception as e:
        logger.error(f"Error in video refresh job: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    # Startup
    logger.info("Starting YouTube Analytics API...")

    # Initialize database
    init_db()
    logger.info("Database initialized")

    # Configure background jobs
    snapshot_interval = int(os.getenv("SNAPSHOT_UPDATE_INTERVAL", "1440"))  # Default: 24 hours
    channel_refresh_interval = int(os.getenv("CHANNEL_REFRESH_INTERVAL", "60"))  # Default: 1 hour

    # Add jobs to scheduler
    scheduler.add_job(
        check_alerts_job,
        trigger=IntervalTrigger(minutes=10),  # Check alerts every 10 minutes
        id="check_alerts",
        name="Check alerts",
        replace_existing=True,
    )

    scheduler.add_job(
        refresh_channels_job,
        trigger=IntervalTrigger(minutes=channel_refresh_interval),
        id="refresh_channels",
        name="Refresh channels",
        replace_existing=True,
    )

    scheduler.add_job(
        refresh_videos_job,
        trigger=IntervalTrigger(minutes=snapshot_interval),
        id="refresh_videos",
        name="Refresh videos and create snapshots",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Background scheduler started")

    yield

    # Shutdown
    logger.info("Shutting down...")
    scheduler.shutdown()
    logger.info("Background scheduler stopped")


# Create FastAPI app
app = FastAPI(
    title="YouTube Analytics API",
    description="API for YouTube channel and video analytics",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "YouTube Analytics API",
        "version": "1.0.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))

    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info",
    )

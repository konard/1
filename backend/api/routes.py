"""
API routes for the YouTube analytics system.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select, desc

from backend.storage import get_session, Channel, Video, Alert, AlertEvent
from backend.data_ingestion import DataIngestionService
from backend.analytics import AnalyticsCalculator
from backend.alerts import AlertService
from backend.api_key_manager import get_key_manager
from backend.api.schemas import (
    ChannelCreate,
    ChannelResponse,
    VideoResponse,
    VideoWithChannel,
    ChannelAnalytics,
    TrendingVideo,
    AlertCreate,
    AlertResponse,
    AlertEventResponse,
    StatsSnapshot,
    APIKeyStatsResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Channels endpoints

@router.post("/channels", response_model=ChannelResponse, status_code=201)
async def create_channel(
    channel_data: ChannelCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    """
    Import a YouTube channel from a URL.

    This will:
    1. Fetch channel data from YouTube API
    2. Store channel in database
    3. Import videos (if enabled)
    4. Create initial stats snapshots
    """
    try:
        ingestion = DataIngestionService(session)

        channel = ingestion.import_channel_from_url(
            url=channel_data.url,
            is_own_channel=channel_data.is_own_channel,
            import_videos=channel_data.import_videos,
            max_videos=channel_data.max_videos,
        )

        if not channel:
            raise HTTPException(status_code=400, detail="Could not import channel from URL")

        return channel

    except Exception as e:
        logger.error(f"Error creating channel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/channels", response_model=List[ChannelResponse])
async def list_channels(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """List all channels"""
    channels = session.exec(
        select(Channel).order_by(desc(Channel.created_at)).offset(skip).limit(limit)
    ).all()
    return channels


@router.get("/channels/{channel_id}", response_model=ChannelResponse)
async def get_channel(
    channel_id: int,
    session: Session = Depends(get_session)
):
    """Get a specific channel by ID"""
    channel = session.get(Channel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel


@router.post("/channels/{channel_id}/refresh", response_model=ChannelResponse)
async def refresh_channel(
    channel_id: int,
    session: Session = Depends(get_session)
):
    """Refresh channel data from YouTube API"""
    channel = session.get(Channel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    ingestion = DataIngestionService(session)
    channel = ingestion.refresh_channel(channel)

    return channel


@router.delete("/channels/{channel_id}", status_code=204)
async def delete_channel(
    channel_id: int,
    session: Session = Depends(get_session)
):
    """Delete a channel and all its data"""
    channel = session.get(Channel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    session.delete(channel)
    session.commit()


# Videos endpoints

@router.get("/channels/{channel_id}/videos", response_model=List[VideoResponse])
async def list_channel_videos(
    channel_id: int,
    skip: int = 0,
    limit: int = 50,
    sort_by: str = "published_at",
    session: Session = Depends(get_session)
):
    """List videos for a specific channel"""
    # Verify channel exists
    channel = session.get(Channel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    # Get videos
    query = select(Video).where(Video.channel_id == channel_id)

    if sort_by == "published_at":
        query = query.order_by(desc(Video.published_at))
    elif sort_by == "view_count":
        query = query.order_by(desc(Video.view_count))
    elif sort_by == "like_count":
        query = query.order_by(desc(Video.like_count))

    videos = session.exec(query.offset(skip).limit(limit)).all()

    # Calculate metrics
    analytics = AnalyticsCalculator(session)
    video_list = []

    for video in videos:
        video_dict = VideoResponse.model_validate(video).model_dump()
        video_dict["engagement_rate"] = analytics.calculate_engagement_rate(video)
        video_dict["views_per_day"] = analytics.calculate_views_per_day(video)
        video_list.append(VideoResponse(**video_dict))

    return video_list


@router.get("/videos/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: int,
    session: Session = Depends(get_session)
):
    """Get a specific video by ID"""
    video = session.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    analytics = AnalyticsCalculator(session)
    video_dict = VideoResponse.model_validate(video).model_dump()
    video_dict["engagement_rate"] = analytics.calculate_engagement_rate(video)
    video_dict["views_per_day"] = analytics.calculate_views_per_day(video)

    return VideoResponse(**video_dict)


@router.get("/videos/{video_id}/history", response_model=List[StatsSnapshot])
async def get_video_history(
    video_id: int,
    days: int = 30,
    session: Session = Depends(get_session)
):
    """Get historical stats for a video"""
    video = session.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    analytics = AnalyticsCalculator(session)
    history = analytics.get_video_history(video, days=days)

    return [StatsSnapshot(**item) for item in history]


# Analytics endpoints

@router.get("/channels/{channel_id}/analytics", response_model=ChannelAnalytics)
async def get_channel_analytics(
    channel_id: int,
    session: Session = Depends(get_session)
):
    """Get comprehensive analytics for a channel"""
    channel = session.get(Channel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    analytics = AnalyticsCalculator(session)
    analytics_data = analytics.get_channel_analytics(channel)

    return ChannelAnalytics(**analytics_data)


@router.get("/trending/videos", response_model=List[TrendingVideo])
async def get_trending_videos(
    hours: int = 24,
    min_growth: int = 0,
    limit: int = 20,
    session: Session = Depends(get_session)
):
    """Get trending videos based on view count growth"""
    analytics = AnalyticsCalculator(session)
    trending = analytics.get_trending_videos(
        hours=hours,
        min_growth=min_growth,
        limit=limit
    )

    result = []
    for item in trending:
        video_dict = VideoResponse.model_validate(item["video"]).model_dump()
        video_dict["engagement_rate"] = analytics.calculate_engagement_rate(item["video"])
        video_dict["views_per_day"] = analytics.calculate_views_per_day(item["video"])

        result.append(TrendingVideo(
            video=VideoResponse(**video_dict),
            channel=ChannelResponse.model_validate(item["channel"]),
            view_growth=item["view_growth"],
            like_growth=item["like_growth"],
            comment_growth=item["comment_growth"],
            time_window_hours=item["time_window_hours"],
        ))

    return result


# Alerts endpoints

@router.post("/alerts", response_model=AlertResponse, status_code=201)
async def create_alert(
    alert_data: AlertCreate,
    session: Session = Depends(get_session)
):
    """Create a new alert"""
    alert_service = AlertService(session)

    alert = alert_service.create_alert(
        name=alert_data.name,
        alert_type=alert_data.alert_type,
        threshold_field=alert_data.threshold_field,
        threshold_value=alert_data.threshold_value,
        time_window_hours=alert_data.time_window_hours,
        channel_id=alert_data.channel_id,
    )

    return alert


@router.get("/alerts", response_model=List[AlertResponse])
async def list_alerts(
    session: Session = Depends(get_session)
):
    """List all alerts"""
    alerts = session.exec(select(Alert).order_by(desc(Alert.created_at))).all()
    return alerts


@router.get("/alerts/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    session: Session = Depends(get_session)
):
    """Get a specific alert"""
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.put("/alerts/{alert_id}/toggle", response_model=AlertResponse)
async def toggle_alert(
    alert_id: int,
    session: Session = Depends(get_session)
):
    """Toggle alert active status"""
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_active = not alert.is_active
    session.commit()
    session.refresh(alert)

    return alert


@router.delete("/alerts/{alert_id}", status_code=204)
async def delete_alert(
    alert_id: int,
    session: Session = Depends(get_session)
):
    """Delete an alert"""
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    session.delete(alert)
    session.commit()


@router.get("/alert-events", response_model=List[AlertEventResponse])
async def list_alert_events(
    limit: int = 50,
    unread_only: bool = False,
    session: Session = Depends(get_session)
):
    """List recent alert events"""
    alert_service = AlertService(session)
    events = alert_service.get_recent_events(limit=limit, unread_only=unread_only)

    return events


@router.put("/alert-events/{event_id}/read", response_model=AlertEventResponse)
async def mark_event_read(
    event_id: int,
    session: Session = Depends(get_session)
):
    """Mark an alert event as read"""
    alert_service = AlertService(session)
    alert_service.mark_event_read(event_id)

    event = session.get(AlertEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return event


# System endpoints

@router.get("/system/api-keys", response_model=List[APIKeyStatsResponse])
async def get_api_key_stats():
    """Get API key usage statistics"""
    key_manager = get_key_manager()
    stats = key_manager.get_stats()

    return [APIKeyStatsResponse(**stat) for stat in stats]


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

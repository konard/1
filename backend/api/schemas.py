"""
Pydantic schemas for API requests and responses.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# Channel schemas

class ChannelCreate(BaseModel):
    """Request schema for creating/importing a channel"""
    url: str = Field(..., description="YouTube channel or video URL")
    is_own_channel: bool = Field(default=False, description="Whether this is user's own channel")
    import_videos: bool = Field(default=True, description="Whether to import videos")
    max_videos: int = Field(default=50, description="Maximum number of videos to import")


class ChannelResponse(BaseModel):
    """Response schema for channel data"""
    id: int
    youtube_channel_id: str
    title: str
    description: Optional[str]
    custom_url: Optional[str]
    thumbnail_url: Optional[str]
    view_count: int
    subscriber_count: int
    video_count: int
    is_own_channel: bool
    created_at: datetime
    updated_at: datetime
    last_sync_at: Optional[datetime]

    class Config:
        from_attributes = True


# Video schemas

class VideoResponse(BaseModel):
    """Response schema for video data"""
    id: int
    youtube_video_id: str
    channel_id: int
    title: str
    description: Optional[str]
    published_at: datetime
    thumbnail_url: Optional[str]
    duration: Optional[str]
    view_count: int
    like_count: int
    comment_count: int
    engagement_rate: Optional[float] = None
    views_per_day: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VideoWithChannel(VideoResponse):
    """Video response with channel info"""
    channel: ChannelResponse


# Analytics schemas

class ChannelAnalytics(BaseModel):
    """Channel analytics response"""
    channel_id: int
    channel_name: str
    total_videos: int
    total_views: int
    total_likes: int
    total_comments: int
    avg_views_per_video: float
    avg_likes_per_video: float
    avg_comments_per_video: float
    avg_engagement_rate: float
    best_video: Optional[dict]
    growth_24h: Optional[dict]


class TrendingVideo(BaseModel):
    """Trending video response"""
    video: VideoResponse
    channel: ChannelResponse
    view_growth: int
    like_growth: int
    comment_growth: int
    time_window_hours: int


# Alert schemas

class AlertCreate(BaseModel):
    """Request schema for creating an alert"""
    name: str
    alert_type: str = Field(..., description="'viral_video', 'engagement_drop', etc.")
    threshold_field: str = Field(..., description="'view_count', 'engagement_rate', etc.")
    threshold_value: float
    time_window_hours: int = Field(default=24)
    channel_id: Optional[int] = None


class AlertResponse(BaseModel):
    """Response schema for alert data"""
    id: int
    name: str
    alert_type: str
    threshold_field: str
    threshold_value: float
    time_window_hours: int
    channel_id: Optional[int]
    is_active: bool
    last_triggered_at: Optional[datetime]
    trigger_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class AlertEventResponse(BaseModel):
    """Response schema for alert event data"""
    id: int
    alert_id: int
    video_id: Optional[int]
    channel_id: Optional[int]
    message: str
    metric_value: float
    triggered_at: datetime
    is_read: bool

    class Config:
        from_attributes = True


# Stats schemas

class StatsSnapshot(BaseModel):
    """Stats snapshot response"""
    date: str
    views: int
    likes: int
    comments: int


class APIKeyStatsResponse(BaseModel):
    """API key usage stats"""
    key_preview: str
    total_requests: int
    quota_used_estimate: int
    last_used: Optional[str]
    is_disabled: bool
    disabled_until: Optional[str]

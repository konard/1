from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship, Column, DateTime
from sqlalchemy import Index


class Channel(SQLModel, table=True):
    """YouTube channel model"""
    __tablename__ = "channels"

    id: Optional[int] = Field(default=None, primary_key=True)
    youtube_channel_id: str = Field(unique=True, index=True)

    # Snippet data
    title: str
    description: Optional[str] = None
    custom_url: Optional[str] = None
    published_at: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=True)))
    country: Optional[str] = None
    thumbnail_url: Optional[str] = None

    # Statistics (latest)
    view_count: int = 0
    subscriber_count: int = 0
    hidden_subscriber_count: bool = False
    video_count: int = 0

    # Playlists
    uploads_playlist_id: Optional[str] = None

    # Metadata
    is_own_channel: bool = False  # Mark if this is user's own channel
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))
    last_sync_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))

    # Relationships
    videos: list["Video"] = Relationship(back_populates="channel")
    stats_snapshots: list["ChannelStatsSnapshot"] = Relationship(back_populates="channel")


class Video(SQLModel, table=True):
    """YouTube video model"""
    __tablename__ = "videos"

    id: Optional[int] = Field(default=None, primary_key=True)
    youtube_video_id: str = Field(unique=True, index=True)
    channel_id: int = Field(foreign_key="channels.id", index=True)

    # Snippet data
    title: str
    description: Optional[str] = None
    published_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    thumbnail_url: Optional[str] = None

    # Content details
    duration: Optional[str] = None  # ISO 8601 duration

    # Statistics (latest)
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))
    last_sync_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))

    # Relationships
    channel: Channel = Relationship(back_populates="videos")
    stats_snapshots: list["VideoStatsSnapshot"] = Relationship(back_populates="video")

    __table_args__ = (
        Index("idx_video_channel_published", "channel_id", "published_at"),
    )


class VideoStatsSnapshot(SQLModel, table=True):
    """Daily snapshots of video statistics"""
    __tablename__ = "video_stats_snapshots"

    id: Optional[int] = Field(default=None, primary_key=True)
    video_id: int = Field(foreign_key="videos.id", index=True)

    # Statistics at this point in time
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0

    # Timestamp
    captured_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))

    # Relationships
    video: Video = Relationship(back_populates="stats_snapshots")

    __table_args__ = (
        Index("idx_snapshot_video_captured", "video_id", "captured_at"),
    )


class ChannelStatsSnapshot(SQLModel, table=True):
    """Daily snapshots of channel statistics"""
    __tablename__ = "channel_stats_snapshots"

    id: Optional[int] = Field(default=None, primary_key=True)
    channel_id: int = Field(foreign_key="channels.id", index=True)

    # Statistics at this point in time
    view_count: int = 0
    subscriber_count: int = 0
    video_count: int = 0

    # Timestamp
    captured_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))

    # Relationships
    channel: Channel = Relationship(back_populates="stats_snapshots")

    __table_args__ = (
        Index("idx_snapshot_channel_captured", "channel_id", "captured_at"),
    )


class Alert(SQLModel, table=True):
    """Alert configuration and history"""
    __tablename__ = "alerts"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Alert definition
    name: str
    alert_type: str  # 'viral_video', 'engagement_drop', 'custom'

    # Conditions (JSON-like structure stored as strings for SQLite compatibility)
    channel_id: Optional[int] = Field(default=None, foreign_key="channels.id")
    threshold_value: float
    threshold_field: str  # 'view_count', 'engagement_rate', etc.
    time_window_hours: int = 24

    # State
    is_active: bool = True
    last_triggered_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    trigger_count: int = 0

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))


class AlertEvent(SQLModel, table=True):
    """Alert trigger events history"""
    __tablename__ = "alert_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    alert_id: int = Field(foreign_key="alerts.id", index=True)

    # Event details
    video_id: Optional[int] = Field(default=None, foreign_key="videos.id")
    channel_id: Optional[int] = Field(default=None, foreign_key="channels.id")

    message: str
    metric_value: float

    # Metadata
    triggered_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))
    is_read: bool = False

    __table_args__ = (
        Index("idx_alert_event_triggered", "triggered_at"),
    )

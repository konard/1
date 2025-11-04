"""
Data ingestion service for importing and updating YouTube channels and videos.
"""

import logging
from datetime import datetime
from typing import Optional, List
from sqlmodel import Session, select

from backend.storage.models import (
    Channel,
    Video,
    VideoStatsSnapshot,
    ChannelStatsSnapshot,
)
from backend.data_ingestion.youtube_client import get_youtube_client

logger = logging.getLogger(__name__)


class DataIngestionService:
    """Service for importing and syncing YouTube data"""

    def __init__(self, session: Session):
        self.session = session
        self.youtube = get_youtube_client()

    def import_channel_from_url(
        self,
        url: str,
        is_own_channel: bool = False,
        import_videos: bool = True,
        max_videos: int = 50
    ) -> Optional[Channel]:
        """
        Import a channel from a YouTube URL.

        Args:
            url: YouTube channel or video URL
            is_own_channel: Whether this is user's own channel
            import_videos: Whether to import videos
            max_videos: Maximum number of videos to import initially

        Returns:
            Channel model instance or None
        """
        logger.info(f"Importing channel from URL: {url}")

        # Fetch channel data from YouTube
        channel_data = self.youtube.get_channel_by_url(url)

        if not channel_data:
            logger.error(f"Could not fetch channel from URL: {url}")
            return None

        # Parse channel data
        channel_id = channel_data["id"]
        snippet = channel_data.get("snippet", {})
        statistics = channel_data.get("statistics", {})
        content_details = channel_data.get("contentDetails", {})

        # Check if channel already exists
        existing = self.session.exec(
            select(Channel).where(Channel.youtube_channel_id == channel_id)
        ).first()

        if existing:
            logger.info(f"Channel {channel_id} already exists, updating...")
            channel = self._update_channel(existing, channel_data)
        else:
            logger.info(f"Creating new channel {channel_id}...")
            channel = Channel(
                youtube_channel_id=channel_id,
                title=snippet.get("title", ""),
                description=snippet.get("description"),
                custom_url=snippet.get("customUrl"),
                published_at=self._parse_datetime(snippet.get("publishedAt")),
                country=snippet.get("country"),
                thumbnail_url=snippet.get("thumbnails", {}).get("default", {}).get("url"),
                view_count=int(statistics.get("viewCount", 0)),
                subscriber_count=int(statistics.get("subscriberCount", 0)),
                hidden_subscriber_count=statistics.get("hiddenSubscriberCount", False),
                video_count=int(statistics.get("videoCount", 0)),
                uploads_playlist_id=content_details.get("relatedPlaylists", {}).get("uploads"),
                is_own_channel=is_own_channel,
                last_sync_at=datetime.utcnow(),
            )
            self.session.add(channel)

        self.session.commit()
        self.session.refresh(channel)

        # Create initial stats snapshot
        self._create_channel_snapshot(channel)

        # Import videos if requested
        if import_videos and channel.uploads_playlist_id:
            self.import_channel_videos(channel, max_videos=max_videos)

        logger.info(f"Successfully imported channel: {channel.title}")
        return channel

    def _update_channel(self, channel: Channel, channel_data: dict) -> Channel:
        """Update existing channel with fresh data"""
        snippet = channel_data.get("snippet", {})
        statistics = channel_data.get("statistics", {})

        channel.title = snippet.get("title", channel.title)
        channel.description = snippet.get("description", channel.description)
        channel.custom_url = snippet.get("customUrl", channel.custom_url)
        channel.country = snippet.get("country", channel.country)
        channel.thumbnail_url = snippet.get("thumbnails", {}).get("default", {}).get("url", channel.thumbnail_url)
        channel.view_count = int(statistics.get("viewCount", 0))
        channel.subscriber_count = int(statistics.get("subscriberCount", 0))
        channel.hidden_subscriber_count = statistics.get("hiddenSubscriberCount", False)
        channel.video_count = int(statistics.get("videoCount", 0))
        channel.updated_at = datetime.utcnow()
        channel.last_sync_at = datetime.utcnow()

        return channel

    def import_channel_videos(self, channel: Channel, max_videos: int = 50) -> int:
        """
        Import videos for a channel.

        Args:
            channel: Channel model instance
            max_videos: Maximum number of videos to import

        Returns:
            Number of videos imported
        """
        if not channel.uploads_playlist_id:
            logger.warning(f"Channel {channel.youtube_channel_id} has no uploads playlist")
            return 0

        logger.info(f"Importing videos for channel: {channel.title}")

        # Fetch videos from YouTube
        videos_data = self.youtube.get_channel_videos(
            channel.youtube_channel_id,
            channel.uploads_playlist_id,
            max_results=max_videos
        )

        imported_count = 0

        for video_data in videos_data:
            try:
                video = self._import_video(channel, video_data)
                if video:
                    imported_count += 1
            except Exception as e:
                logger.error(f"Error importing video: {e}")
                continue

        logger.info(f"Imported {imported_count} videos for channel {channel.title}")
        return imported_count

    def _import_video(self, channel: Channel, video_data: dict) -> Optional[Video]:
        """Import or update a single video"""
        video_id = video_data["id"]
        snippet = video_data.get("snippet", {})
        content_details = video_data.get("contentDetails", {})
        statistics = video_data.get("statistics", {})

        # Check if video already exists
        existing = self.session.exec(
            select(Video).where(Video.youtube_video_id == video_id)
        ).first()

        if existing:
            # Update existing video
            existing.title = snippet.get("title", existing.title)
            existing.description = snippet.get("description", existing.description)
            existing.thumbnail_url = snippet.get("thumbnails", {}).get("default", {}).get("url", existing.thumbnail_url)
            existing.duration = content_details.get("duration", existing.duration)
            existing.view_count = int(statistics.get("viewCount", 0))
            existing.like_count = int(statistics.get("likeCount", 0))
            existing.comment_count = int(statistics.get("commentCount", 0))
            existing.updated_at = datetime.utcnow()
            existing.last_sync_at = datetime.utcnow()
            video = existing
        else:
            # Create new video
            video = Video(
                youtube_video_id=video_id,
                channel_id=channel.id,
                title=snippet.get("title", ""),
                description=snippet.get("description"),
                published_at=self._parse_datetime(snippet.get("publishedAt")),
                thumbnail_url=snippet.get("thumbnails", {}).get("default", {}).get("url"),
                duration=content_details.get("duration"),
                view_count=int(statistics.get("viewCount", 0)),
                like_count=int(statistics.get("likeCount", 0)),
                comment_count=int(statistics.get("commentCount", 0)),
                last_sync_at=datetime.utcnow(),
            )
            self.session.add(video)

        self.session.commit()
        self.session.refresh(video)

        # Create initial stats snapshot
        self._create_video_snapshot(video)

        return video

    def refresh_channel(self, channel: Channel) -> Channel:
        """
        Refresh channel data from YouTube.

        Args:
            channel: Channel to refresh

        Returns:
            Updated channel
        """
        logger.info(f"Refreshing channel: {channel.title}")

        channel_data = self.youtube.get_channel_by_id(channel.youtube_channel_id)

        if not channel_data:
            logger.error(f"Could not fetch channel {channel.youtube_channel_id}")
            return channel

        channel = self._update_channel(channel, channel_data)
        self.session.commit()
        self.session.refresh(channel)

        # Create snapshot
        self._create_channel_snapshot(channel)

        return channel

    def refresh_video(self, video: Video) -> Video:
        """
        Refresh video data from YouTube.

        Args:
            video: Video to refresh

        Returns:
            Updated video
        """
        video_data = self.youtube.get_video_by_id(video.youtube_video_id)

        if not video_data:
            logger.error(f"Could not fetch video {video.youtube_video_id}")
            return video

        statistics = video_data.get("statistics", {})
        video.view_count = int(statistics.get("viewCount", 0))
        video.like_count = int(statistics.get("likeCount", 0))
        video.comment_count = int(statistics.get("commentCount", 0))
        video.updated_at = datetime.utcnow()
        video.last_sync_at = datetime.utcnow()

        self.session.commit()
        self.session.refresh(video)

        # Create snapshot
        self._create_video_snapshot(video)

        return video

    def _create_channel_snapshot(self, channel: Channel):
        """Create a stats snapshot for a channel"""
        snapshot = ChannelStatsSnapshot(
            channel_id=channel.id,
            view_count=channel.view_count,
            subscriber_count=channel.subscriber_count,
            video_count=channel.video_count,
            captured_at=datetime.utcnow(),
        )
        self.session.add(snapshot)
        self.session.commit()

    def _create_video_snapshot(self, video: Video):
        """Create a stats snapshot for a video"""
        snapshot = VideoStatsSnapshot(
            video_id=video.id,
            view_count=video.view_count,
            like_count=video.like_count,
            comment_count=video.comment_count,
            captured_at=datetime.utcnow(),
        )
        self.session.add(snapshot)
        self.session.commit()

    @staticmethod
    def _parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO 8601 datetime string"""
        if not dt_str:
            return None
        try:
            # Remove 'Z' and parse
            if dt_str.endswith('Z'):
                dt_str = dt_str[:-1]
            return datetime.fromisoformat(dt_str)
        except Exception:
            return None

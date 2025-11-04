"""
Analytics calculator for computing metrics and trends.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlmodel import Session, select, and_, desc

from backend.storage.models import (
    Channel,
    Video,
    VideoStatsSnapshot,
    ChannelStatsSnapshot,
)

logger = logging.getLogger(__name__)


class AnalyticsCalculator:
    """Calculator for various analytics metrics"""

    def __init__(self, session: Session):
        self.session = session

    @staticmethod
    def calculate_engagement_rate(video: Video) -> float:
        """
        Calculate engagement rate for a video.

        engagement_rate = (likes + comments) / views

        Args:
            video: Video model instance

        Returns:
            Engagement rate (0.0 to 1.0+)
        """
        if video.view_count == 0:
            return 0.0

        engagement = video.like_count + video.comment_count
        return engagement / video.view_count

    @staticmethod
    def calculate_views_per_day(video: Video) -> float:
        """
        Calculate average views per day since publication.

        Args:
            video: Video model instance

        Returns:
            Average views per day
        """
        if not video.published_at:
            return 0.0

        days_since_publish = (datetime.utcnow() - video.published_at).days
        if days_since_publish == 0:
            days_since_publish = 1  # Avoid division by zero for today's videos

        return video.view_count / days_since_publish

    def get_video_growth_24h(self, video: Video) -> Optional[int]:
        """
        Get view count growth in last 24 hours.

        Args:
            video: Video model instance

        Returns:
            View count increase or None if no data
        """
        # Get snapshot from 24 hours ago (or closest)
        time_24h_ago = datetime.utcnow() - timedelta(hours=24)

        snapshot = self.session.exec(
            select(VideoStatsSnapshot)
            .where(
                and_(
                    VideoStatsSnapshot.video_id == video.id,
                    VideoStatsSnapshot.captured_at <= time_24h_ago
                )
            )
            .order_by(desc(VideoStatsSnapshot.captured_at))
            .limit(1)
        ).first()

        if not snapshot:
            return None

        return video.view_count - snapshot.view_count

    def get_trending_videos(
        self,
        hours: int = 24,
        min_growth: int = 0,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get trending videos based on view count growth.

        Args:
            hours: Time window in hours
            min_growth: Minimum view count growth to include
            limit: Maximum number of results

        Returns:
            List of dicts with video and growth data
        """
        time_ago = datetime.utcnow() - timedelta(hours=hours)

        # Get all videos with their latest stats
        videos = self.session.exec(select(Video)).all()

        trending = []

        for video in videos:
            # Get snapshot from specified time ago
            snapshot = self.session.exec(
                select(VideoStatsSnapshot)
                .where(
                    and_(
                        VideoStatsSnapshot.video_id == video.id,
                        VideoStatsSnapshot.captured_at <= time_ago
                    )
                )
                .order_by(desc(VideoStatsSnapshot.captured_at))
                .limit(1)
            ).first()

            if snapshot:
                growth = video.view_count - snapshot.view_count

                if growth >= min_growth:
                    # Get channel info
                    channel = self.session.get(Channel, video.channel_id)

                    trending.append({
                        "video": video,
                        "channel": channel,
                        "view_growth": growth,
                        "like_growth": video.like_count - snapshot.like_count,
                        "comment_growth": video.comment_count - snapshot.comment_count,
                        "time_window_hours": hours,
                    })

        # Sort by view growth descending
        trending.sort(key=lambda x: x["view_growth"], reverse=True)

        return trending[:limit]

    def get_channel_analytics(self, channel: Channel) -> Dict[str, Any]:
        """
        Get comprehensive analytics for a channel.

        Args:
            channel: Channel model instance

        Returns:
            Dict with various analytics metrics
        """
        # Get all videos for this channel
        videos = self.session.exec(
            select(Video).where(Video.channel_id == channel.id)
        ).all()

        total_videos = len(videos)
        total_views = sum(v.view_count for v in videos)
        total_likes = sum(v.like_count for v in videos)
        total_comments = sum(v.comment_count for v in videos)

        # Calculate averages
        avg_views = total_views / total_videos if total_videos > 0 else 0
        avg_likes = total_likes / total_videos if total_videos > 0 else 0
        avg_comments = total_comments / total_videos if total_videos > 0 else 0

        # Calculate engagement rates
        engagement_rates = [self.calculate_engagement_rate(v) for v in videos]
        avg_engagement_rate = (
            sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0
        )

        # Get best performing video
        best_video = max(videos, key=lambda v: v.view_count) if videos else None

        # Get 24h growth for channel
        channel_growth_24h = self.get_channel_growth_24h(channel)

        return {
            "channel_id": channel.id,
            "channel_name": channel.title,
            "total_videos": total_videos,
            "total_views": total_views,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "avg_views_per_video": avg_views,
            "avg_likes_per_video": avg_likes,
            "avg_comments_per_video": avg_comments,
            "avg_engagement_rate": avg_engagement_rate,
            "best_video": {
                "id": best_video.id,
                "title": best_video.title,
                "views": best_video.view_count,
            } if best_video else None,
            "growth_24h": channel_growth_24h,
        }

    def get_channel_growth_24h(self, channel: Channel) -> Optional[Dict[str, int]]:
        """
        Get channel growth metrics in last 24 hours.

        Args:
            channel: Channel model instance

        Returns:
            Dict with growth metrics or None
        """
        time_24h_ago = datetime.utcnow() - timedelta(hours=24)

        snapshot = self.session.exec(
            select(ChannelStatsSnapshot)
            .where(
                and_(
                    ChannelStatsSnapshot.channel_id == channel.id,
                    ChannelStatsSnapshot.captured_at <= time_24h_ago
                )
            )
            .order_by(desc(ChannelStatsSnapshot.captured_at))
            .limit(1)
        ).first()

        if not snapshot:
            return None

        return {
            "view_growth": channel.view_count - snapshot.view_count,
            "subscriber_growth": channel.subscriber_count - snapshot.subscriber_count,
            "video_growth": channel.video_count - snapshot.video_count,
        }

    def get_video_history(
        self,
        video: Video,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get historical stats for a video.

        Args:
            video: Video model instance
            days: Number of days to look back

        Returns:
            List of historical data points
        """
        time_ago = datetime.utcnow() - timedelta(days=days)

        snapshots = self.session.exec(
            select(VideoStatsSnapshot)
            .where(
                and_(
                    VideoStatsSnapshot.video_id == video.id,
                    VideoStatsSnapshot.captured_at >= time_ago
                )
            )
            .order_by(VideoStatsSnapshot.captured_at)
        ).all()

        return [
            {
                "date": snapshot.captured_at.isoformat(),
                "views": snapshot.view_count,
                "likes": snapshot.like_count,
                "comments": snapshot.comment_count,
            }
            for snapshot in snapshots
        ]

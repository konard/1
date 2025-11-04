"""
YouTube Data API v3 client with multi-key support and rate limiting.
"""

import logging
import re
from typing import Optional, List, Dict, Any
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from backend.api_key_manager import get_key_manager

logger = logging.getLogger(__name__)


class YouTubeClient:
    """
    Client for YouTube Data API v3 with automatic key rotation and error handling.
    """

    def __init__(self):
        self.key_manager = get_key_manager()
        self._youtube = None

    def _get_client(self):
        """Get or create YouTube API client with current key"""
        api_key = self.key_manager.get_key()
        return build("youtube", "v3", developerKey=api_key)

    def _make_request(self, request_func, quota_units: int = 1):
        """
        Execute a YouTube API request with error handling and key rotation.

        Args:
            request_func: Function that creates and returns an API request
            quota_units: Estimated quota units for this request

        Returns:
            API response

        Raises:
            Exception: If all keys fail or other error occurs
        """
        max_retries = len(self.key_manager.keys)
        retries = 0

        while retries < max_retries:
            try:
                youtube = self._get_client()
                current_key = self.key_manager.keys[
                    (self.key_manager.current_key_index - 1) % len(self.key_manager.keys)
                ].key

                # Execute request
                response = request_func(youtube).execute()

                # Record successful quota usage
                self.key_manager.record_quota_usage(current_key, quota_units)

                return response

            except HttpError as e:
                # Handle quota exceeded error
                if e.resp.status == 403 and "quotaExceeded" in str(e):
                    logger.warning(f"Quota exceeded for current key, rotating...")
                    self.key_manager.handle_quota_exceeded(current_key)
                    retries += 1
                    continue
                elif e.resp.status == 403 and "dailyLimitExceeded" in str(e):
                    logger.warning(f"Daily limit exceeded for current key, rotating...")
                    self.key_manager.handle_quota_exceeded(current_key, retry_after_seconds=86400)
                    retries += 1
                    continue
                else:
                    # Other HTTP errors
                    logger.error(f"HTTP error from YouTube API: {e}")
                    raise

            except Exception as e:
                logger.error(f"Unexpected error in YouTube API request: {e}")
                raise

        raise RuntimeError("All API keys exhausted. Cannot complete request.")

    @staticmethod
    def extract_channel_id_from_url(url: str) -> Optional[str]:
        """
        Extract channel ID from various YouTube URL formats.

        Supports:
        - https://www.youtube.com/channel/UC...
        - https://www.youtube.com/@username
        - https://www.youtube.com/c/channelname
        - https://www.youtube.com/user/username
        - Video URLs (will extract channel from video)

        Args:
            url: YouTube URL

        Returns:
            Channel ID if found, None otherwise
        """
        # Direct channel ID
        match = re.search(r'youtube\.com/channel/([a-zA-Z0-9_-]+)', url)
        if match:
            return match.group(1)

        # Handle @username, /c/, /user/ by returning None
        # (we'll need to resolve these via API)
        if re.search(r'youtube\.com/@[a-zA-Z0-9_-]+', url):
            return None  # Need to resolve via API

        if re.search(r'youtube\.com/c/[a-zA-Z0-9_-]+', url):
            return None  # Need to resolve via API

        if re.search(r'youtube\.com/user/[a-zA-Z0-9_-]+', url):
            return None  # Need to resolve via API

        # Video URL - extract video ID, then we'll get channel from video
        match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)', url)
        if match:
            return None  # Will resolve via video

        return None

    @staticmethod
    def extract_video_id_from_url(url: str) -> Optional[str]:
        """Extract video ID from YouTube URL"""
        match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)', url)
        return match.group(1) if match else None

    def get_channel_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get channel information from any YouTube URL.

        Args:
            url: YouTube channel or video URL

        Returns:
            Channel data dict or None
        """
        # Try direct channel ID extraction
        channel_id = self.extract_channel_id_from_url(url)

        if channel_id:
            return self.get_channel_by_id(channel_id)

        # Try video ID extraction
        video_id = self.extract_video_id_from_url(url)
        if video_id:
            video_data = self.get_video_by_id(video_id)
            if video_data:
                channel_id = video_data.get("snippet", {}).get("channelId")
                if channel_id:
                    return self.get_channel_by_id(channel_id)

        # Try @username or custom URL
        if "@" in url or "/c/" in url or "/user/" in url:
            # Extract the username part
            username = None
            if "@" in url:
                match = re.search(r'@([a-zA-Z0-9_-]+)', url)
                username = match.group(1) if match else None
            elif "/c/" in url:
                match = re.search(r'/c/([a-zA-Z0-9_-]+)', url)
                username = match.group(1) if match else None
            elif "/user/" in url:
                match = re.search(r'/user/([a-zA-Z0-9_-]+)', url)
                username = match.group(1) if match else None

            if username:
                return self.search_channel_by_username(username)

        return None

    def search_channel_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Search for a channel by username or handle.

        Args:
            username: Channel username/handle

        Returns:
            Channel data dict or None
        """
        def request_func(youtube):
            return youtube.search().list(
                part="snippet",
                q=username,
                type="channel",
                maxResults=1
            )

        try:
            response = self._make_request(request_func, quota_units=100)
            items = response.get("items", [])

            if items:
                channel_id = items[0]["id"]["channelId"]
                return self.get_channel_by_id(channel_id)
        except Exception as e:
            logger.error(f"Error searching channel by username '{username}': {e}")

        return None

    def get_channel_by_id(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """
        Get channel data by channel ID.

        Args:
            channel_id: YouTube channel ID

        Returns:
            Channel data dict with snippet, statistics, contentDetails
        """
        def request_func(youtube):
            return youtube.channels().list(
                part="snippet,statistics,contentDetails",
                id=channel_id
            )

        try:
            response = self._make_request(request_func, quota_units=1)
            items = response.get("items", [])
            return items[0] if items else None
        except Exception as e:
            logger.error(f"Error fetching channel {channel_id}: {e}")
            return None

    def get_video_by_id(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get video data by video ID.

        Args:
            video_id: YouTube video ID

        Returns:
            Video data dict with snippet, contentDetails, statistics
        """
        def request_func(youtube):
            return youtube.videos().list(
                part="snippet,contentDetails,statistics",
                id=video_id
            )

        try:
            response = self._make_request(request_func, quota_units=1)
            items = response.get("items", [])
            return items[0] if items else None
        except Exception as e:
            logger.error(f"Error fetching video {video_id}: {e}")
            return None

    def get_channel_videos(
        self,
        channel_id: str,
        uploads_playlist_id: str,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get videos from a channel's uploads playlist.

        Args:
            channel_id: YouTube channel ID
            uploads_playlist_id: Uploads playlist ID
            max_results: Maximum number of videos to fetch

        Returns:
            List of video data dicts
        """
        videos = []
        next_page_token = None

        try:
            while len(videos) < max_results:
                # Get playlist items
                def request_func(youtube):
                    return youtube.playlistItems().list(
                        part="snippet,contentDetails",
                        playlistId=uploads_playlist_id,
                        maxResults=min(50, max_results - len(videos)),
                        pageToken=next_page_token
                    )

                response = self._make_request(request_func, quota_units=1)
                items = response.get("items", [])

                if not items:
                    break

                # Extract video IDs
                video_ids = [item["contentDetails"]["videoId"] for item in items]

                # Get detailed video info (batch request)
                def video_request_func(youtube):
                    return youtube.videos().list(
                        part="snippet,contentDetails,statistics",
                        id=",".join(video_ids)
                    )

                video_response = self._make_request(video_request_func, quota_units=1)
                video_items = video_response.get("items", [])
                videos.extend(video_items)

                # Check for next page
                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break

        except Exception as e:
            logger.error(f"Error fetching videos for channel {channel_id}: {e}")

        return videos


# Global instance
_youtube_client: Optional[YouTubeClient] = None


def get_youtube_client() -> YouTubeClient:
    """Get or create the global YouTube client instance"""
    global _youtube_client
    if _youtube_client is None:
        _youtube_client = YouTubeClient()
    return _youtube_client

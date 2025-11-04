"""
API Key Manager for YouTube Data API v3

Manages multiple API keys, tracks quota usage, and provides intelligent key rotation
to avoid hitting rate limits on individual keys.
"""

import os
import time
import logging
from typing import Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class APIKeyStats:
    """Statistics for a single API key"""
    key: str
    total_requests: int = 0
    quota_used: int = 0  # Approximate quota units used
    last_used: Optional[datetime] = None
    last_quota_exceeded: Optional[datetime] = None
    is_temporarily_disabled: bool = False
    disabled_until: Optional[datetime] = None


class YouTubeAPIKeyManager:
    """
    Manages multiple YouTube API keys with intelligent rotation.

    YouTube Data API v3 has a default quota of 10,000 units per day per key.
    Common costs:
    - list video: 1 unit
    - list channel: 1 unit
    - list playlist items: 1 unit
    - search: 100 units

    This manager distributes requests across multiple keys and handles quota errors.
    """

    def __init__(self, api_keys: Optional[List[str]] = None):
        """
        Initialize the API key manager.

        Args:
            api_keys: List of YouTube API keys. If None, reads from YOUTUBE_API_KEYS env var.
        """
        if api_keys is None:
            keys_str = os.getenv("YOUTUBE_API_KEYS", "")
            api_keys = [k.strip() for k in keys_str.split(",") if k.strip()]

        if not api_keys:
            raise ValueError(
                "No API keys provided. Set YOUTUBE_API_KEYS environment variable "
                "with comma-separated keys."
            )

        self.keys: List[APIKeyStats] = [APIKeyStats(key=key) for key in api_keys]
        self.current_key_index = 0
        self.lock = Lock()

        logger.info(f"Initialized YouTubeAPIKeyManager with {len(self.keys)} keys")

    def get_key(self) -> str:
        """
        Get the next available API key for a request.

        Returns:
            API key string

        Raises:
            RuntimeError: If all keys are temporarily disabled
        """
        with self.lock:
            # First, check and re-enable any keys whose disabled period has expired
            now = datetime.utcnow()
            for key_stat in self.keys:
                if (
                    key_stat.is_temporarily_disabled
                    and key_stat.disabled_until
                    and now >= key_stat.disabled_until
                ):
                    logger.info(f"Re-enabling key ending in ...{key_stat.key[-4:]}")
                    key_stat.is_temporarily_disabled = False
                    key_stat.disabled_until = None

            # Find next available (not disabled) key using round-robin
            attempts = 0
            while attempts < len(self.keys):
                key_stat = self.keys[self.current_key_index]

                if not key_stat.is_temporarily_disabled:
                    # Update stats
                    key_stat.total_requests += 1
                    key_stat.last_used = datetime.utcnow()

                    # Move to next key for next request (round-robin)
                    self.current_key_index = (self.current_key_index + 1) % len(self.keys)

                    logger.debug(
                        f"Using key ...{key_stat.key[-4:]} "
                        f"(requests: {key_stat.total_requests}, "
                        f"quota: ~{key_stat.quota_used})"
                    )
                    return key_stat.key

                # Try next key
                self.current_key_index = (self.current_key_index + 1) % len(self.keys)
                attempts += 1

            # All keys are disabled
            raise RuntimeError(
                "All API keys are temporarily disabled due to quota limits. "
                "Please wait or add more keys."
            )

    def record_quota_usage(self, key: str, quota_units: int):
        """
        Record quota usage for a key.

        Args:
            key: The API key
            quota_units: Number of quota units consumed (estimate)
        """
        with self.lock:
            for key_stat in self.keys:
                if key_stat.key == key:
                    key_stat.quota_used += quota_units
                    break

    def handle_quota_exceeded(self, key: str, retry_after_seconds: int = 3600):
        """
        Mark a key as temporarily disabled due to quota exceeded.

        Args:
            key: The API key that hit the limit
            retry_after_seconds: How long to disable the key (default: 1 hour)
        """
        with self.lock:
            for key_stat in self.keys:
                if key_stat.key == key:
                    key_stat.is_temporarily_disabled = True
                    key_stat.last_quota_exceeded = datetime.utcnow()
                    key_stat.disabled_until = datetime.utcnow() + timedelta(
                        seconds=retry_after_seconds
                    )

                    logger.warning(
                        f"Key ...{key[-4:]} exceeded quota. "
                        f"Disabled until {key_stat.disabled_until}"
                    )
                    break

    def get_stats(self) -> List[dict]:
        """
        Get statistics for all keys.

        Returns:
            List of dictionaries with key statistics
        """
        with self.lock:
            return [
                {
                    "key_preview": f"...{ks.key[-4:]}",
                    "total_requests": ks.total_requests,
                    "quota_used_estimate": ks.quota_used,
                    "last_used": ks.last_used.isoformat() if ks.last_used else None,
                    "is_disabled": ks.is_temporarily_disabled,
                    "disabled_until": (
                        ks.disabled_until.isoformat() if ks.disabled_until else None
                    ),
                }
                for ks in self.keys
            ]

    def reset_daily_stats(self):
        """
        Reset daily quota counters.

        Should be called once per day (YouTube API quotas reset at midnight Pacific Time).
        """
        with self.lock:
            for key_stat in self.keys:
                key_stat.quota_used = 0
                key_stat.is_temporarily_disabled = False
                key_stat.disabled_until = None
                key_stat.last_quota_exceeded = None

            logger.info("Reset daily stats for all API keys")


# Global instance
_key_manager: Optional[YouTubeAPIKeyManager] = None


def get_key_manager() -> YouTubeAPIKeyManager:
    """Get or create the global API key manager instance"""
    global _key_manager
    if _key_manager is None:
        _key_manager = YouTubeAPIKeyManager()
    return _key_manager

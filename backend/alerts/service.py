"""
Alert service for monitoring and triggering alerts.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from sqlmodel import Session, select, and_, desc

from backend.storage.models import Alert, AlertEvent, Video, Channel, VideoStatsSnapshot
from backend.analytics import AnalyticsCalculator

logger = logging.getLogger(__name__)


class AlertService:
    """Service for managing and checking alerts"""

    def __init__(self, session: Session):
        self.session = session
        self.analytics = AnalyticsCalculator(session)

    def create_alert(
        self,
        name: str,
        alert_type: str,
        threshold_field: str,
        threshold_value: float,
        time_window_hours: int = 24,
        channel_id: Optional[int] = None,
    ) -> Alert:
        """
        Create a new alert.

        Args:
            name: Alert name
            alert_type: Type of alert ('viral_video', 'engagement_drop', etc.)
            threshold_field: Field to monitor ('view_count', 'engagement_rate', etc.)
            threshold_value: Threshold value to trigger alert
            time_window_hours: Time window for checking (default 24h)
            channel_id: Optional channel to limit alert to

        Returns:
            Created Alert instance
        """
        alert = Alert(
            name=name,
            alert_type=alert_type,
            threshold_field=threshold_field,
            threshold_value=threshold_value,
            time_window_hours=time_window_hours,
            channel_id=channel_id,
        )

        self.session.add(alert)
        self.session.commit()
        self.session.refresh(alert)

        logger.info(f"Created alert: {name}")
        return alert

    def check_all_alerts(self):
        """Check all active alerts and trigger if conditions are met"""
        alerts = self.session.exec(
            select(Alert).where(Alert.is_active == True)
        ).all()

        logger.info(f"Checking {len(alerts)} active alerts...")

        for alert in alerts:
            try:
                self._check_alert(alert)
            except Exception as e:
                logger.error(f"Error checking alert {alert.id}: {e}")

    def _check_alert(self, alert: Alert):
        """Check a single alert"""
        if alert.alert_type == "viral_video":
            self._check_viral_video_alert(alert)
        elif alert.alert_type == "engagement_drop":
            self._check_engagement_drop_alert(alert)
        # Add more alert types as needed

    def _check_viral_video_alert(self, alert: Alert):
        """
        Check for viral videos (high view growth in time window).

        Triggers when a video gains more than threshold_value views in time_window_hours.
        """
        time_ago = datetime.utcnow() - timedelta(hours=alert.time_window_hours)

        # Get videos to check
        query = select(Video)
        if alert.channel_id:
            query = query.where(Video.channel_id == alert.channel_id)

        videos = self.session.exec(query).all()

        for video in videos:
            # Get snapshot from time_ago
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
                view_growth = video.view_count - snapshot.view_count

                if view_growth >= alert.threshold_value:
                    # Check if we already triggered for this video recently
                    recent_event = self.session.exec(
                        select(AlertEvent)
                        .where(
                            and_(
                                AlertEvent.alert_id == alert.id,
                                AlertEvent.video_id == video.id,
                                AlertEvent.triggered_at >= time_ago
                            )
                        )
                    ).first()

                    if not recent_event:
                        self._trigger_alert(
                            alert=alert,
                            video=video,
                            message=f"Video '{video.title}' gained {view_growth:,} views in {alert.time_window_hours}h",
                            metric_value=view_growth,
                        )

    def _check_engagement_drop_alert(self, alert: Alert):
        """
        Check for engagement rate drops.

        Triggers when a channel's recent videos have engagement below threshold.
        """
        if not alert.channel_id:
            logger.warning(f"Alert {alert.id} has no channel_id, skipping")
            return

        channel = self.session.get(Channel, alert.channel_id)
        if not channel:
            return

        # Get recent videos (published in last 7 days)
        time_7d_ago = datetime.utcnow() - timedelta(days=7)

        recent_videos = self.session.exec(
            select(Video)
            .where(
                and_(
                    Video.channel_id == channel.id,
                    Video.published_at >= time_7d_ago
                )
            )
        ).all()

        if not recent_videos:
            return

        # Calculate average engagement rate
        engagement_rates = [
            self.analytics.calculate_engagement_rate(v) for v in recent_videos
        ]
        avg_engagement = sum(engagement_rates) / len(engagement_rates)

        if avg_engagement < alert.threshold_value:
            # Check if we already triggered recently
            recent_event = self.session.exec(
                select(AlertEvent)
                .where(
                    and_(
                        AlertEvent.alert_id == alert.id,
                        AlertEvent.channel_id == channel.id,
                        AlertEvent.triggered_at >= datetime.utcnow() - timedelta(hours=alert.time_window_hours)
                    )
                )
            ).first()

            if not recent_event:
                self._trigger_alert(
                    alert=alert,
                    channel=channel,
                    message=f"Channel '{channel.title}' engagement dropped to {avg_engagement:.4f} (threshold: {alert.threshold_value:.4f})",
                    metric_value=avg_engagement,
                )

    def _trigger_alert(
        self,
        alert: Alert,
        message: str,
        metric_value: float,
        video: Optional[Video] = None,
        channel: Optional[Channel] = None,
    ):
        """Trigger an alert by creating an event"""
        event = AlertEvent(
            alert_id=alert.id,
            video_id=video.id if video else None,
            channel_id=channel.id if channel else (video.channel_id if video else None),
            message=message,
            metric_value=metric_value,
        )

        self.session.add(event)

        # Update alert stats
        alert.last_triggered_at = datetime.utcnow()
        alert.trigger_count += 1

        self.session.commit()

        logger.info(f"Alert triggered: {message}")

    def get_recent_events(self, limit: int = 50, unread_only: bool = False) -> List[AlertEvent]:
        """
        Get recent alert events.

        Args:
            limit: Maximum number of events to return
            unread_only: Only return unread events

        Returns:
            List of AlertEvent instances
        """
        query = select(AlertEvent).order_by(desc(AlertEvent.triggered_at)).limit(limit)

        if unread_only:
            query = query.where(AlertEvent.is_read == False)

        events = self.session.exec(query).all()
        return list(events)

    def mark_event_read(self, event_id: int):
        """Mark an alert event as read"""
        event = self.session.get(AlertEvent, event_id)
        if event:
            event.is_read = True
            self.session.commit()

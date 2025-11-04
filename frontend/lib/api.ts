/**
 * API client for YouTube Analytics backend
 */

import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface Channel {
  id: number;
  youtube_channel_id: string;
  title: string;
  description?: string;
  custom_url?: string;
  thumbnail_url?: string;
  view_count: number;
  subscriber_count: number;
  video_count: number;
  is_own_channel: boolean;
  created_at: string;
  updated_at: string;
  last_sync_at?: string;
}

export interface Video {
  id: number;
  youtube_video_id: string;
  channel_id: number;
  title: string;
  description?: string;
  published_at: string;
  thumbnail_url?: string;
  duration?: string;
  view_count: number;
  like_count: number;
  comment_count: number;
  engagement_rate?: number;
  views_per_day?: number;
  created_at: string;
  updated_at: string;
}

export interface VideoWithChannel extends Video {
  channel: Channel;
}

export interface TrendingVideo {
  video: Video;
  channel: Channel;
  view_growth: number;
  like_growth: number;
  comment_growth: number;
  time_window_hours: number;
}

export interface ChannelAnalytics {
  channel_id: number;
  channel_name: string;
  total_videos: number;
  total_views: number;
  total_likes: number;
  total_comments: number;
  avg_views_per_video: number;
  avg_likes_per_video: number;
  avg_comments_per_video: number;
  avg_engagement_rate: number;
  best_video?: {
    id: number;
    title: string;
    views: number;
  };
  growth_24h?: {
    view_growth: number;
    subscriber_growth: number;
    video_growth: number;
  };
}

export interface Alert {
  id: number;
  name: string;
  alert_type: string;
  threshold_field: string;
  threshold_value: number;
  time_window_hours: number;
  channel_id?: number;
  is_active: boolean;
  last_triggered_at?: string;
  trigger_count: number;
  created_at: string;
}

export interface AlertEvent {
  id: number;
  alert_id: number;
  video_id?: number;
  channel_id?: number;
  message: string;
  metric_value: number;
  triggered_at: string;
  is_read: boolean;
}

// API functions

// Channels
export const getChannels = () => api.get<Channel[]>('/channels');
export const getChannel = (id: number) => api.get<Channel>(`/channels/${id}`);
export const createChannel = (data: {
  url: string;
  is_own_channel?: boolean;
  import_videos?: boolean;
  max_videos?: number;
}) => api.post<Channel>('/channels', data);
export const refreshChannel = (id: number) => api.post<Channel>(`/channels/${id}/refresh`);
export const deleteChannel = (id: number) => api.delete(`/channels/${id}`);

// Videos
export const getChannelVideos = (channelId: number, params?: {
  skip?: number;
  limit?: number;
  sort_by?: string;
}) => api.get<Video[]>(`/channels/${channelId}/videos`, { params });
export const getVideo = (id: number) => api.get<Video>(`/videos/${id}`);
export const getVideoHistory = (id: number, days?: number) =>
  api.get<{ date: string; views: number; likes: number; comments: number }[]>(
    `/videos/${id}/history`,
    { params: { days } }
  );

// Analytics
export const getChannelAnalytics = (channelId: number) =>
  api.get<ChannelAnalytics>(`/channels/${channelId}/analytics`);
export const getTrendingVideos = (params?: {
  hours?: number;
  min_growth?: number;
  limit?: number;
}) => api.get<TrendingVideo[]>('/trending/videos', { params });

// Alerts
export const getAlerts = () => api.get<Alert[]>('/alerts');
export const createAlert = (data: {
  name: string;
  alert_type: string;
  threshold_field: string;
  threshold_value: number;
  time_window_hours?: number;
  channel_id?: number;
}) => api.post<Alert>('/alerts', data);
export const toggleAlert = (id: number) => api.put<Alert>(`/alerts/${id}/toggle`);
export const deleteAlert = (id: number) => api.delete(`/alerts/${id}`);
export const getAlertEvents = (params?: {
  limit?: number;
  unread_only?: boolean;
}) => api.get<AlertEvent[]>('/alert-events', { params });
export const markEventRead = (id: number) => api.put<AlertEvent>(`/alert-events/${id}/read`);

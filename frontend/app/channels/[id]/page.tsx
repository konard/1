"use client"

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { getChannel, getChannelVideos, getChannelAnalytics, type Channel, type Video, type ChannelAnalytics } from '@/lib/api'
import { formatNumber, formatDate, formatDuration } from '@/lib/utils'

export default function ChannelDetailPage() {
  const params = useParams()
  const channelId = parseInt(params.id as string)

  const [channel, setChannel] = useState<Channel | null>(null)
  const [videos, setVideos] = useState<Video[]>([])
  const [analytics, setAnalytics] = useState<ChannelAnalytics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      try {
        const [channelRes, videosRes, analyticsRes] = await Promise.all([
          getChannel(channelId),
          getChannelVideos(channelId, { limit: 50, sort_by: 'view_count' }),
          getChannelAnalytics(channelId),
        ])
        setChannel(channelRes.data)
        setVideos(videosRes.data)
        setAnalytics(analyticsRes.data)
      } catch (error) {
        console.error('Error fetching channel data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [channelId])

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-muted-foreground">Loading channel...</p>
      </div>
    )
  }

  if (!channel) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-muted-foreground">Channel not found</p>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-4">
          {channel.thumbnail_url && (
            <img
              src={channel.thumbnail_url}
              alt={channel.title}
              className="h-20 w-20 rounded-full"
            />
          )}
          <div>
            <h1 className="text-3xl font-bold">{channel.title}</h1>
            <p className="text-muted-foreground">{channel.custom_url}</p>
          </div>
        </div>
        {channel.description && (
          <p className="text-sm text-muted-foreground line-clamp-2">{channel.description}</p>
        )}
      </div>

      {analytics && (
        <div className="grid gap-4 md:grid-cols-4 mb-8">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Avg Views/Video</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatNumber(Math.round(analytics.avg_views_per_video))}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Avg Engagement</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{(analytics.avg_engagement_rate * 100).toFixed(2)}%</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Total Likes</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatNumber(analytics.total_likes)}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Total Comments</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatNumber(analytics.total_comments)}</div>
            </CardContent>
          </Card>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Videos</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Title</TableHead>
                <TableHead>Published</TableHead>
                <TableHead className="text-right">Views</TableHead>
                <TableHead className="text-right">Likes</TableHead>
                <TableHead className="text-right">Comments</TableHead>
                <TableHead className="text-right">Engagement</TableHead>
                <TableHead className="text-right">Views/Day</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {videos.map((video) => (
                <TableRow key={video.id}>
                  <TableCell className="font-medium max-w-md truncate">
                    {video.title}
                  </TableCell>
                  <TableCell>{formatDate(video.published_at)}</TableCell>
                  <TableCell className="text-right">{formatNumber(video.view_count)}</TableCell>
                  <TableCell className="text-right">{formatNumber(video.like_count)}</TableCell>
                  <TableCell className="text-right">{formatNumber(video.comment_count)}</TableCell>
                  <TableCell className="text-right">
                    {video.engagement_rate ? (video.engagement_rate * 100).toFixed(2) + '%' : 'N/A'}
                  </TableCell>
                  <TableCell className="text-right">
                    {video.views_per_day ? formatNumber(Math.round(video.views_per_day)) : 'N/A'}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}

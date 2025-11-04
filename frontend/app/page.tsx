"use client"

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { getChannels, getAlertEvents, type Channel, type AlertEvent } from '@/lib/api'
import { formatNumber } from '@/lib/utils'
import { Youtube, Eye, Users, TrendingUp } from 'lucide-react'

export default function Home() {
  const [channels, setChannels] = useState<Channel[]>([])
  const [alerts, setAlerts] = useState<AlertEvent[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      try {
        const [channelsRes, alertsRes] = await Promise.all([
          getChannels(),
          getAlertEvents({ limit: 5, unread_only: true }),
        ])
        setChannels(channelsRes.data)
        setAlerts(alertsRes.data)
      } catch (error) {
        console.error('Error fetching data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  const totalViews = channels.reduce((sum, ch) => sum + ch.view_count, 0)
  const totalSubscribers = channels.reduce((sum, ch) => sum + ch.subscriber_count, 0)
  const totalVideos = channels.reduce((sum, ch) => sum + ch.video_count, 0)

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">Overview of your YouTube analytics</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Channels</CardTitle>
            <Youtube className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{channels.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Views</CardTitle>
            <Eye className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(totalViews)}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Subscribers</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(totalSubscribers)}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Videos</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(totalVideos)}</div>
          </CardContent>
        </Card>
      </div>

      <div className="mt-8 grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent Channels</CardTitle>
            <CardDescription>Your tracked YouTube channels</CardDescription>
          </CardHeader>
          <CardContent>
            {channels.length === 0 ? (
              <p className="text-sm text-muted-foreground">No channels yet. Add one to get started!</p>
            ) : (
              <div className="space-y-4">
                {channels.slice(0, 5).map((channel) => (
                  <div key={channel.id} className="flex items-center gap-4">
                    {channel.thumbnail_url && (
                      <img
                        src={channel.thumbnail_url}
                        alt={channel.title}
                        className="h-10 w-10 rounded-full"
                      />
                    )}
                    <div className="flex-1">
                      <p className="text-sm font-medium">{channel.title}</p>
                      <p className="text-xs text-muted-foreground">
                        {formatNumber(channel.subscriber_count)} subscribers
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Alerts</CardTitle>
            <CardDescription>Latest notifications and updates</CardDescription>
          </CardHeader>
          <CardContent>
            {alerts.length === 0 ? (
              <p className="text-sm text-muted-foreground">No recent alerts</p>
            ) : (
              <div className="space-y-4">
                {alerts.map((alert) => (
                  <div key={alert.id} className="text-sm">
                    <p className="font-medium">{alert.message}</p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(alert.triggered_at).toLocaleString()}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

"use client"

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { getAlertEvents, markEventRead, type AlertEvent } from '@/lib/api'
import { Bell, Check } from 'lucide-react'
import { formatDate } from '@/lib/utils'

export default function AlertsPage() {
  const [events, setEvents] = useState<AlertEvent[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchEvents()
  }, [])

  async function fetchEvents() {
    try {
      const res = await getAlertEvents({ limit: 100 })
      setEvents(res.data)
    } catch (error) {
      console.error('Error fetching alert events:', error)
    } finally {
      setLoading(false)
    }
  }

  async function handleMarkRead(eventId: number) {
    try {
      await markEventRead(eventId)
      setEvents((prev) =>
        prev.map((event) =>
          event.id === eventId ? { ...event, is_read: true } : event
        )
      )
    } catch (error) {
      console.error('Error marking event as read:', error)
    }
  }

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-muted-foreground">Loading alerts...</p>
      </div>
    )
  }

  const unreadCount = events.filter((e) => !e.is_read).length

  return (
    <div className="p-8">
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-2">
          <Bell className="h-8 w-8" />
          <h1 className="text-3xl font-bold">Alerts</h1>
        </div>
        <p className="text-muted-foreground">
          {unreadCount > 0 ? `${unreadCount} unread notification${unreadCount > 1 ? 's' : ''}` : 'All caught up!'}
        </p>
      </div>

      {events.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Bell className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">No alerts yet</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {events.map((event) => (
            <Card
              key={event.id}
              className={event.is_read ? 'opacity-60' : 'border-primary'}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg">{event.message}</CardTitle>
                    <p className="text-sm text-muted-foreground mt-1">
                      {new Date(event.triggered_at).toLocaleString()}
                    </p>
                  </div>
                  {!event.is_read && (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleMarkRead(event.id)}
                    >
                      <Check className="h-4 w-4 mr-1" />
                      Mark as read
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Metric Value: </span>
                    <span className="font-medium">{event.metric_value.toFixed(2)}</span>
                  </div>
                  {event.is_read && (
                    <div className="text-muted-foreground">Read</div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

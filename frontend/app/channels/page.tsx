"use client"

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { getChannels, createChannel, type Channel } from '@/lib/api'
import { formatNumber, formatDate } from '@/lib/utils'
import { Plus, ExternalLink } from 'lucide-react'

export default function ChannelsPage() {
  const [channels, setChannels] = useState<Channel[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddForm, setShowAddForm] = useState(false)
  const [newChannelUrl, setNewChannelUrl] = useState('')
  const [importing, setImporting] = useState(false)

  useEffect(() => {
    fetchChannels()
  }, [])

  async function fetchChannels() {
    try {
      const res = await getChannels()
      setChannels(res.data)
    } catch (error) {
      console.error('Error fetching channels:', error)
    } finally {
      setLoading(false)
    }
  }

  async function handleAddChannel(e: React.FormEvent) {
    e.preventDefault()
    if (!newChannelUrl.trim()) return

    setImporting(true)
    try {
      await createChannel({
        url: newChannelUrl,
        import_videos: true,
        max_videos: 50,
      })
      setNewChannelUrl('')
      setShowAddForm(false)
      fetchChannels()
    } catch (error) {
      console.error('Error adding channel:', error)
      alert('Failed to add channel. Please check the URL and try again.')
    } finally {
      setImporting(false)
    }
  }

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-muted-foreground">Loading channels...</p>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Channels</h1>
          <p className="text-muted-foreground">Manage your tracked YouTube channels</p>
        </div>
        <Button onClick={() => setShowAddForm(!showAddForm)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Channel
        </Button>
      </div>

      {showAddForm && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Add New Channel</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAddChannel} className="flex gap-4">
              <Input
                placeholder="Enter YouTube channel URL or video URL"
                value={newChannelUrl}
                onChange={(e) => setNewChannelUrl(e.target.value)}
                className="flex-1"
                disabled={importing}
              />
              <Button type="submit" disabled={importing}>
                {importing ? 'Importing...' : 'Import'}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowAddForm(false)}
                disabled={importing}
              >
                Cancel
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      {channels.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <p className="text-muted-foreground">No channels yet. Add one to get started!</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {channels.map((channel) => (
            <Card key={channel.id} className="overflow-hidden">
              <CardHeader className="space-y-0 pb-4">
                <div className="flex items-start gap-4">
                  {channel.thumbnail_url && (
                    <img
                      src={channel.thumbnail_url}
                      alt={channel.title}
                      className="h-16 w-16 rounded-full"
                    />
                  )}
                  <div className="flex-1 min-w-0">
                    <CardTitle className="text-lg truncate">{channel.title}</CardTitle>
                    {channel.custom_url && (
                      <a
                        href={`https://youtube.com/${channel.custom_url}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-muted-foreground hover:underline flex items-center gap-1"
                      >
                        {channel.custom_url}
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Subscribers</span>
                    <span className="font-medium">{formatNumber(channel.subscriber_count)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Total Views</span>
                    <span className="font-medium">{formatNumber(channel.view_count)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Videos</span>
                    <span className="font-medium">{channel.video_count}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Added</span>
                    <span className="font-medium">{formatDate(channel.created_at)}</span>
                  </div>
                </div>
                <div className="mt-4">
                  <Link href={`/channels/${channel.id}`}>
                    <Button className="w-full" variant="outline">
                      View Details
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

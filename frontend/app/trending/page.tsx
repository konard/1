"use client"

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { getTrendingVideos, type TrendingVideo } from '@/lib/api'
import { formatNumber, formatDate } from '@/lib/utils'
import { TrendingUp, ArrowUp } from 'lucide-react'

export default function TrendingPage() {
  const [trendingVideos, setTrendingVideos] = useState<TrendingVideo[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await getTrendingVideos({ hours: 24, limit: 50 })
        setTrendingVideos(res.data)
      } catch (error) {
        console.error('Error fetching trending videos:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-muted-foreground">Loading trending videos...</p>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-2">
          <TrendingUp className="h-8 w-8" />
          <h1 className="text-3xl font-bold">Trending Videos</h1>
        </div>
        <p className="text-muted-foreground">Videos with the highest growth in the last 24 hours</p>
      </div>

      {trendingVideos.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <p className="text-muted-foreground">
              No trending videos yet. Check back after some time for growth data.
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Top Performing Videos (24h)</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Video</TableHead>
                  <TableHead>Channel</TableHead>
                  <TableHead>Published</TableHead>
                  <TableHead className="text-right">Total Views</TableHead>
                  <TableHead className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <ArrowUp className="h-4 w-4" />
                      Views (24h)
                    </div>
                  </TableHead>
                  <TableHead className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <ArrowUp className="h-4 w-4" />
                      Likes (24h)
                    </div>
                  </TableHead>
                  <TableHead className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <ArrowUp className="h-4 w-4" />
                      Comments (24h)
                    </div>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {trendingVideos.map((item) => (
                  <TableRow key={item.video.id}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        {item.video.thumbnail_url && (
                          <img
                            src={item.video.thumbnail_url}
                            alt={item.video.title}
                            className="h-12 w-20 rounded object-cover"
                          />
                        )}
                        <div className="max-w-md">
                          <p className="font-medium line-clamp-2">{item.video.title}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>{item.channel.title}</TableCell>
                    <TableCell>{formatDate(item.video.published_at)}</TableCell>
                    <TableCell className="text-right">{formatNumber(item.video.view_count)}</TableCell>
                    <TableCell className="text-right">
                      <span className="font-medium text-green-600">
                        +{formatNumber(item.view_growth)}
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      <span className="font-medium text-green-600">
                        +{formatNumber(item.like_growth)}
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      <span className="font-medium text-green-600">
                        +{formatNumber(item.comment_growth)}
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

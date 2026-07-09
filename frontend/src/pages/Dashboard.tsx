import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { format } from 'date-fns'
import {
  ExternalLink,
  Trash2,
  BarChart2,
  AlertCircle,
  Link2,
  Plus,
  Copy,
  Check,
} from 'lucide-react'
import { listURLs, deleteURL } from '../api/urls'
import { getAnalytics } from '../api/analytics'
import type { URLItem } from '../types'

interface URLWithStats extends URLItem {
  total_clicks: number | undefined
  stats_loaded: boolean
}

function isExpired(expiresAt: string | null): boolean {
  if (!expiresAt) return false
  return new Date(expiresAt) < new Date()
}

function ExpiryBadge({ expiresAt }: { expiresAt: string | null }) {
  if (!expiresAt) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
        Active
      </span>
    )
  }
  if (isExpired(expiresAt)) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
        Expired
      </span>
    )
  }
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-700">
      Expires {format(new Date(expiresAt), 'MMM d, yyyy')}
    </span>
  )
}

function SkeletonRow() {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 animate-pulse">
      <div className="flex items-center gap-4">
        <div className="flex-1 space-y-2">
          <div className="h-4 bg-slate-200 rounded w-48" />
          <div className="h-3 bg-slate-200 rounded w-72" />
          <div className="h-3 bg-slate-200 rounded w-32" />
        </div>
        <div className="flex gap-2">
          <div className="h-8 w-24 bg-slate-200 rounded-lg" />
          <div className="h-8 w-8 bg-slate-200 rounded-lg" />
        </div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [urls, setUrls] = useState<URLWithStats[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [deletingCode, setDeletingCode] = useState<string | null>(null)
  const [copiedCode, setCopiedCode] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const urlList = await listURLs()
      const withStats: URLWithStats[] = urlList.map((u) => ({
        ...u,
        total_clicks: undefined,
        stats_loaded: false,
      }))
      setUrls(withStats)

      const analyticsResults = await Promise.allSettled(
        urlList.map((u) => getAnalytics(u.short_code))
      )

      setUrls(
        urlList.map((u, i) => {
          const result = analyticsResults[i]
          return {
            ...u,
            total_clicks:
              result.status === 'fulfilled' ? result.value.total_clicks : undefined,
            stats_loaded: true,
          }
        })
      )
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setError(axiosErr.response?.data?.detail || 'Failed to load your URLs')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const handleDelete = async (shortCode: string) => {
    if (!confirm('Delete this URL? This cannot be undone.')) return
    setDeletingCode(shortCode)
    try {
      await deleteURL(shortCode)
      setUrls((prev) => prev.filter((u) => u.short_code !== shortCode))
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      alert(axiosErr.response?.data?.detail || 'Failed to delete URL')
    } finally {
      setDeletingCode(null)
    }
  }

  const handleCopy = async (shortUrl: string, shortCode: string) => {
    await navigator.clipboard.writeText(shortUrl)
    setCopiedCode(shortCode)
    setTimeout(() => setCopiedCode(null), 2000)
  }

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8">
        <div className="mb-8 animate-pulse">
          <div className="h-7 bg-slate-200 rounded w-32" />
          <div className="h-4 bg-slate-200 rounded w-20 mt-2" />
        </div>
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonRow key={i} />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8">
        <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-medium">Failed to load URLs</p>
            <p className="text-sm mt-0.5 text-red-600">{error}</p>
          </div>
          <button
            onClick={fetchData}
            className="text-sm font-medium underline shrink-0"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (urls.length === 0) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8">
        <div className="text-center py-24">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-slate-100 rounded-2xl mb-5">
            <Link2 className="w-8 h-8 text-slate-400" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900">No URLs yet</h3>
          <p className="mt-2 text-slate-500 text-sm">Shorten your first URL to see it here.</p>
          <Link
            to="/"
            className="mt-6 inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg text-sm transition"
          >
            <Plus className="w-4 h-4" />
            Shorten a URL
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-7">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Your URLs</h1>
          <p className="text-slate-500 text-sm mt-0.5">
            {urls.length} link{urls.length !== 1 ? 's' : ''}
          </p>
        </div>
        <Link
          to="/"
          className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg text-sm transition"
        >
          <Plus className="w-4 h-4" />
          <span className="hidden sm:inline">New URL</span>
        </Link>
      </div>

      <div className="space-y-3">
        {urls.map((url) => (
          <div
            key={url.id}
            className="bg-white rounded-xl border border-slate-200 p-4 sm:p-5 hover:border-slate-300 transition"
          >
            <div className="flex flex-col sm:flex-row sm:items-center gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <a
                    href={url.short_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-mono text-sm font-semibold text-indigo-600 hover:text-indigo-700 transition"
                  >
                    {url.short_url}
                  </a>
                  <ExpiryBadge expiresAt={url.expires_at} />
                </div>
                <p className="text-sm text-slate-500 truncate mt-1">{url.original_url}</p>
                <div className="flex items-center gap-4 mt-2 text-xs text-slate-400">
                  <span>Created {format(new Date(url.created_at), 'MMM d, yyyy')}</span>
                  {url.stats_loaded ? (
                    <span className="font-medium text-slate-600">
                      {url.total_clicks !== undefined
                        ? `${url.total_clicks.toLocaleString()} click${url.total_clicks !== 1 ? 's' : ''}`
                        : '— clicks'}
                    </span>
                  ) : (
                    <span className="w-16 h-3 bg-slate-200 rounded animate-pulse inline-block" />
                  )}
                </div>
              </div>

              <div className="flex items-center gap-1.5 shrink-0">
                <button
                  onClick={() => handleCopy(url.short_url, url.short_code)}
                  className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition"
                  title="Copy short URL"
                >
                  {copiedCode === url.short_code ? (
                    <Check className="w-4 h-4 text-green-600" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </button>
                <Link
                  to={`/analytics/${url.short_code}`}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-slate-600 border border-slate-300 rounded-lg hover:bg-slate-50 transition"
                >
                  <BarChart2 className="w-4 h-4" />
                  <span className="hidden sm:inline">Analytics</span>
                </Link>
                <a
                  href={url.short_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition"
                  title="Open URL"
                >
                  <ExternalLink className="w-4 h-4" />
                </a>
                <button
                  onClick={() => handleDelete(url.short_code)}
                  disabled={deletingCode === url.short_code}
                  className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition disabled:opacity-50"
                  title="Delete URL"
                >
                  {deletingCode === url.short_code ? (
                    <span className="w-4 h-4 border-2 border-slate-400 border-t-transparent rounded-full animate-spin block" />
                  ) : (
                    <Trash2 className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

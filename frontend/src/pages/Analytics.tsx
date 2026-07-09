import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { format, parseISO } from 'date-fns'
import {
  ArrowLeft,
  TrendingUp,
  Globe,
  Monitor,
  AlertCircle,
  MousePointerClick,
} from 'lucide-react'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { getAnalytics } from '../api/analytics'
import type { URLAnalytics, AttributeClick } from '../types'

const COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#3b82f6', '#f97316']

function StatCard({
  icon,
  label,
  value,
  accent,
}: {
  icon: React.ReactNode
  label: string
  value: string
  accent: string
}) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <div className={`inline-flex p-2 rounded-lg ${accent} mb-3`}>{icon}</div>
      <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">{label}</p>
      <p className="text-2xl font-bold text-slate-900 mt-0.5">{value}</p>
    </div>
  )
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <h3 className="text-sm font-semibold text-slate-700 mb-5">{title}</h3>
      {children}
    </div>
  )
}

function EmptyChart({ message = 'No data yet' }: { message?: string }) {
  return (
    <div className="h-44 flex flex-col items-center justify-center gap-2 text-slate-400">
      <TrendingUp className="w-8 h-8 opacity-30" />
      <p className="text-sm">{message}</p>
    </div>
  )
}

function DonutChart({ title, data }: { title: string; data: AttributeClick[] }) {
  const chartData = data.map((d) => ({ name: d.name || 'Unknown', value: d.click_count }))
  return (
    <ChartCard title={title}>
      {chartData.length === 0 ? (
        <EmptyChart />
      ) : (
        <ResponsiveContainer width="100%" height={200}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={48}
              outerRadius={75}
              dataKey="value"
              paddingAngle={2}
            >
              {chartData.map((_, index) => (
                <Cell key={index} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value: number) => [value.toLocaleString(), 'Clicks']}
              contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e2e8f0' }}
            />
            <Legend
              iconType="circle"
              iconSize={8}
              formatter={(value: string) => (
                <span style={{ fontSize: 12, color: '#475569' }}>{value}</span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      )}
    </ChartCard>
  )
}

function SkeletonAnalytics() {
  return (
    <div className="max-w-5xl mx-auto px-4 py-8 animate-pulse space-y-6">
      <div className="h-4 bg-slate-200 rounded w-32" />
      <div className="h-8 bg-slate-200 rounded w-48" />
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-24 bg-slate-200 rounded-xl" />
        ))}
      </div>
      <div className="h-64 bg-slate-200 rounded-xl" />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="h-64 bg-slate-200 rounded-xl" />
        <div className="h-64 bg-slate-200 rounded-xl" />
      </div>
    </div>
  )
}

export default function Analytics() {
  const { shortCode } = useParams<{ shortCode: string }>()
  const [analytics, setAnalytics] = useState<URLAnalytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!shortCode) return
    let cancelled = false
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const data = await getAnalytics(shortCode)
        if (!cancelled) setAnalytics(data)
      } catch (err: unknown) {
        if (!cancelled) {
          const axiosErr = err as { response?: { data?: { detail?: string } } }
          setError(axiosErr.response?.data?.detail || 'Failed to load analytics')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [shortCode])

  if (loading) return <SkeletonAnalytics />

  if (error || !analytics) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8">
        <Link
          to="/dashboard"
          className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 mb-6 transition"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to dashboard
        </Link>
        <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <p className="text-sm">{error || 'Analytics not found'}</p>
        </div>
      </div>
    )
  }

  const clicksOverTime = analytics.clicks_over_time.map((d) => ({
    date: format(parseISO(d.date), 'MMM d'),
    Clicks: d.click_count,
  }))

  const countriesData = analytics.top_countries
    .slice(0, 8)
    .map((c) => ({ name: c.country_code || 'Unknown', Clicks: c.click_count }))

  const referrersData = analytics.top_referrers
    .slice(0, 8)
    .map((r) => ({ name: r.referrer || 'Direct', Clicks: r.click_count }))

  const tooltipStyle = {
    fontSize: 12,
    borderRadius: 8,
    border: '1px solid #e2e8f0',
    boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
  }

  const axisStyle = { fontSize: 11, fill: '#94a3b8' }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <Link
        to="/dashboard"
        className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 mb-6 transition"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to dashboard
      </Link>

      <div className="mb-7">
        <h1 className="text-2xl font-bold text-slate-900 font-mono">/{analytics.short_code}</h1>
        <p className="text-sm text-slate-500 mt-1 truncate max-w-2xl">{analytics.original_url}</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <StatCard
          icon={<MousePointerClick className="w-5 h-5 text-indigo-600" />}
          label="Total Clicks"
          value={analytics.total_clicks.toLocaleString()}
          accent="bg-indigo-50"
        />
        <StatCard
          icon={<Globe className="w-5 h-5 text-violet-600" />}
          label="Countries"
          value={analytics.top_countries.length.toString()}
          accent="bg-violet-50"
        />
        <StatCard
          icon={<Monitor className="w-5 h-5 text-emerald-600" />}
          label="Device Types"
          value={analytics.device_breakdown.length.toString()}
          accent="bg-emerald-50"
        />
      </div>

      <ChartCard title="Clicks Over Time">
        {clicksOverTime.length === 0 ? (
          <EmptyChart message="No clicks recorded yet" />
        ) : (
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={clicksOverTime} margin={{ top: 4, right: 4, left: -16, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="date" tick={axisStyle} />
              <YAxis tick={axisStyle} allowDecimals={false} />
              <Tooltip contentStyle={tooltipStyle} />
              <Line
                type="monotone"
                dataKey="Clicks"
                stroke="#6366f1"
                strokeWidth={2}
                dot={{ r: 3, fill: '#6366f1', strokeWidth: 0 }}
                activeDot={{ r: 5, strokeWidth: 0 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </ChartCard>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <ChartCard title="Top Countries">
          {countriesData.length === 0 ? (
            <EmptyChart />
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart
                data={countriesData}
                layout="vertical"
                margin={{ top: 0, right: 8, left: 0, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                <XAxis type="number" tick={axisStyle} allowDecimals={false} />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={axisStyle}
                  width={52}
                />
                <Tooltip contentStyle={tooltipStyle} />
                <Bar dataKey="Clicks" fill="#6366f1" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        <ChartCard title="Top Referrers">
          {referrersData.length === 0 ? (
            <EmptyChart />
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart
                data={referrersData}
                layout="vertical"
                margin={{ top: 0, right: 8, left: 0, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                <XAxis type="number" tick={axisStyle} allowDecimals={false} />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={axisStyle}
                  width={80}
                  tickFormatter={(v: string) => (v.length > 14 ? v.slice(0, 14) + '…' : v)}
                />
                <Tooltip contentStyle={tooltipStyle} />
                <Bar dataKey="Clicks" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mt-6">
        <DonutChart title="Devices" data={analytics.device_breakdown} />
        <DonutChart title="Browsers" data={analytics.browser_breakdown} />
        <DonutChart title="Operating Systems" data={analytics.os_breakdown} />
      </div>
    </div>
  )
}

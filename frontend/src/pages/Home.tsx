import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link2, Copy, Check, ExternalLink, Zap, BarChart2, Shield } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { shortenURL } from '../api/urls'
import type { URLItem } from '../types'

const schema = z.object({
  original_url: z
    .string()
    .min(1, 'URL is required')
    .url('Please enter a valid URL')
    .refine(
      (val) => val.startsWith('http://') || val.startsWith('https://'),
      'URL must start with http:// or https://'
    ),
  custom_alias: z
    .string()
    .regex(/^[a-zA-Z0-9_-]*$/, 'Only letters, numbers, hyphens, and underscores are allowed')
    .min(3, 'Alias must be at least 3 characters')
    .max(30, 'Alias must be at most 30 characters')
    .optional()
    .or(z.literal('')),
  expires_at: z.string().optional(),
})

type FormData = z.infer<typeof schema>

export default function Home() {
  const { user } = useAuthStore()
  const [result, setResult] = useState<URLItem | null>(null)
  const [copied, setCopied] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<FormData>({ resolver: zodResolver(schema) })

  const onSubmit = async (data: FormData) => {
    setSubmitError(null)
    try {
      const payload = {
        original_url: data.original_url,
        ...(data.custom_alias ? { custom_alias: data.custom_alias } : {}),
        ...(data.expires_at ? { expires_at: new Date(data.expires_at).toISOString() } : {}),
      }
      const url = await shortenURL(payload)
      setResult(url)
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setSubmitError(
        axiosErr.response?.data?.detail || 'Something went wrong. Please try again.'
      )
    }
  }

  const handleCopy = async () => {
    if (!result) return
    await navigator.clipboard.writeText(result.short_url)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleNewLink = () => {
    setResult(null)
    setSubmitError(null)
    reset()
  }

  return (
    <div className="bg-gradient-to-br from-slate-50 to-indigo-50">
      <div className="max-w-2xl mx-auto px-4 pt-20 pb-16">
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-indigo-100 rounded-2xl mb-6">
            <Link2 className="w-8 h-8 text-indigo-600" />
          </div>
          <h1 className="text-4xl font-bold text-slate-900 sm:text-5xl tracking-tight">
            Shorten any URL
          </h1>
          <p className="mt-4 text-lg text-slate-500">
            Fast, free link shortening with built-in analytics.{' '}
            {!user && (
              <>
                <Link to="/signup" className="text-indigo-600 hover:text-indigo-700 font-medium">
                  Sign up
                </Link>{' '}
                for custom aliases and expiry dates.
              </>
            )}
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 sm:p-8">
          {!result ? (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Long URL
                </label>
                <input
                  {...register('original_url')}
                  type="text"
                  placeholder="https://example.com/very/long/url/that/needs/shortening"
                  autoFocus
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition placeholder:text-slate-400"
                  disabled={isSubmitting}
                />
                {errors.original_url && (
                  <p className="mt-1.5 text-sm text-red-600">{errors.original_url.message}</p>
                )}
              </div>

              {user && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                      Custom alias{' '}
                      <span className="text-slate-400 font-normal">(optional)</span>
                    </label>
                    <input
                      {...register('custom_alias')}
                      type="text"
                      placeholder="my-custom-link"
                      className="w-full px-4 py-3 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition placeholder:text-slate-400"
                      disabled={isSubmitting}
                    />
                    {errors.custom_alias && (
                      <p className="mt-1.5 text-sm text-red-600">{errors.custom_alias.message}</p>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                      Expires at{' '}
                      <span className="text-slate-400 font-normal">(optional)</span>
                    </label>
                    <input
                      {...register('expires_at')}
                      type="datetime-local"
                      min={new Date(Date.now() + 60_000).toISOString().slice(0, 16)}
                      className="w-full px-4 py-3 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition"
                      disabled={isSubmitting}
                    />
                    {errors.expires_at && (
                      <p className="mt-1.5 text-sm text-red-600">{errors.expires_at.message}</p>
                    )}
                  </div>
                </div>
              )}

              {submitError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                  {submitError}
                </div>
              )}

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-3 px-6 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-medium rounded-lg transition flex items-center justify-center gap-2 text-sm"
              >
                {isSubmitting ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Shortening...
                  </>
                ) : (
                  'Shorten URL'
                )}
              </button>
            </form>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-green-600 font-medium text-sm">
                <Check className="w-4 h-4" />
                Your link is ready
              </div>

              <div className="flex items-center gap-2 p-4 bg-slate-50 rounded-xl border border-slate-200">
                <span className="flex-1 text-sm font-mono text-indigo-600 truncate font-medium">
                  {result.short_url}
                </span>
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition shrink-0"
                >
                  {copied ? (
                    <>
                      <Check className="w-4 h-4 text-green-600" />
                      Copied
                    </>
                  ) : (
                    <>
                      <Copy className="w-4 h-4" />
                      Copy
                    </>
                  )}
                </button>
                <a
                  href={result.short_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-1.5 text-slate-400 hover:text-slate-600 transition shrink-0"
                  title="Open link"
                >
                  <ExternalLink className="w-4 h-4" />
                </a>
              </div>

              <p className="text-sm text-slate-500 truncate">
                <span className="font-medium text-slate-600">Original: </span>
                {result.original_url}
              </p>

              <div className="flex gap-3 pt-2">
                <button
                  onClick={handleNewLink}
                  className="flex-1 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg text-sm transition"
                >
                  Shorten another
                </button>
                {user && (
                  <Link
                    to="/dashboard"
                    className="flex-1 py-2.5 px-4 text-center bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-medium rounded-lg text-sm transition"
                  >
                    View dashboard
                  </Link>
                )}
              </div>
            </div>
          )}
        </div>

        {!user && (
          <p className="text-center text-sm text-slate-500 mt-5">
            Already have an account?{' '}
            <Link to="/login" className="text-indigo-600 hover:text-indigo-700 font-medium">
              Log in
            </Link>
          </p>
        )}
      </div>

      <div className="max-w-4xl mx-auto px-4 pb-20">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          {[
            {
              icon: <Zap className="w-5 h-5 text-indigo-600" />,
              bg: 'bg-indigo-50',
              title: 'Instant redirects',
              body: 'Redis-cached lookups serve redirects in single-digit milliseconds.',
            },
            {
              icon: <BarChart2 className="w-5 h-5 text-violet-600" />,
              bg: 'bg-violet-50',
              title: 'Built-in analytics',
              body: 'Track clicks by country, referrer, device, and browser over time.',
            },
            {
              icon: <Shield className="w-5 h-5 text-emerald-600" />,
              bg: 'bg-emerald-50',
              title: 'SSRF protected',
              body: 'Private and reserved IP ranges are blocked before shortening.',
            },
          ].map(({ icon, bg, title, body }) => (
            <div key={title} className="bg-white rounded-xl border border-slate-200 p-5">
              <div className={`inline-flex p-2 rounded-lg ${bg} mb-3`}>{icon}</div>
              <h3 className="font-semibold text-slate-900 text-sm">{title}</h3>
              <p className="text-sm text-slate-500 mt-1">{body}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

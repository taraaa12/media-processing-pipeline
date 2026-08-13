import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Search } from 'lucide-react'
import { useState } from 'react'
import { listImages } from '../api/images'
import { getImageUrl } from '../api/client'
import { PageLoader } from '../components/Loading'
import { StatusBadge } from '../components/StatusBadge'

export function HistoryPage() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [overallFilter, setOverallFilter] = useState('')
  const [sortBy, setSortBy] = useState('upload_time')
  const [sortOrder, setSortOrder] = useState('desc')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['images', page, search, statusFilter, overallFilter, sortBy, sortOrder, dateFrom, dateTo],
    queryFn: () =>
      listImages({
        page,
        page_size: 12,
        search: search || undefined,
        status: statusFilter || undefined,
        overall_status: overallFilter || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
        date_from: dateFrom ? new Date(dateFrom).toISOString() : undefined,
        date_to: dateTo ? new Date(dateTo + 'T23:59:59').toISOString() : undefined,
      }),
    refetchInterval: 15000,
  })

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">History</h2>
        <p className="text-slate-500">Browse and filter processed images</p>
      </div>

      <div className="flex flex-wrap gap-3">
        <div className="relative min-w-[200px] flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search filename or ID..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setPage(1)
            }}
            className="w-full rounded-lg border border-slate-300 py-2 pl-10 pr-3 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value)
            setPage(1)
          }}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        >
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="processing">Processing</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
        </select>
        <select
          value={overallFilter}
          onChange={(e) => {
            setOverallFilter(e.target.value)
            setPage(1)
          }}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        >
          <option value="">All results</option>
          <option value="good">Good</option>
          <option value="needs_review">Needs Review</option>
          <option value="poor">Poor</option>
          <option value="failed">Failed</option>
        </select>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        >
          <option value="upload_time">Sort by upload time</option>
          <option value="processing_start_time">Sort by processing start</option>
          <option value="processing_completion_time">Sort by completion time</option>
        </select>
        <select
          value={sortOrder}
          onChange={(e) => setSortOrder(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        >
          <option value="desc">Newest first</option>
          <option value="asc">Oldest first</option>
        </select>
        <input
          type="date"
          value={dateFrom}
          onChange={(e) => {
            setDateFrom(e.target.value)
            setPage(1)
          }}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          title="From date"
        />
        <input
          type="date"
          value={dateTo}
          onChange={(e) => {
            setDateTo(e.target.value)
            setPage(1)
          }}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          title="To date"
        />
      </div>

      {isLoading && <PageLoader />}
      {isError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
          {(error as Error).message}
        </div>
      )}

      {data && data.items.length === 0 && (
        <div className="rounded-xl border border-slate-200 bg-white py-16 text-center text-slate-400">
          No images found. <Link to="/upload" className="text-brand-600 hover:underline">Upload one</Link>
        </div>
      )}

      {data && data.items.length > 0 && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.items.map((item) => (
              <Link
                key={item.processing_id}
                to={`/processing/${item.processing_id}`}
                className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm transition hover:shadow-md"
              >
                <div className="aspect-video bg-slate-100">
                  <img
                    src={getImageUrl(item.processing_id)}
                    alt={item.original_filename}
                    className="h-full w-full object-cover"
                    onError={(e) => {
                      ;(e.target as HTMLImageElement).style.display = 'none'
                    }}
                  />
                </div>
                <div className="space-y-2 p-4">
                  <p className="truncate font-medium text-slate-800">{item.original_filename}</p>
                  <p className="truncate text-xs text-slate-400">{item.processing_id}</p>
                  <div className="flex flex-wrap gap-2">
                    <StatusBadge status={item.status} />
                    {item.overall_status && <StatusBadge status={item.overall_status} />}
                  </div>
                  <p className="text-xs text-slate-400">
                    {new Date(item.upload_time).toLocaleString()}
                    {item.overall_confidence != null && ` · ${(item.overall_confidence * 100).toFixed(0)}% conf.`}
                  </p>
                </div>
              </Link>
            ))}
          </div>

          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-500">
              Page {data.page} of {data.total_pages} ({data.total} total)
            </p>
            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="rounded-lg border border-slate-300 px-3 py-1 text-sm disabled:opacity-40"
              >
                Previous
              </button>
              <button
                disabled={page >= data.total_pages}
                onClick={() => setPage((p) => p + 1)}
                className="rounded-lg border border-slate-300 px-3 py-1 text-sm disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

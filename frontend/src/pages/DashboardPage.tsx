import { useQuery } from '@tanstack/react-query'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { getDashboardStats } from '../api/images'
import { LoadingSkeleton, PageLoader } from '../components/Loading'
import { StatCard } from '../components/StatCard'

const COLORS = ['#3b82f6', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#f97316']

export function DashboardPage() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: getDashboardStats,
    refetchInterval: 10000,
  })

  if (isLoading) return <PageLoader />
  if (isError || !data) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-700">
        Failed to load dashboard: {(error as Error)?.message}
      </div>
    )
  }

  const statusData = [
    { name: 'Pending', value: data.pending },
    { name: 'Processing', value: data.processing },
    { name: 'Completed', value: data.completed },
    { name: 'Failed', value: data.failed },
  ]

  const qualityData = [
    { name: 'Good', value: data.good },
    { name: 'Needs Review', value: data.needs_review },
    { name: 'Poor', value: data.poor },
  ]

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Dashboard</h2>
        <p className="text-slate-500">Overview of image processing pipeline activity</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard title="Total Uploads" value={data.total_uploads} accent="border-l-brand-500" />
        <StatCard
          title="In Queue"
          value={data.pending + data.processing}
          subtitle={`${data.pending} pending · ${data.processing} processing`}
          accent="border-l-amber-500"
        />
        <StatCard title="Completed" value={data.completed} accent="border-l-emerald-500" />
        <StatCard title="Failed" value={data.failed} accent="border-l-red-500" />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <StatCard
          title="Avg Processing Time"
          value={data.average_processing_time_seconds != null ? `${data.average_processing_time_seconds}s` : '—'}
          accent="border-l-violet-500"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="mb-4 font-semibold text-slate-800">Processing Status</h3>
          {data.total_uploads === 0 ? (
            <LoadingSkeleton className="h-64" />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={statusData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="mb-4 font-semibold text-slate-800">Quality Distribution</h3>
          {data.completed === 0 ? (
            <p className="py-16 text-center text-slate-400">No completed analyses yet</p>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={qualityData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label>
                  {qualityData.map((_, index) => (
                    <Cell key={index} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  )
}

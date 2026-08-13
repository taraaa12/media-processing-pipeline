import clsx from 'clsx'

const statusStyles: Record<string, string> = {
  pending: 'bg-amber-100 text-amber-800',
  processing: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  good: 'bg-emerald-100 text-emerald-800',
  needs_review: 'bg-yellow-100 text-yellow-800',
  poor: 'bg-orange-100 text-orange-800',
}

interface StatusBadgeProps {
  status: string
  className?: string
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const key = status.toLowerCase()
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize',
        statusStyles[key] || 'bg-slate-100 text-slate-700',
        className
      )}
    >
      {status.replace(/_/g, ' ')}
    </span>
  )
}

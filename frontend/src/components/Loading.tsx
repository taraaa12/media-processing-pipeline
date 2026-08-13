interface Props {
  className?: string
}

export function LoadingSkeleton({ className = 'h-32' }: Props) {
  return <div className={`animate-pulse rounded-lg bg-slate-200 ${className}`} />
}

export function PageLoader() {
  return (
    <div className="flex min-h-[40vh] items-center justify-center">
      <div className="h-10 w-10 animate-spin rounded-full border-4 border-brand-500 border-t-transparent" />
    </div>
  )
}

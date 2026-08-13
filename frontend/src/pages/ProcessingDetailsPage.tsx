import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, CheckCircle2, Clock, XCircle } from 'lucide-react'
import { getImage, getResults, getStatus } from '../api/images'
import { getImageUrl } from '../api/client'
import type { AnalysisResult } from '../types'
import { PageLoader } from '../components/Loading'
import { StatusBadge } from '../components/StatusBadge'

function formatDuration(start?: string | null, end?: string | null): string {
  if (!start || !end) return '—'
  const ms = new Date(end).getTime() - new Date(start).getTime()
  return `${(ms / 1000).toFixed(1)}s`
}

function AnalysisCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <h4 className="mb-2 font-semibold text-slate-800">{title}</h4>
      <div className="space-y-1 text-sm text-slate-600">{children}</div>
    </div>
  )
}

function ResultsGrid({ analysis }: { analysis: AnalysisResult }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <AnalysisCard title="Blur Detection">
        <p>Status: <span className="font-medium">{analysis.blur_status}</span></p>
        <p>Score: {analysis.blur_score?.toFixed(2)}</p>
        <p>Confidence: {((analysis.blur_confidence ?? 0) * 100).toFixed(0)}%</p>
        <p className="text-xs text-slate-400">Heuristic based on Laplacian variance</p>
      </AnalysisCard>

      <AnalysisCard title="Brightness">
        <p>Status: <span className="font-medium">{analysis.brightness_status}</span></p>
        <p>Score: {analysis.brightness_score?.toFixed(1)}</p>
        <p>Confidence: {((analysis.brightness_confidence ?? 0) * 100).toFixed(0)}%</p>
      </AnalysisCard>

      <AnalysisCard title="Duplicate Detection">
        <p>{analysis.is_duplicate ? 'Duplicate detected' : 'Unique image'}</p>
        {analysis.duplicate_original_processing_id && (
          <p>Original ID: {analysis.duplicate_original_processing_id}</p>
        )}
        {analysis.duplicate_match_type && <p>Match type: {analysis.duplicate_match_type}</p>}
      </AnalysisCard>

      <AnalysisCard title="OCR & Vehicle Number">
        <p>Vehicle: {analysis.vehicle_number || 'Not detected'}</p>
        <p>Valid format: {analysis.vehicle_number_valid ? 'Yes' : 'No / N/A'}</p>
        <p>OCR confidence: {((analysis.ocr_confidence ?? 0) * 100).toFixed(0)}%</p>
        {analysis.ocr_cleaned_text && (
          <p className="mt-1 truncate text-xs text-slate-400">{analysis.ocr_cleaned_text}</p>
        )}
      </AnalysisCard>

      <AnalysisCard title="Dimensions">
        <p>Valid: {analysis.dimension_valid ? 'Yes' : 'No'}</p>
        {analysis.dimension_details && (
          <p>
            {String(analysis.dimension_details.width)}×{String(analysis.dimension_details.height)}
            {' '}(aspect {String(analysis.dimension_details.aspect_ratio)})
          </p>
        )}
      </AnalysisCard>

      <AnalysisCard title="Screenshot / Photo-of-Photo">
        <p>Probability: {((analysis.screenshot_probability ?? 0) * 100).toFixed(0)}%</p>
        <p>Confidence: {((analysis.screenshot_confidence ?? 0) * 100).toFixed(0)}%</p>
        {analysis.screenshot_signals && Object.keys(analysis.screenshot_signals).length > 0 && (
          <ul className="mt-2 list-inside list-disc text-xs text-slate-500">
            {Object.entries(analysis.screenshot_signals).map(([key, val]) => (
              <li key={key}>{key}: {String(val)}</li>
            ))}
          </ul>
        )}
        <p className="text-xs text-slate-400">Heuristic — not definitive</p>
      </AnalysisCard>

      <AnalysisCard title="Tampering Indicators">
        <p>Probability: {((analysis.tampering_probability ?? 0) * 100).toFixed(0)}%</p>
        <p>Confidence: {((analysis.tampering_confidence ?? 0) * 100).toFixed(0)}%</p>
        {analysis.tampering_signals && Object.keys(analysis.tampering_signals).length > 0 && (
          <ul className="mt-2 list-inside list-disc text-xs text-slate-500">
            {Object.entries(analysis.tampering_signals).map(([key, val]) => (
              <li key={key}>{key}: {String(val)}</li>
            ))}
          </ul>
        )}
        <p className="text-xs text-slate-400">Not forensic-level certainty</p>
      </AnalysisCard>

      <AnalysisCard title="Overall Result">
        <div className="flex items-center gap-2">
          <StatusBadge status={analysis.overall_status || 'unknown'} />
          <span className="font-medium">Score: {analysis.overall_score?.toFixed(2)}</span>
        </div>
        <p>Confidence: {((analysis.overall_confidence ?? 0) * 100).toFixed(0)}%</p>
        {analysis.detected_issues && analysis.detected_issues.length > 0 && (
          <ul className="mt-2 list-inside list-disc text-amber-700">
            {analysis.detected_issues.map((issue, i) => (
              <li key={i}>{issue}</li>
            ))}
          </ul>
        )}
      </AnalysisCard>
    </div>
  )
}

function AnalyzerDetailsSection({ details }: { details: Record<string, unknown> }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6">
      <h3 className="mb-4 font-semibold text-slate-800">Analyzer Details (raw)</h3>
      <div className="grid gap-3 sm:grid-cols-2">
        {Object.entries(details).map(([name, data]) => (
          <div key={name} className="rounded-lg border border-slate-100 bg-slate-50 p-3">
            <p className="font-medium capitalize text-slate-700">{name.replace(/_/g, ' ')}</p>
            <pre className="mt-1 overflow-x-auto text-xs text-slate-600">
              {JSON.stringify(data, null, 2)}
            </pre>
          </div>
        ))}
      </div>
    </div>
  )
}

const timelineSteps = ['pending', 'processing', 'completed'] as const

export function ProcessingDetailsPage() {
  const { id } = useParams<{ id: string }>()

  const statusQuery = useQuery({
    queryKey: ['status', id],
    queryFn: () => getStatus(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === 'completed' || status === 'failed') return false
      return 2000
    },
  })

  const imageQuery = useQuery({
    queryKey: ['image', id],
    queryFn: () => getImage(id!),
    enabled: !!id,
    refetchInterval: () => {
      const status = statusQuery.data?.status
      if (status === 'completed' || status === 'failed') return false
      return 3000
    },
  })

  const resultsQuery = useQuery({
    queryKey: ['results', id],
    queryFn: () => getResults(id!),
    enabled: !!id && (statusQuery.data?.status === 'completed' || statusQuery.data?.status === 'failed'),
  })

  if (!id) return <p>Invalid processing ID</p>
  if (statusQuery.isLoading || imageQuery.isLoading) return <PageLoader />

  const status = statusQuery.data?.status || 'unknown'
  const image = imageQuery.data
  const analysis = resultsQuery.data?.analysis

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Processing Details</h2>
          <p className="font-mono text-sm text-slate-500">{id}</p>
        </div>
        <StatusBadge status={status} className="text-sm" />
      </div>

      {/* Timeline */}
      <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white p-4">
        {timelineSteps.map((step, i) => {
          const isActive =
            status === step ||
            (step === 'pending' && ['processing', 'completed', 'failed'].includes(status)) ||
            (step === 'processing' && ['completed', 'failed'].includes(status))
          const isFailed = status === 'failed' && step === 'completed'
          const Icon =
            isFailed ? XCircle : isActive ? CheckCircle2 : Clock
          return (
            <div key={step} className="flex flex-1 items-center gap-2">
              <Icon
                className={`h-5 w-5 ${
                  isFailed ? 'text-red-500' : isActive ? 'text-emerald-500' : 'text-slate-300'
                }`}
              />
              <span className="text-sm capitalize text-slate-600">{step}</span>
              {i < timelineSteps.length - 1 && <div className="mx-2 h-px flex-1 bg-slate-200" />}
            </div>
          )
        })}
      </div>

      {status === 'failed' && image?.failure_reason && (
        <div className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" />
          <div>
            <p className="font-medium">Processing Failed</p>
            <p className="text-sm">{image.failure_reason}</p>
          </div>
        </div>
      )}

      {image && (
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
            <img
              src={getImageUrl(id)}
              alt={image.original_filename}
              className="max-h-96 w-full object-contain bg-slate-50"
            />
          </div>
          <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-6">
            <p><span className="text-slate-500">Filename:</span> {image.original_filename}</p>
            <p><span className="text-slate-500">Uploaded:</span> {new Date(image.upload_time).toLocaleString()}</p>
            <p><span className="text-slate-500">Size:</span> {(image.file_size / 1024).toFixed(1)} KB</p>
            <p><span className="text-slate-500">Dimensions:</span> {image.width}×{image.height}</p>
            <p><span className="text-slate-500">Duration:</span> {formatDuration(image.processing_start_time, image.processing_completion_time)}</p>
            <p className="truncate text-xs text-slate-400">SHA-256: {image.sha256_hash}</p>
          </div>
        </div>
      )}

      {(status === 'pending' || status === 'processing') && (
        <div className="flex items-center gap-3 rounded-lg border border-blue-200 bg-blue-50 p-4 text-blue-800">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
          <p>Processing in progress... Results will appear automatically.</p>
        </div>
      )}

      {analysis && <ResultsGrid analysis={analysis} />}
      {analysis?.analyzer_details && Object.keys(analysis.analyzer_details).length > 0 && (
        <AnalyzerDetailsSection details={analysis.analyzer_details} />
      )}
    </div>
  )
}

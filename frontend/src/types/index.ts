export interface UploadResponse {
  processing_id: string
  status: string
  message: string
}

export interface AnalysisResult {
  blur_score?: number | null
  blur_status?: string | null
  blur_confidence?: number | null
  brightness_score?: number | null
  brightness_status?: string | null
  brightness_confidence?: number | null
  is_duplicate: boolean
  duplicate_original_processing_id?: string | null
  duplicate_confidence?: number | null
  duplicate_match_type?: string | null
  ocr_raw_text?: string | null
  ocr_cleaned_text?: string | null
  vehicle_number?: string | null
  vehicle_number_valid?: boolean | null
  ocr_confidence?: number | null
  screenshot_probability?: number | null
  screenshot_confidence?: number | null
  screenshot_signals?: Record<string, unknown> | null
  tampering_probability?: number | null
  tampering_confidence?: number | null
  tampering_signals?: Record<string, unknown> | null
  dimension_valid?: boolean | null
  dimension_details?: Record<string, unknown> | null
  overall_score?: number | null
  overall_status?: string | null
  overall_confidence?: number | null
  detected_issues?: string[] | null
  analyzer_details?: Record<string, unknown> | null
}

export interface ImageDetail {
  processing_id: string
  original_filename: string
  mime_type: string
  file_size: number
  width?: number | null
  height?: number | null
  status: string
  upload_time: string
  processing_start_time?: string | null
  processing_completion_time?: string | null
  failure_reason?: string | null
  sha256_hash: string
  analysis_result?: AnalysisResult | null
}

export interface StatusResponse {
  processing_id: string
  status: string
  message?: string | null
  processing_start_time?: string | null
  processing_completion_time?: string | null
}

export interface ResultsResponse {
  processing_id: string
  status: string
  analysis?: AnalysisResult | null
}

export interface ImageListItem {
  processing_id: string
  original_filename: string
  status: string
  upload_time: string
  overall_status?: string | null
  overall_confidence?: number | null
  thumbnail_url?: string | null
}

export interface PaginatedImageList {
  items: ImageListItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface DashboardStats {
  total_uploads: number
  pending: number
  processing: number
  completed: number
  failed: number
  good: number
  needs_review: number
  poor: number
  average_processing_time_seconds?: number | null
}

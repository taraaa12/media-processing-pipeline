import type {
  DashboardStats,
  ImageDetail,
  PaginatedImageList,
  ResultsResponse,
  StatusResponse,
  UploadResponse,
} from '../types'
import { apiClient } from './client'

export async function uploadImage(file: File, onProgress?: (pct: number) => void): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await apiClient.post<UploadResponse>('/api/v1/images/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (event) => {
      if (event.total && onProgress) {
        onProgress(Math.round((event.loaded * 100) / event.total))
      }
    },
  })
  return data
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const { data } = await apiClient.get<DashboardStats>('/api/v1/images/stats/dashboard')
  return data
}

export async function listImages(params: {
  page?: number
  page_size?: number
  status?: string
  overall_status?: string
  search?: string
  date_from?: string
  date_to?: string
  sort_by?: string
  sort_order?: string
}): Promise<PaginatedImageList> {
  const { data } = await apiClient.get<PaginatedImageList>('/api/v1/images', { params })
  return data
}

export async function getImage(processingId: string): Promise<ImageDetail> {
  const { data } = await apiClient.get<ImageDetail>(`/api/v1/images/${processingId}`)
  return data
}

export async function getStatus(processingId: string): Promise<StatusResponse> {
  const { data } = await apiClient.get<StatusResponse>(`/api/v1/images/${processingId}/status`)
  return data
}

export async function getResults(processingId: string): Promise<ResultsResponse> {
  const { data } = await apiClient.get<ResultsResponse>(`/api/v1/images/${processingId}/results`)
  return data
}

export async function getFailure(processingId: string): Promise<{ failure_reason?: string }> {
  const { data } = await apiClient.get(`/api/v1/images/${processingId}/failure`)
  return data
}

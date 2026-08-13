import axios from 'axios'

/**
 * API base URL strategy:
 * - Empty/unset (default): same-origin requests via nginx /api proxy (Docker) or Vite dev proxy.
 * - http://localhost:8000: direct backend access for local dev without proxy.
 */
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.message ||
      'An unexpected error occurred'
    return Promise.reject(new Error(typeof message === 'string' ? message : JSON.stringify(message)))
  }
)

export function getImageUrl(processingId: string): string {
  return `${API_BASE_URL}/api/v1/images/${processingId}/file`
}

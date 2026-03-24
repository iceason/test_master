import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, InternalAxiosRequestConfig } from 'axios'

const AccessTokenKey = 'admin-token'
const RefreshTokenKey = 'admin-refresh-token'

export function getToken() {
  return localStorage.getItem(AccessTokenKey)
}

export function setToken(token: string) {
  return localStorage.setItem(AccessTokenKey, token)
}

export function removeToken() {
  return localStorage.removeItem(AccessTokenKey)
}

export function getRefreshToken() {
  return localStorage.getItem(RefreshTokenKey)
}

export function setRefreshToken(token: string) {
  return localStorage.setItem(RefreshTokenKey, token)
}

export function removeRefreshToken() {
  return localStorage.removeItem(RefreshTokenKey)
}

const KEEP_PAGINATION_KEY = '__keepPagination__'

let isRefreshing = false
let pendingRequests: Array<{
  resolve: (token: string) => void
  reject: (error: any) => void
}> = []

function processPendingRequests(token: string | null, error: any = null) {
  pendingRequests.forEach(({ resolve, reject }) => {
    if (token) {
      resolve(token)
    } else {
      reject(error)
    }
  })
  pendingRequests = []
}

function createInstance() {
  const instance = axios.create()
  
  instance.interceptors.request.use(
    config => config,
    error => Promise.reject(error)
  )

  instance.interceptors.response.use(
    (response) => {
      const apiData = response.data
      const responseType = response.config.responseType
      if (responseType === 'blob' || responseType === 'arraybuffer') return apiData
      
      if (typeof apiData.code === 'number' && apiData.code !== undefined) {
        if (apiData.code === 0) {
          return apiData.data
        } else {
          console.error(apiData.message || 'Error')
          return Promise.reject(new Error(apiData.message || 'Error'))
        }
      }
      
      if (apiData && typeof apiData === 'object' && 'results' in apiData && Array.isArray(apiData.results)) {
        if ((response.config as any)[KEEP_PAGINATION_KEY]) {
          return apiData
        }
        return apiData.results
      }
      
      return apiData
    },
    async (error) => {
      const status = error.response?.status
      const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

      if (status === 401 && !originalRequest._retry) {
        const refreshToken = getRefreshToken()

        if (!refreshToken) {
          removeToken()
          removeRefreshToken()
          window.location.reload()
          return Promise.reject(error)
        }

        if (isRefreshing) {
          return new Promise((resolve, reject) => {
            pendingRequests.push({ resolve, reject })
          }).then((newToken) => {
            originalRequest.headers['Authorization'] = `Bearer ${newToken}`
            return instance(originalRequest)
          })
        }

        originalRequest._retry = true
        isRefreshing = true

        try {
          const base = (import.meta as any).env?.VITE_API_BASE || '/api'
          const res = await axios.post(`${base}/token/refresh/`, { refresh: refreshToken })
          const data = res.data

          if (data.code === 0 && data.data) {
            const newAccess = data.data.access
            const newRefresh = data.data.refresh
            setToken(newAccess)
            if (newRefresh) setRefreshToken(newRefresh)
            processPendingRequests(newAccess)
            originalRequest.headers['Authorization'] = `Bearer ${newAccess}`
            return instance(originalRequest)
          } else {
            throw new Error('refresh failed')
          }
        } catch (refreshError) {
          processPendingRequests(null, refreshError)
          removeToken()
          removeRefreshToken()
          window.location.reload()
          return Promise.reject(refreshError)
        } finally {
          isRefreshing = false
        }
      }
      
      const message = error.response?.data?.detail || error.response?.data?.error || error.response?.data?.message || error.message
      console.error(message)
      return Promise.reject(error)
    }
  )
  return instance
}

function getDefaultConfig(): AxiosRequestConfig {
  const token = getToken()
  const base = (import.meta as any).env?.VITE_API_BASE || '/api'
  return {
    baseURL: base,
    headers: {
      'Authorization': token ? `Bearer ${token}` : undefined,
      'Content-Type': 'application/json'
    },
    timeout: 30000,
  }
}

function createRequest(instance: AxiosInstance) {
  return <T>(config: AxiosRequestConfig): Promise<T> => {
    const mergeConfig = { ...getDefaultConfig(), ...config }
    return instance(mergeConfig)
  }
}

const instance = createInstance()
export const request = createRequest(instance)

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

/**
 * Request that preserves the full DRF paginated response
 * (count, next, previous, results) without auto-unwrapping.
 */
export function paginatedRequest<T>(config: AxiosRequestConfig): Promise<PaginatedResponse<T>> {
  const mergeConfig = { ...getDefaultConfig(), ...config, [KEEP_PAGINATION_KEY]: true }
  return instance(mergeConfig)
}

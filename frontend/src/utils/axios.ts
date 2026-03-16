import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig } from 'axios'

// 简单的 LocalStorage 封装
const TokenKey = 'admin-token'

export function getToken() {
  return localStorage.getItem(TokenKey)
}

export function setToken(token: string) {
  return localStorage.setItem(TokenKey, token)
}

export function removeToken() {
  return localStorage.removeItem(TokenKey)
}

const KEEP_PAGINATION_KEY = '__keepPagination__'

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
      
      // 如果存在 code 字段，按业务逻辑判断（自定义响应格式）
      if (apiData.code !== undefined) {
        if (apiData.code === 0) {
          return apiData.data
        } else {
          console.error(apiData.message || 'Error')
          return Promise.reject(new Error(apiData.message || 'Error'))
        }
      }
      
      // DRF 分页响应格式: { count, next, previous, results }
      if (apiData && typeof apiData === 'object' && 'results' in apiData && Array.isArray(apiData.results)) {
        // 如果请求标记了保留分页信息，返回完整结构
        if ((response.config as any)[KEEP_PAGINATION_KEY]) {
          return apiData
        }
        // 否则自动解包 results 数组
        return apiData.results
      }
      
      // 其他情况直接返回（DRF 标准返回、单个对象等）
      return apiData
    },
    (error) => {
      const status = error.response?.status
      const message = error.response?.data?.detail || error.response?.data?.message || error.message
      
      if (status === 401) {
        // Token 过期
        removeToken()
        window.location.reload()
      }
      
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
      'Authorization': token ? `Token ${token}` : undefined,
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

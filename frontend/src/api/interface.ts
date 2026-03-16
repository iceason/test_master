import { request } from '@/utils/axios'

// 接口相关类型
export interface Interface {
  id: number
  name: string
  method: string
  path: string
  directory: number
  schema?: Record<string, any> // 后端是 JSONField
  schema_yaml?: string // 后端 WriteOnly
  created_at: string
  updated_at: string
}

export const getInterfaces = (params?: any) => {
  return request<Interface[]>({
    url: 'interfaces/',
    method: 'get',
    params
  })
}

export const createInterface = (data: Partial<Interface>) => {
  return request<Interface>({
    url: 'interfaces/',
    method: 'post',
    data
  })
}

export const updateInterface = (id: number, data: Partial<Interface>) => {
  return request<Interface>({
    url: `interfaces/${id}/`,
    method: 'put',
    data
  })
}

export const deleteInterface = (id: number) => {
  return request<void>({
    url: `interfaces/${id}/`,
    method: 'delete'
  })
}

// 批量删除接口
export const batchDeleteInterfaces = (ids: number[]) => {
  return request<void>({
    url: 'interfaces/batch_delete/',
    method: 'post',
    data: { ids }
  })
}

// 生成用例接口
export const generateTestCases = (interfaceId: number, data?: { category_ids: number[] }) => {
  return request<any>({
    url: `interfaces/${interfaceId}/generate_cases/`,
    method: 'post',
    data
  })
}

// OpenAPI 导入相关类型
export interface ImportResult {
  total: number
  created: number
  updated: number
  failed: number
  created_items: Array<{ id: number; name: string; method: string; path: string }>
  updated_items: Array<{ id: number; name: string; method: string; path: string }>
  errors: Array<{ method: string; path: string; error: string }>
}

export interface PreviewInfo {
  title: string
  version: string
  description: string
  totalApis: number
  tags: string[]
}

// 导入 OpenAPI 文档
export const importOpenAPI = (file: File, directoryId: number) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('directory_id', directoryId.toString())

  return request<ImportResult>({
    url: 'import-openapi/',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 预览 OpenAPI 文档信息
export const previewOpenAPI = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)

  return request<PreviewInfo>({
    url: 'import-openapi/preview/',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

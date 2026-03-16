import { request, paginatedRequest } from '@/utils/axios'
import type { PaginatedResponse } from '@/utils/axios'

// 用例相关类型
export interface TestCase {
  id: number
  interface: number
  project?: number | null
  category?: number | null
  name: string
  description: string
  test_field: string
  request_data: Record<string, any>
  expected_value: Record<string, any>
  expected_response?: Record<string, any>
  created_at: string
  updated_at: string
  category_name?: string
  project_name?: string | null
  test_type?: 'positive' | 'negative' | 'boundary' | 'security'
  strategy?: string
}

export const getTestCases = (params?: any) => {
  return request<TestCase[]>({
    url: 'testcases/',
    method: 'get',
    params
  })
}

export interface TestCaseQueryParams {
  page?: number
  page_size?: number
  search?: string
  interface?: number | null
  project?: number | null
  test_type?: string | null
  ordering?: string
  no_page?: boolean
}

export const getTestCasesPaginated = (params?: TestCaseQueryParams): Promise<PaginatedResponse<TestCase>> => {
  return paginatedRequest<TestCase>({
    url: 'testcases/',
    method: 'get',
    params
  })
}

export const createTestCase = (data: Partial<TestCase>) => {
  return request<TestCase>({
    url: 'testcases/',
    method: 'post',
    data
  })
}

export const updateTestCase = (id: number, data: Partial<TestCase>) => {
  return request<TestCase>({
    url: `testcases/${id}/`,
    method: 'put',
    data
  })
}

export const deleteTestCase = (id: number) => {
  return request<void>({
    url: `testcases/${id}/`,
    method: 'delete'
  })
}

// 批量删除用例
export const batchDeleteTestCases = (ids: number[]) => {
  return request<void>({
    url: 'testcases/batch_delete/',
    method: 'post',
    data: { ids }
  })
}

export const exportTestCases = (format: 'excel' | 'xmind' | 'json', ids: number[]) => {
  // 映射前端格式到后端支持的格式
  let backendFormat = format;
  if (format === 'xmind') {
    // 暂时将xmind映射到json，直到后端支持xmind
    backendFormat = 'json';
  }
  
  return request<Blob>({
    url: 'export/',
    method: 'post',
    data: { 
      scope: 'testcase', // 使用正确的scope参数形式
      ids,
      format: backendFormat
    },
    responseType: 'blob'
  })
}

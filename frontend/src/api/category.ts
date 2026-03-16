import { request } from '@/utils/axios'

export interface TestCaseCategory {
  id: number
  name: string
  code: string
  parent?: number
  description?: string
  sub_categories?: TestCaseCategory[]
}

export const getCategories = () => {
  return request<TestCaseCategory[]>({
    url: 'categories/',
    method: 'get'
  })
}

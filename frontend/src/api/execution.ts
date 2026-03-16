/**
 * 测试执行相关API
 */

import { request } from '@/utils/axios'

// 获取环境列表
export const getEnvironments = (params?: any) => {
  return request({
    url: 'environments/',
    method: 'get',
    params
  })
}

// 批量执行测试用例
export const executeTestCases = (data: {
  name: string
  case_ids: number[]
  environment: number
  parallel?: boolean
  executor?: string
}) => {
  return request({
    url: 'execution-batches/execute_cases/',
    method: 'post',
    data
  })
}

// 获取批次状态
export const getBatchStatus = (id: number) => {
  return request({
    url: `execution-batches/${id}/status/`,
    method: 'get'
  })
}

// 获取批次详情
export const getBatchDetail = (id: number) => {
  return request({
    url: `execution-batches/${id}/`,
    method: 'get'
  })
}

// 获取批次列表
export const getBatchList = (params?: any) => {
  return request({
    url: 'execution-batches/',
    method: 'get',
    params
  })
}

// 获取执行记录列表
export const getExecutionList = (params?: any) => {
  return request({
    url: 'executions/',
    method: 'get',
    params
  })
}

// 执行单个测试用例
export const executeSingleCase = (data: {
  case_id: number
  environment: number
}) => {
  return request({
    url: 'executions/execute_single/',
    method: 'post',
    data
  })
}

// YAML导出
export const exportYaml = (data: {
  scope: string
  ids: number[]
}) => {
  return request({
    url: 'yaml/export/',
    method: 'post',
    data,
    responseType: 'blob'
  })
}

// YAML导入
export const importYaml = (data: {
  yaml_content: string
  mode: string
}) => {
  return request({
    url: 'yaml/import/',
    method: 'post',
    data
  })
}

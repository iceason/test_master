/**
 * Testing module API: ExecutorMachines, BuildPlans, BuildExecutions
 */
import { request } from '@/utils/axios'

// -----------------------------------------------------------------------
// Executor Machines
// -----------------------------------------------------------------------

export const getExecutorMachines = (params?: any) =>
  request({ url: 'executor-machines/', method: 'get', params })

export const getExecutorMachine = (id: number) =>
  request({ url: `executor-machines/${id}/`, method: 'get' })

export const createExecutorMachine = (data: any) =>
  request({ url: 'executor-machines/', method: 'post', data })

export const updateExecutorMachine = (id: number, data: any) =>
  request({ url: `executor-machines/${id}/`, method: 'put', data })

export const deleteExecutorMachine = (id: number) =>
  request({ url: `executor-machines/${id}/`, method: 'delete' })

export const pingExecutorMachine = (id: number) =>
  request({ url: `executor-machines/${id}/ping/`, method: 'post' })

// -----------------------------------------------------------------------
// Build Plans
// -----------------------------------------------------------------------

export const getBuildPlans = (params?: any) =>
  request({ url: 'build-plans/', method: 'get', params })

export const getBuildPlan = (id: number) =>
  request({ url: `build-plans/${id}/`, method: 'get' })

export const createBuildPlan = (data: any) =>
  request({ url: 'build-plans/', method: 'post', data })

export const updateBuildPlan = (id: number, data: any) =>
  request({ url: `build-plans/${id}/`, method: 'put', data })

export const deleteBuildPlan = (id: number) =>
  request({ url: `build-plans/${id}/`, method: 'delete' })

export const triggerBuildPlan = (id: number) =>
  request({ url: `build-plans/${id}/trigger/`, method: 'post' })

export const getBuildPlanExecutions = (id: number, params?: any) =>
  request({ url: `build-plans/${id}/executions/`, method: 'get', params })

// -----------------------------------------------------------------------
// Build Executions
// -----------------------------------------------------------------------

export const getBuildExecutions = (params?: any) =>
  request({ url: 'build-executions/', method: 'get', params })

export const getBuildExecution = (id: number) =>
  request({ url: `build-executions/${id}/`, method: 'get' })

export const getBuildExecutionLogs = (id: number) =>
  request({ url: `build-executions/${id}/logs/`, method: 'get' })

export const downloadBuildExecutionLog = (id: number) =>
  request({ url: `build-executions/${id}/log_download/`, method: 'get', responseType: 'blob' })

export const getBuildExecutionReport = (id: number) =>
  request({ url: `build-executions/${id}/report/`, method: 'get' })

export const cancelBuildExecution = (id: number) =>
  request({ url: `build-executions/${id}/cancel/`, method: 'post' })

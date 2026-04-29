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

export const testJenkinsConnection = (machineId: number) =>
  request({ url: `executor-machines/${machineId}/test-jenkins/`, method: 'post' })

// -----------------------------------------------------------------------
// Build Plans
// -----------------------------------------------------------------------

export const getBuildPlans = (params?: any) =>
  request({ url: 'build-plans/', method: 'get', params })

export const getBuildPlan = (id: number) => request({ url: `build-plans/${id}/`, method: 'get' })

export const createBuildPlan = (data: any) => request({ url: 'build-plans/', method: 'post', data })

export const updateBuildPlan = (id: number, data: any) =>
  request({ url: `build-plans/${id}/`, method: 'put', data })

export const deleteBuildPlan = (id: number) =>
  request({ url: `build-plans/${id}/`, method: 'delete' })

export const triggerBuildPlan = (id: number) =>
  request({ url: `build-plans/${id}/trigger/`, method: 'post' })

export const getBuildPlanExecutions = (id: number, params?: any) =>
  request({ url: `build-plans/${id}/executions/`, method: 'get', params })

export const getJenkinsfilePreview = (planId: number) =>
  request({ url: `build-plans/${planId}/jenkinsfile_preview/`, method: 'get' })

export const getBuildPlanJenkinsEnv = () =>
  request<{ backend_base_url: string }>({ url: 'build-plans/jenkins-env/', method: 'get' })

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

export const stopBuildPlan = (id: number) =>
  request({ url: `build-plans/${id}/stop/`, method: 'post' })

export const refreshBuildPlanStatus = (id: number) =>
  request({ url: `build-plans/${id}/refresh_status/`, method: 'post' })

export const syncJenkinsJob = (id: number) =>
  request({ url: `build-plans/${id}/sync_jenkins/`, method: 'post' })

export const getProgressiveLog = (executionId: number, start?: number) =>
  request({
    url: `build-executions/${executionId}/progressive_log/`,
    method: 'get',
    params: start !== undefined ? { start } : undefined,
  })

// -----------------------------------------------------------------------
// Environments
// -----------------------------------------------------------------------

export const getEnvironments = (params?: any) =>
  request({ url: 'environments/', method: 'get', params })

export const getEnvironment = (id: number) => request({ url: `environments/${id}/`, method: 'get' })

export const createEnvironment = (data: any) =>
  request({ url: 'environments/', method: 'post', data })

export const updateEnvironment = (id: number, data: any) =>
  request({ url: `environments/${id}/`, method: 'put', data })

export const deleteEnvironment = (id: number) =>
  request({ url: `environments/${id}/`, method: 'delete' })

// -----------------------------------------------------------------------
// Email Templates
// -----------------------------------------------------------------------

export const getEmailTemplates = (params?: any) =>
  request({ url: 'email-templates/', method: 'get', params })

export const getEmailTemplate = (id: number) =>
  request({ url: `email-templates/${id}/`, method: 'get' })

export const createEmailTemplate = (data: any) =>
  request({ url: 'email-templates/', method: 'post', data })

export const updateEmailTemplate = (id: number, data: any) =>
  request({ url: `email-templates/${id}/`, method: 'put', data })

export const deleteEmailTemplate = (id: number) =>
  request({ url: `email-templates/${id}/`, method: 'delete' })

export const setDefaultEmailTemplate = (id: number) =>
  request({ url: `email-templates/${id}/set_default/`, method: 'post' })

export const previewEmailTemplate = (id: number) =>
  request({ url: `email-templates/${id}/preview/`, method: 'post' })

export const previewCustomEmailTemplate = (data: { subject: string; body: string }) =>
  request({ url: 'email-templates/preview_custom/', method: 'post', data })

// -----------------------------------------------------------------------
// DingTalk Groups
// -----------------------------------------------------------------------

export const getDingTalkGroups = (params?: any) =>
  request({ url: 'dingtalk-groups/', method: 'get', params })

export const createDingTalkGroup = (data: any) =>
  request({ url: 'dingtalk-groups/', method: 'post', data })

export const updateDingTalkGroup = (id: number, data: any) =>
  request({ url: `dingtalk-groups/${id}/`, method: 'put', data })

export const deleteDingTalkGroup = (id: number) =>
  request({ url: `dingtalk-groups/${id}/`, method: 'delete' })

export const testDingTalkGroupSend = (id: number, data?: any) =>
  request({ url: `dingtalk-groups/${id}/test-send/`, method: 'post', data })

// -----------------------------------------------------------------------
// DingTalk Templates
// -----------------------------------------------------------------------

export const getDingTalkTemplates = (params?: any) =>
  request({ url: 'dingtalk-templates/', method: 'get', params })

export const createDingTalkTemplate = (data: any) =>
  request({ url: 'dingtalk-templates/', method: 'post', data })

export const updateDingTalkTemplate = (id: number, data: any) =>
  request({ url: `dingtalk-templates/${id}/`, method: 'put', data })

export const deleteDingTalkTemplate = (id: number) =>
  request({ url: `dingtalk-templates/${id}/`, method: 'delete' })

export const setDefaultDingTalkTemplate = (id: number) =>
  request({ url: `dingtalk-templates/${id}/set_default/`, method: 'post' })

export const previewDingTalkTemplate = (id: number) =>
  request({ url: `dingtalk-templates/${id}/preview/`, method: 'post' })

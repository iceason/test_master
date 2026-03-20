<template>
  <v-container fluid class="detail-root">
    <!-- Top Bar -->
    <div class="detail-topbar mb-5">
      <div class="d-flex align-center">
        <v-btn icon="mdi-arrow-left" variant="text" size="small" class="mr-2" @click="$router.back()" />
        <div class="flex-grow-1">
          <div class="d-flex align-center ga-3">
            <span class="text-h6 font-weight-bold">{{ plan.name }}</span>
            <v-chip
              :color="plan.status === 'active' ? 'success' : 'grey'"
              size="small" variant="flat" class="font-weight-bold"
            >
              {{ plan.status === 'active' ? $t('testing.plans.status.active') : $t('testing.plans.status.disabled') }}
            </v-chip>
            <v-chip v-if="latestExec" :color="getExecStatusColor(latestExec.status)" size="small" variant="tonal">
              {{ $t(`testing.executions.status.${latestExec.status}`) }}
            </v-chip>
          </div>
          <div v-if="plan.description" class="text-body-2 text-medium-emphasis mt-1">{{ plan.description }}</div>
        </div>
        <div class="d-flex align-center ga-2">
          <v-btn color="default" variant="tonal" prepend-icon="mdi-refresh" @click="refreshStatus" :loading="refreshing" class="text-none" rounded="lg" size="small">
            {{ $t('common.refresh') }}
          </v-btn>
          <v-btn color="teal" prepend-icon="mdi-play-circle-outline" @click="confirmTriggerDialog = true" :loading="triggering" class="text-none" rounded="lg" variant="flat">
            {{ $t('testing.plans.trigger') }}
          </v-btn>
        </div>
      </div>
    </div>

    <!-- Plan Metadata -->
    <v-sheet class="detail-meta rounded-xl mb-5" elevation="0">
      <div class="meta-grid">
        <div class="meta-item">
          <v-avatar size="40" color="teal" variant="tonal" rounded="lg" class="meta-icon">
            <v-icon size="22" color="teal">mdi-server-network</v-icon>
          </v-avatar>
          <div class="meta-text">
            <div class="meta-label">执行机器</div>
            <div class="meta-value">{{ plan.executor_machine_name || 'Jenkins Master' }}</div>
          </div>
        </div>
        <div class="meta-divider" />
        <div class="meta-item">
          <v-avatar size="40" color="blue" variant="tonal" rounded="lg" class="meta-icon">
            <v-icon size="22" color="blue">mdi-pipe</v-icon>
          </v-avatar>
          <div class="meta-text">
            <div class="meta-label">Jenkins Job</div>
            <div class="meta-value">{{ plan.jenkins_job_name || '-' }}</div>
          </div>
        </div>
        <div class="meta-divider" />
        <div class="meta-item">
          <v-avatar size="40" :color="plan.is_cron_enabled ? 'orange' : 'grey'" variant="tonal" rounded="lg" class="meta-icon">
            <v-icon size="22" :color="plan.is_cron_enabled ? 'orange' : 'grey'">mdi-timer-cog-outline</v-icon>
          </v-avatar>
          <div class="meta-text">
            <div class="meta-label">定时任务</div>
            <div class="meta-value">
              <template v-if="plan.is_cron_enabled">
                <v-icon size="10" color="success" class="mr-1">mdi-circle</v-icon>
                {{ plan.cron_expression }}
              </template>
              <span v-else class="text-medium-emphasis">未启用</span>
            </div>
          </div>
        </div>
        <div class="meta-divider" />
        <div class="meta-item">
          <v-avatar size="40" color="deep-purple" variant="tonal" rounded="lg" class="meta-icon">
            <v-icon size="22" color="deep-purple">mdi-format-list-numbered</v-icon>
          </v-avatar>
          <div class="meta-text">
            <div class="meta-label">构建步骤</div>
            <div class="meta-value">{{ (plan.steps || []).length }} 步</div>
          </div>
        </div>
        <div class="meta-divider" />
        <div class="meta-item">
          <v-avatar size="40" color="cyan" variant="tonal" rounded="lg" class="meta-icon">
            <v-icon size="22" color="cyan-darken-2">mdi-history</v-icon>
          </v-avatar>
          <div class="meta-text">
            <div class="meta-label">最近构建</div>
            <div class="meta-value">
              <template v-if="latestExec">
                <v-chip :color="getExecStatusColor(latestExec.status)" size="x-small" variant="flat" class="mr-1">
                  {{ latestExec.status.toUpperCase() }}
                </v-chip>
                {{ formatDate(latestExec.started_at) }}
              </template>
              <span v-else class="text-medium-emphasis">暂无</span>
            </div>
          </div>
        </div>
      </div>
    </v-sheet>

    <!-- Extended Info (Git / Report) -->
    <v-sheet v-if="plan.git_repo_url || plan.report_enabled || hasEnvVars" class="rounded-xl mb-5 pa-5" color="surface" elevation="0" style="border: 1px solid rgba(0,0,0,0.06);">
      <v-row dense>
        <v-col v-if="plan.git_repo_url" cols="12" md="6">
          <div class="ext-section">
            <div class="ext-title">
              <v-icon size="16" color="teal" class="mr-2">mdi-source-branch</v-icon>
              代码仓库
            </div>
            <div class="ext-row">
              <span class="ext-key">仓库地址</span>
              <code class="ext-val">{{ plan.git_repo_url }}</code>
            </div>
            <div class="ext-row">
              <span class="ext-key">分支</span>
              <v-chip size="x-small" color="info" variant="flat">{{ plan.git_branch || 'main' }}</v-chip>
            </div>
            <div v-if="plan.git_credential_id" class="ext-row">
              <span class="ext-key">凭证 ID</span>
              <code class="ext-val">{{ plan.git_credential_id }}</code>
            </div>
          </div>
        </v-col>
        <v-col v-if="plan.report_enabled" cols="12" :md="plan.git_repo_url ? 6 : 12">
          <div class="ext-section">
            <div class="ext-title">
              <v-icon size="16" color="teal" class="mr-2">mdi-file-chart-outline</v-icon>
              报告配置
            </div>
            <div class="ext-row">
              <span class="ext-key">报告</span>
              <v-chip size="x-small" color="success" variant="flat">已启用</v-chip>
            </div>
            <div v-if="plan.report_command" class="ext-row">
              <span class="ext-key">命令</span>
              <code class="ext-val">{{ plan.report_command }}</code>
            </div>
          </div>
        </v-col>
        <v-col v-if="hasEnvVars" cols="12">
          <div class="ext-section">
            <div class="ext-title">
              <v-icon size="16" color="teal" class="mr-2">mdi-variable</v-icon>
              环境变量
            </div>
            <div class="env-chips">
              <v-chip v-for="ev in plan.environment_variables" :key="ev.key" size="small" variant="outlined" color="teal" class="mr-2 mb-1">
                <span class="font-weight-bold">{{ ev.key }}</span>
                <span class="text-medium-emphasis mx-1">=</span>
                <span>{{ ev.value }}</span>
              </v-chip>
            </div>
          </div>
        </v-col>
      </v-row>
    </v-sheet>

    <!-- Executions -->
    <v-sheet class="rounded-xl" elevation="0" style="border: 1px solid rgba(0,0,0,0.06);">
      <div class="d-flex align-center px-5 pt-4 pb-2">
        <v-icon size="20" color="teal" class="mr-2">mdi-history</v-icon>
        <span class="text-subtitle-1 font-weight-bold">执行记录</span>
        <v-spacer />
        <v-chip size="x-small" variant="tonal" color="default">{{ executions.length }} 条</v-chip>
      </div>
      <v-data-table
        :headers="execHeaders" :items="executions" :loading="loadingExec" hover
        @click:row="(_e: any, { item }: any) => showExecDetail(item)"
        class="exec-table"
      >
        <template v-slot:item.status="{ item }">
          <v-chip :color="getExecStatusColor(item.status)" size="small" variant="flat" class="font-weight-bold">
            {{ $t(`testing.executions.status.${item.status}`) }}
          </v-chip>
        </template>
        <template v-slot:item.trigger_type="{ item }">
          <v-chip size="small" variant="tonal" color="default">
            {{ $t(`testing.executions.triggerType.${item.trigger_type}`) }}
          </v-chip>
        </template>
        <template v-slot:item.started_at="{ item }">
          {{ formatDate(item.started_at) }}
        </template>
        <template v-slot:item.actions="{ item }">
          <div class="d-flex" @click.stop>
            <v-tooltip text="查看日志" location="top">
              <template v-slot:activator="{ props }">
                <v-btn v-bind="props" icon="mdi-text-long" size="small" variant="text" color="info" @click="showLogs(item)" />
              </template>
            </v-tooltip>
            <v-tooltip text="查看报告" location="top">
              <template v-slot:activator="{ props }">
                <v-btn v-bind="props" icon="mdi-file-chart-outline" size="small" variant="text" color="primary" @click="showReport(item)" />
              </template>
            </v-tooltip>
            <v-tooltip v-if="item.status === 'running' || item.status === 'pending'" text="取消执行" location="top">
              <template v-slot:activator="{ props }">
                <v-btn v-bind="props" icon="mdi-stop-circle-outline" size="small" variant="text" color="error" @click="confirmCancelExec(item)" />
              </template>
            </v-tooltip>
          </div>
        </template>
        <template v-slot:no-data>
          <div class="text-center py-12 text-medium-emphasis">
            <v-icon size="48" color="grey-lighten-1" class="mb-3">mdi-clock-fast</v-icon>
            <div class="text-body-2">暂无执行记录</div>
            <v-btn color="teal" variant="tonal" class="text-none mt-3" size="small" prepend-icon="mdi-play-circle-outline" @click="confirmTriggerDialog = true">
              启动首次构建
            </v-btn>
          </div>
        </template>
      </v-data-table>
    </v-sheet>

    <!-- Trigger Confirm Dialog -->
    <v-dialog v-model="confirmTriggerDialog" max-width="400">
      <v-card class="rounded-xl">
        <v-card-title class="bg-teal text-white pa-4 d-flex align-center">
          <v-icon class="mr-2">mdi-play-circle-outline</v-icon>
          <span class="text-subtitle-1 font-weight-bold">{{ $t('testing.plans.trigger') }}</span>
        </v-card-title>
        <v-card-text class="pa-4">{{ $t('testing.plans.triggerConfirm') }}</v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="confirmTriggerDialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="teal" variant="flat" @click="triggerBuild">{{ $t('common.confirm') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Cancel Exec Confirm Dialog -->
    <v-dialog v-model="confirmCancelDialog" max-width="400">
      <v-card class="rounded-xl">
        <v-card-title class="bg-error text-white pa-4">
          <span class="text-subtitle-1 font-weight-bold">{{ $t('testing.executions.cancel') }}</span>
        </v-card-title>
        <v-card-text class="pa-4">{{ $t('testing.executions.cancelConfirm') }}</v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="confirmCancelDialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="error" variant="flat" @click="doCancelExec">{{ $t('common.confirm') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Log Dialog -->
    <v-dialog v-model="logDialog" max-width="900" scrollable>
      <v-card class="rounded-xl">
        <v-card-title class="pa-4 bg-grey-darken-3 text-white d-flex align-center justify-space-between">
          <span class="text-subtitle-1 font-weight-bold">
            <v-icon start>mdi-console</v-icon>{{ $t('testing.executions.logs') }} #{{ selectedExec?.id }}
            <v-chip v-if="isLogStreaming" size="x-small" color="green" class="ml-2" variant="flat">LIVE</v-chip>
          </span>
          <div>
            <v-btn icon="mdi-download" variant="text" color="white" size="small" @click="downloadLog" class="mr-1" />
            <v-btn icon="mdi-refresh" variant="text" color="white" size="small" @click="refreshLog" class="mr-1" />
            <v-btn icon="mdi-close" variant="text" color="white" size="small" @click="closeLogDialog" />
          </div>
        </v-card-title>
        <v-card-text class="pa-0" style="max-height: 60vh;">
          <pre ref="logViewerRef" class="log-viewer pa-4">{{ logContent || $t('testing.executions.noLogs') }}</pre>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Report Dialog -->
    <v-dialog v-model="reportDialog" max-width="1000" scrollable>
      <v-card class="rounded-xl">
        <v-card-title class="pa-4 bg-primary text-white d-flex align-center justify-space-between">
          <span class="text-subtitle-1 font-weight-bold">
            <v-icon start>mdi-file-chart-outline</v-icon>{{ $t('testing.executions.report') }}
          </span>
          <v-btn icon="mdi-close" variant="text" color="white" size="small" @click="reportDialog = false" />
        </v-card-title>
        <v-card-text class="pa-4" style="max-height: 70vh;">
          <div v-if="reportData.report_type === 'allure' && reportData.report_url">
            <iframe :src="reportData.report_url" style="width: 100%; height: 60vh; border: none; border-radius: 8px;" />
          </div>
          <div v-else-if="reportData.report_type === 'junit' && reportData.report_data">
            <v-row class="mb-4">
              <v-col cols="3">
                <v-card color="blue" variant="tonal"><v-card-text class="text-center"><div class="text-h5">{{ reportData.report_data.tests || 0 }}</div><div class="text-caption">Total</div></v-card-text></v-card>
              </v-col>
              <v-col cols="3">
                <v-card color="green" variant="tonal"><v-card-text class="text-center"><div class="text-h5">{{ (reportData.report_data.tests || 0) - (reportData.report_data.failures || 0) - (reportData.report_data.errors || 0) }}</div><div class="text-caption">Passed</div></v-card-text></v-card>
              </v-col>
              <v-col cols="3">
                <v-card color="red" variant="tonal"><v-card-text class="text-center"><div class="text-h5">{{ reportData.report_data.failures || 0 }}</div><div class="text-caption">Failures</div></v-card-text></v-card>
              </v-col>
              <v-col cols="3">
                <v-card color="orange" variant="tonal"><v-card-text class="text-center"><div class="text-h5">{{ reportData.report_data.errors || 0 }}</div><div class="text-caption">Errors</div></v-card-text></v-card>
              </v-col>
            </v-row>
            <v-data-table v-if="reportData.report_data.suites" :headers="junitHeaders" :items="flattenSuites(reportData.report_data)" density="compact">
              <template v-slot:item.status="{ item }">
                <v-icon :color="item.status === 'passed' ? 'green' : 'red'" size="small">
                  {{ item.status === 'passed' ? 'mdi-check-circle' : 'mdi-alert-circle' }}
                </v-icon>
              </template>
            </v-data-table>
          </div>
          <v-empty-state v-else icon="mdi-file-chart-off-outline" :title="$t('testing.executions.noReport')" class="py-10" />
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { useSnackbarStore } from '@/store/snackbar'
import {
  getBuildPlan, triggerBuildPlan, getBuildPlanExecutions,
  getBuildExecutionLogs, downloadBuildExecutionLog,
  getBuildExecutionReport, cancelBuildExecution,
  refreshBuildPlanStatus, getProgressiveLog,
} from '@/api/testing'

const { t } = useI18n()
const route = useRoute()
const snackbar = useSnackbarStore()

const plan = ref<any>({})
const executions = ref<any[]>([])
const loading = ref(false)
const loadingExec = ref(false)
const triggering = ref(false)
const refreshing = ref(false)

const confirmTriggerDialog = ref(false)
const confirmCancelDialog = ref(false)
const cancelTarget = ref<any>(null)

const logDialog = ref(false)
const logContent = ref('')
const selectedExec = ref<any>(null)
const logViewerRef = ref<HTMLElement | null>(null)
const isLogStreaming = ref(false)
let logPollTimer: ReturnType<typeof setInterval> | null = null
let logStart = 0

const reportDialog = ref(false)
const reportData = ref<any>({})

const planId = computed(() => Number(route.params.id))

const latestExec = computed(() => executions.value.length ? executions.value[0] : null)

const hasEnvVars = computed(() => {
  const ev = plan.value.environment_variables
  return Array.isArray(ev) && ev.length > 0
})

const execHeaders = computed(() => [
  { title: '#', key: 'id', width: 60 },
  { title: '状态', key: 'status', width: 100 },
  { title: '触发方式', key: 'trigger_type', width: 120 },
  { title: '触发人', key: 'triggered_by' },
  { title: 'Jenkins #', key: 'jenkins_build_number', width: 100 },
  { title: '耗时', key: 'duration_display', width: 100 },
  { title: '开始时间', key: 'started_at' },
  { title: '操作', key: 'actions', sortable: false, width: 130 },
])

const junitHeaders = [
  { title: 'Status', key: 'status', width: 60 },
  { title: 'Suite', key: 'suite' },
  { title: 'Test', key: 'name' },
  { title: 'Time', key: 'time', width: 80 },
]

const getExecStatusColor = (s: string) =>
  ({ pending: 'grey', running: 'info', success: 'success', failed: 'error', cancelled: 'warning' }[s] || 'grey')

const formatDate = (d: string) => {
  if (!d) return '-'
  return new Date(d).toLocaleString()
}

const loadPlan = async () => {
  loading.value = true
  try {
    plan.value = await getBuildPlan(planId.value)
  } catch (e) { console.error(e) }
  loading.value = false
}

const loadExecutions = async () => {
  loadingExec.value = true
  try {
    const res = await getBuildPlanExecutions(planId.value, { no_page: true })
    executions.value = Array.isArray(res) ? res : []
  } catch (e) { console.error(e) }
  loadingExec.value = false
}

const refreshStatus = async () => {
  refreshing.value = true
  try {
    await refreshBuildPlanStatus(planId.value)
    await loadPlan()
    await loadExecutions()
    snackbar.notify(t('common.success'), 'success')
  } catch (e: any) { snackbar.notify(e?.message || t('common.error'), 'error') }
  refreshing.value = false
}

const triggerBuild = async () => {
  confirmTriggerDialog.value = false
  triggering.value = true
  try {
    await triggerBuildPlan(planId.value)
    snackbar.notify(t('common.success'), 'success')
    loadExecutions()
  } catch (e: any) { snackbar.notify(e?.message || t('common.error'), 'error') }
  triggering.value = false
}

const showExecDetail = (item: any) => { showLogs(item) }

const showLogs = async (item: any) => {
  selectedExec.value = item
  logContent.value = 'Loading...'
  logStart = 0
  logDialog.value = true
  isLogStreaming.value = item.status === 'running' || item.status === 'pending'

  try {
    if (isLogStreaming.value) {
      await fetchProgressiveLog()
      startLogPolling()
    } else {
      const res = await getBuildExecutionLogs(item.id) as any
      logContent.value = res.log_text || t('testing.executions.noLogs')
    }
  } catch (e) { logContent.value = 'Error loading logs' }
}

const fetchProgressiveLog = async () => {
  if (!selectedExec.value) return
  try {
    const res = await getProgressiveLog(selectedExec.value.id, logStart) as any
    if (res.text) {
      if (logStart === 0) { logContent.value = res.text }
      else { logContent.value += res.text }
      logStart = res.offset || logContent.value.length
      await nextTick()
      if (logViewerRef.value) { logViewerRef.value.scrollTop = logViewerRef.value.scrollHeight }
    }
    if (!res.more) {
      isLogStreaming.value = false
      stopLogPolling()
    }
  } catch (e) { /* ignore polling errors */ }
}

const startLogPolling = () => {
  stopLogPolling()
  logPollTimer = setInterval(fetchProgressiveLog, 2000)
}

const stopLogPolling = () => {
  if (logPollTimer) { clearInterval(logPollTimer); logPollTimer = null }
}

const closeLogDialog = () => {
  logDialog.value = false
  stopLogPolling()
}

const refreshLog = async () => {
  if (!selectedExec.value) return
  logStart = 0
  try {
    if (isLogStreaming.value) { await fetchProgressiveLog() }
    else {
      const res = await getBuildExecutionLogs(selectedExec.value.id) as any
      logContent.value = res.log_text || t('testing.executions.noLogs')
    }
  } catch (e) { /* ignore */ }
}

const downloadLog = async () => {
  if (!selectedExec.value) return
  try {
    const res = await downloadBuildExecutionLog(selectedExec.value.id) as BlobPart
    const url = window.URL.createObjectURL(new Blob([res]))
    const a = document.createElement('a')
    a.href = url
    a.download = `build_${selectedExec.value.id}_log.txt`
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (e: any) { snackbar.notify('Download failed', 'error') }
}

const showReport = async (item: any) => {
  reportData.value = {}
  reportDialog.value = true
  try {
    reportData.value = await getBuildExecutionReport(item.id)
  } catch (e) { reportData.value = {} }
}

const confirmCancelExec = (item: any) => {
  cancelTarget.value = item
  confirmCancelDialog.value = true
}

const doCancelExec = async () => {
  confirmCancelDialog.value = false
  if (!cancelTarget.value) return
  try {
    await cancelBuildExecution(cancelTarget.value.id)
    snackbar.notify(t('common.success'), 'success')
    loadExecutions()
  } catch (e: any) { snackbar.notify(e?.message || t('common.error'), 'error') }
}

const flattenSuites = (data: any) => {
  const results: any[] = []
  for (const suite of (data.suites || [])) {
    for (const tc of (suite.cases || [])) {
      results.push({
        suite: suite.name,
        name: tc.name || tc.className,
        status: tc.status === 'PASSED' || !tc.errorDetails ? 'passed' : 'failed',
        time: tc.duration ? `${tc.duration.toFixed(2)}s` : '-',
      })
    }
  }
  return results
}

let pollTimer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  loadPlan()
  loadExecutions()
  pollTimer = setInterval(loadExecutions, 10000)
})

onBeforeUnmount(() => {
  if (pollTimer) clearInterval(pollTimer)
  stopLogPolling()
})
</script>

<style scoped>
.detail-root {
  max-width: 1600px;
}

.detail-topbar {
  padding: 18px 24px;
  background: linear-gradient(135deg, #f8fffe 0%, #f0faf8 100%);
  border: 1px solid rgba(0, 128, 128, 0.08);
  border-radius: 16px;
}

/* Metadata bar */
.detail-meta {
  border: 1px solid rgba(0, 0, 0, 0.06);
  background: #fff;
}

.meta-grid {
  display: flex;
  align-items: stretch;
  padding: 0;
}

.meta-item {
  flex: 1;
  padding: 20px 24px;
  display: flex;
  align-items: center;
  gap: 14px;
}

.meta-icon {
  flex-shrink: 0;
}

.meta-text {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
}

.meta-label {
  font-size: 12px;
  color: #999;
  font-weight: 500;
  margin-bottom: 4px;
  letter-spacing: 0.3px;
  line-height: 1;
}

.meta-value {
  font-size: 14px;
  font-weight: 700;
  color: #222;
  display: flex;
  align-items: center;
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.meta-divider {
  width: 1px;
  background: rgba(0, 0, 0, 0.06);
  align-self: stretch;
  margin: 14px 0;
}

/* Extended info */
.ext-section {
  margin-bottom: 4px;
}

.ext-title {
  font-size: 14px;
  font-weight: 700;
  color: #444;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
}

.ext-row {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-size: 13px;
}

.ext-key {
  min-width: 80px;
  color: #999;
  font-weight: 500;
  flex-shrink: 0;
}

.ext-val {
  font-family: 'Menlo', 'Consolas', monospace;
  font-size: 12px;
  background: rgba(0, 128, 128, 0.05);
  padding: 3px 10px;
  border-radius: 4px;
  color: #333;
  word-break: break-all;
}

.env-chips {
  margin-top: 4px;
}

/* Executions table */
.exec-table :deep(.v-data-table__tr) {
  cursor: pointer;
}

/* Log viewer */
.log-viewer {
  background-color: #1e1e1e;
  color: #d4d4d4;
  font-family: 'Fira Code', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
  min-height: 300px;
  margin: 0;
}

@media (max-width: 960px) {
  .meta-grid {
    flex-wrap: wrap;
  }
  .meta-item {
    flex: 0 0 50%;
  }
  .meta-divider {
    display: none;
  }
}
</style>

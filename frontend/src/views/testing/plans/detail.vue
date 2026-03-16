<template>
  <v-container fluid>
    <!-- Header -->
    <v-sheet class="pa-4 rounded-xl border-thin mb-4" elevation="0" color="surface">
      <v-row align="center">
        <v-col cols="auto">
          <v-btn icon="mdi-arrow-left" variant="text" @click="$router.back()" />
        </v-col>
        <v-col>
          <div class="text-h6 font-weight-bold">{{ plan.name }}</div>
          <div class="text-body-2 text-grey">{{ plan.description || '-' }}</div>
        </v-col>
        <v-col cols="auto">
          <v-chip :color="plan.status === 'active' ? 'success' : 'grey'" class="mr-2">
            {{ plan.status === 'active' ? $t('testing.plans.status.active') : $t('testing.plans.status.disabled') }}
          </v-chip>
          <v-btn color="success" prepend-icon="mdi-play" @click="triggerBuild" :loading="triggering" class="text-none" rounded="lg" variant="flat">
            {{ $t('testing.plans.trigger') }}
          </v-btn>
        </v-col>
      </v-row>
    </v-sheet>

    <!-- Info Cards -->
    <v-row class="mb-4">
      <v-col cols="12" md="3">
        <v-card variant="tonal" color="primary" class="rounded-xl">
          <v-card-text class="text-center">
            <v-icon size="32" class="mb-1">mdi-server</v-icon>
            <div class="text-body-2">{{ $t('testing.plans.fields.executorMachine') }}</div>
            <div class="text-subtitle-1 font-weight-bold">{{ plan.executor_machine_name || 'Jenkins Master' }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card variant="tonal" color="info" class="rounded-xl">
          <v-card-text class="text-center">
            <v-icon size="32" class="mb-1">mdi-jenkins</v-icon>
            <div class="text-body-2">Jenkins Job</div>
            <div class="text-subtitle-1 font-weight-bold">{{ plan.jenkins_job_name || '-' }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card variant="tonal" :color="plan.is_cron_enabled ? 'warning' : 'grey'" class="rounded-xl">
          <v-card-text class="text-center">
            <v-icon size="32" class="mb-1">mdi-clock-outline</v-icon>
            <div class="text-body-2">Cron</div>
            <div class="text-subtitle-1 font-weight-bold">{{ plan.is_cron_enabled ? plan.cron_expression : 'Disabled' }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card variant="tonal" color="secondary" class="rounded-xl">
          <v-card-text class="text-center">
            <v-icon size="32" class="mb-1">mdi-format-list-numbered</v-icon>
            <div class="text-body-2">{{ $t('testing.steps.title') }}</div>
            <div class="text-subtitle-1 font-weight-bold">{{ (plan.steps || []).length }}</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Tabs -->
    <v-card class="rounded-xl" elevation="1">
      <v-tabs v-model="activeTab" color="primary" class="border-b">
        <v-tab value="steps"><v-icon start>mdi-format-list-numbered</v-icon>{{ $t('testing.steps.title') }}</v-tab>
        <v-tab value="executions"><v-icon start>mdi-history</v-icon>{{ $t('testing.executions.title') }}</v-tab>
      </v-tabs>

      <v-window v-model="activeTab">
        <!-- Steps Tab -->
        <v-window-item value="steps">
          <v-card-text>
            <v-timeline v-if="plan.steps && plan.steps.length" density="compact" side="end">
              <v-timeline-item v-for="(step, idx) in plan.steps" :key="idx" :dot-color="'primary'" size="small">
                <v-card variant="outlined" class="rounded-lg">
                  <v-card-title class="text-subtitle-2 pa-3">
                    <v-chip size="x-small" color="primary" class="mr-2">{{ idx + 1 }}</v-chip>
                    {{ step.name }}
                    <v-spacer />
                    <v-chip size="x-small" variant="outlined" class="mr-1">{{ step.timeout }}s</v-chip>
                    <v-chip size="x-small" variant="outlined">{{ step.on_failure }}</v-chip>
                  </v-card-title>
                  <v-card-text v-if="step.script" class="pa-3 pt-0">
                    <pre class="code-block">{{ step.script }}</pre>
                  </v-card-text>
                </v-card>
              </v-timeline-item>
            </v-timeline>
            <v-empty-state v-else icon="mdi-playlist-remove" title="No steps defined" class="py-10" />
          </v-card-text>
        </v-window-item>

        <!-- Executions Tab -->
        <v-window-item value="executions">
          <v-card-text>
            <v-data-table :headers="execHeaders" :items="executions" :loading="loadingExec" hover @click:row="(_e: any, { item }: any) => showExecDetail(item)">
              <template v-slot:item.status="{ item }">
                <v-chip :color="getExecStatusColor(item.status)" size="small" variant="flat">
                  {{ $t(`testing.executions.status.${item.status}`) }}
                </v-chip>
              </template>
              <template v-slot:item.trigger_type="{ item }">
                <v-chip size="small" variant="outlined">
                  {{ $t(`testing.executions.triggerType.${item.trigger_type}`) }}
                </v-chip>
              </template>
              <template v-slot:item.started_at="{ item }">
                {{ formatDate(item.started_at) }}
              </template>
              <template v-slot:item.actions="{ item }">
                <div class="d-flex" @click.stop>
                  <v-btn icon="mdi-text-long" size="small" variant="text" color="info" @click="showLogs(item)" />
                  <v-btn icon="mdi-file-chart-outline" size="small" variant="text" color="primary" @click="showReport(item)" />
                  <v-btn v-if="item.status === 'running' || item.status === 'pending'" icon="mdi-stop-circle-outline" size="small" variant="text" color="error" @click="cancelExec(item)" />
                </div>
              </template>
              <template v-slot:no-data>
                <v-empty-state icon="mdi-history" :title="$t('common.noData')" class="py-10" />
              </template>
            </v-data-table>
          </v-card-text>
        </v-window-item>
      </v-window>
    </v-card>

    <!-- Log Dialog -->
    <v-dialog v-model="logDialog" max-width="900" scrollable>
      <v-card class="rounded-xl">
        <v-card-title class="pa-4 bg-grey-darken-3 text-white d-flex align-center justify-space-between">
          <span class="text-subtitle-1 font-weight-bold">
            <v-icon start>mdi-console</v-icon>{{ $t('testing.executions.logs') }} #{{ selectedExec?.id }}
          </span>
          <div>
            <v-btn icon="mdi-download" variant="text" color="white" size="small" @click="downloadLog" class="mr-1" />
            <v-btn icon="mdi-refresh" variant="text" color="white" size="small" @click="refreshLog" class="mr-1" />
            <v-btn icon="mdi-close" variant="text" color="white" size="small" @click="logDialog = false" />
          </div>
        </v-card-title>
        <v-card-text class="pa-0" style="max-height: 60vh;">
          <pre class="log-viewer pa-4">{{ logContent || $t('testing.executions.noLogs') }}</pre>
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
          <!-- Allure iframe -->
          <div v-if="reportData.report_type === 'allure' && reportData.report_url">
            <iframe :src="reportData.report_url" style="width: 100%; height: 60vh; border: none; border-radius: 8px;" />
          </div>
          <!-- JUnit data -->
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
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { useSnackbarStore } from '@/store/snackbar'
import {
  getBuildPlan, triggerBuildPlan, getBuildPlanExecutions,
  getBuildExecutionLogs, downloadBuildExecutionLog,
  getBuildExecutionReport, cancelBuildExecution,
} from '@/api/testing'

const { t } = useI18n()
const route = useRoute()
const snackbar = useSnackbarStore()

const plan = ref<any>({})
const executions = ref<any[]>([])
const loading = ref(false)
const loadingExec = ref(false)
const triggering = ref(false)
const activeTab = ref('steps')

// Log dialog
const logDialog = ref(false)
const logContent = ref('')
const selectedExec = ref<any>(null)

// Report dialog
const reportDialog = ref(false)
const reportData = ref<any>({})

const planId = computed(() => Number(route.params.id))

const execHeaders = computed(() => [
  { title: '#', key: 'id', width: 60 },
  { title: t('testing.executions.status.pending').replace('...', ''), key: 'status', width: 100 },
  { title: 'Trigger', key: 'trigger_type', width: 120 },
  { title: 'Triggered By', key: 'triggered_by' },
  { title: 'Jenkins #', key: 'jenkins_build_number', width: 100 },
  { title: 'Duration', key: 'duration_display', width: 100 },
  { title: 'Started', key: 'started_at' },
  { title: t('common.actions'), key: 'actions', sortable: false, width: 130 },
])

// Rename header for status column
execHeaders.value[1].title = 'Status'

const junitHeaders = [
  { title: 'Status', key: 'status', width: 60 },
  { title: 'Suite', key: 'suite' },
  { title: 'Test', key: 'name' },
  { title: 'Time', key: 'time', width: 80 },
]

const getExecStatusColor = (s: string) => ({ pending: 'grey', running: 'info', success: 'success', failed: 'error', cancelled: 'warning' }[s] || 'grey')

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
    const res = await getBuildPlanExecutions(planId.value)
    executions.value = res.results || res || []
  } catch (e) { console.error(e) }
  loadingExec.value = false
}

const triggerBuild = async () => {
  if (!confirm(t('testing.plans.triggerConfirm'))) return
  triggering.value = true
  try {
    await triggerBuildPlan(planId.value)
    snackbar.notify(t('common.success'), 'success')
    loadExecutions()
  } catch (e: any) { snackbar.notify(e?.message || t('common.error'), 'error') }
  triggering.value = false
}

const showExecDetail = (item: any) => {
  showLogs(item)
}

const showLogs = async (item: any) => {
  selectedExec.value = item
  logContent.value = 'Loading...'
  logDialog.value = true
  try {
    const res = await getBuildExecutionLogs(item.id)
    logContent.value = res.log_text || t('testing.executions.noLogs')
  } catch (e) { logContent.value = 'Error loading logs' }
}

const refreshLog = async () => {
  if (!selectedExec.value) return
  try {
    const res = await getBuildExecutionLogs(selectedExec.value.id)
    logContent.value = res.log_text || t('testing.executions.noLogs')
  } catch (e) { /* ignore */ }
}

const downloadLog = async () => {
  if (!selectedExec.value) return
  try {
    const res = await downloadBuildExecutionLog(selectedExec.value.id)
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

const cancelExec = async (item: any) => {
  if (!confirm(t('testing.executions.cancelConfirm'))) return
  try {
    await cancelBuildExecution(item.id)
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

// Auto-refresh executions when tab is active
let pollTimer: ReturnType<typeof setInterval> | null = null
watch(activeTab, (val) => {
  if (val === 'executions') {
    loadExecutions()
    pollTimer = setInterval(loadExecutions, 10000)
  } else if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
})

onMounted(() => {
  loadPlan()
  loadExecutions()
})
</script>

<style scoped>
.code-block {
  background-color: rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 6px;
  padding: 10px;
  font-family: 'Fira Code', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  overflow-x: auto;
}
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
</style>

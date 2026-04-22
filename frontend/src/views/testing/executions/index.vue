<template>
  <v-container fluid>
    <!-- 筛选栏 -->
    <v-sheet class="pa-4 rounded-xl border-thin" elevation="0" color="surface">
      <v-row dense align="center">
        <v-col cols="6" md="2">
          <v-select
            v-model="filters.project"
            :items="projects"
            item-title="name"
            item-value="id"
            :label="$t('executionRecords.filters.project')"
            density="compact"
            variant="outlined"
            hide-details
            clearable
            bg-color="background"
            class="rounded-lg"
            prepend-inner-icon="mdi-folder-outline"
          />
        </v-col>
        <v-col cols="6" md="2">
          <v-select
            v-model="filters.interface"
            :items="interfaces"
            item-title="name"
            item-value="id"
            :label="$t('executionRecords.filters.interface')"
            density="compact"
            variant="outlined"
            hide-details
            clearable
            bg-color="background"
            class="rounded-lg"
            prepend-inner-icon="mdi-api"
          />
        </v-col>
        <v-col cols="6" md="2">
          <v-select
            v-model="filters.status"
            :items="statusItems"
            item-title="title"
            item-value="value"
            :label="$t('executionRecords.filters.status')"
            density="compact"
            variant="outlined"
            hide-details
            clearable
            bg-color="background"
            class="rounded-lg"
            prepend-inner-icon="mdi-flag-outline"
          />
        </v-col>
        <v-col cols="6" md="2">
          <v-text-field
            v-model="filters.startDate"
            :label="$t('executionRecords.filters.startDate')"
            type="date"
            density="compact"
            variant="outlined"
            hide-details
            clearable
            bg-color="background"
            class="rounded-lg"
          />
        </v-col>
        <v-col cols="6" md="2">
          <v-text-field
            v-model="filters.endDate"
            :label="$t('executionRecords.filters.endDate')"
            type="date"
            density="compact"
            variant="outlined"
            hide-details
            clearable
            bg-color="background"
            class="rounded-lg"
          />
        </v-col>
        <v-col cols="6" md="2">
          <v-text-field
            v-model="search"
            :label="$t('common.search')"
            prepend-inner-icon="mdi-magnify"
            density="compact"
            variant="outlined"
            hide-details
            clearable
            bg-color="background"
            class="rounded-lg"
          />
        </v-col>
      </v-row>
    </v-sheet>

    <!-- 统计卡片 -->
    <v-row class="mt-2" dense>
      <v-col cols="6" sm="4" md>
        <v-card variant="tonal" color="blue" class="rounded-xl">
          <v-card-text class="text-center py-3">
            <div class="text-h5 font-weight-bold">{{ stats.total }}</div>
            <div class="text-caption mt-1">{{ $t('executionRecords.stats.total') }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6" sm="4" md>
        <v-card variant="tonal" color="success" class="rounded-xl">
          <v-card-text class="text-center py-3">
            <div class="text-h5 font-weight-bold">{{ stats.passed }}</div>
            <div class="text-caption mt-1">{{ $t('executionRecords.stats.passed') }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6" sm="4" md>
        <v-card variant="tonal" color="error" class="rounded-xl">
          <v-card-text class="text-center py-3">
            <div class="text-h5 font-weight-bold">{{ stats.failed }}</div>
            <div class="text-caption mt-1">{{ $t('executionRecords.stats.failed') }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6" sm="4" md>
        <v-card variant="tonal" color="warning" class="rounded-xl">
          <v-card-text class="text-center py-3">
            <div class="text-h5 font-weight-bold">{{ stats.error }}</div>
            <div class="text-caption mt-1">{{ $t('executionRecords.stats.error') }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6" sm="4" md>
        <v-card variant="tonal" color="info" class="rounded-xl">
          <v-card-text class="text-center py-3">
            <div class="text-h5 font-weight-bold">{{ stats.avg_response_time != null ? Math.round(stats.avg_response_time) : '-' }}<span class="text-caption">ms</span></div>
            <div class="text-caption mt-1">{{ $t('executionRecords.stats.avgTime') }}</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 执行记录表格 -->
    <v-card class="mt-3 rounded-xl" elevation="1">
      <v-data-table-server
        v-model:items-per-page="pageSize"
        :headers="tableHeaders"
        :items="records"
        :items-length="totalCount"
        :loading="loading"
        v-model:page="currentPage"
        fixed-header
        height="520"
        hover
        item-key="id"
        @update:options="onTableOptionsUpdate"
      >
        <template #item.test_case_name="{ item }">
          <span class="font-weight-medium">{{ item.test_case_name }}</span>
        </template>

        <template #item.test_case_interface="{ item }">
          <v-chip size="small" variant="outlined" color="primary" label>
            {{ item.test_case_interface }}
          </v-chip>
        </template>

        <template #item.project_name="{ item }">
          <v-chip v-if="item.project_name" size="small" label color="teal" variant="tonal">
            {{ item.project_name }}
          </v-chip>
          <span v-else class="text-grey text-caption">-</span>
        </template>

        <template #item.request_method="{ item }">
          <v-chip size="x-small" :color="methodColor(item.request_method)" variant="flat" label class="font-weight-bold">
            {{ item.request_method }}
          </v-chip>
        </template>

        <template #item.status="{ item }">
          <v-chip size="small" :color="statusColor(item.status)" variant="flat">
            {{ $t(`execution.status.${item.status}`, item.status) }}
          </v-chip>
        </template>

        <template #item.response_time_ms="{ item }">
          <span v-if="item.response_time_ms != null" :class="item.response_time_ms > 3000 ? 'text-error' : 'text-medium-emphasis'">
            {{ item.response_time_ms }}ms
          </span>
          <span v-else class="text-medium-emphasis">-</span>
        </template>

        <template #item.assertions="{ item }">
          <span class="text-success">{{ item.assertions_passed }}</span>
          <span class="text-medium-emphasis mx-1">/</span>
          <span :class="item.assertions_failed > 0 ? 'text-error' : 'text-medium-emphasis'">{{ item.assertions_failed }}</span>
        </template>

        <template #item.started_at="{ item }">
          <span class="text-caption">{{ formatTime(item.started_at) }}</span>
        </template>

        <template #item.actions="{ item }">
          <v-btn icon="mdi-eye-outline" variant="text" size="small" color="primary" @click="openDetail(item)" />
        </template>

        <template #no-data>
          <v-empty-state
            icon="mdi-clipboard-text-clock-outline"
            :title="$t('executionRecords.noRecords')"
            :text="$t('executionRecords.noRecordsHint')"
            class="py-10"
          />
        </template>
      </v-data-table-server>
    </v-card>

    <!-- 详情弹窗 -->
    <v-dialog v-model="detailDialog" max-width="960" scrollable>
      <v-card v-if="selectedRecord" class="rounded-xl">
        <v-toolbar color="primary" density="compact" class="px-2">
          <v-toolbar-title class="text-subtitle-1 font-weight-bold text-white">
            {{ selectedRecord.test_case_name }}
          </v-toolbar-title>
          <v-chip :color="statusColor(selectedRecord.status)" size="small" variant="flat" class="ml-2">
            {{ $t(`execution.status.${selectedRecord.status}`, selectedRecord.status) }}
          </v-chip>
          <v-spacer />
          <span class="text-caption text-white mr-3">{{ selectedRecord.response_time_ms }}ms</span>
          <v-btn icon="mdi-close" variant="text" color="white" size="small" @click="detailDialog = false" />
        </v-toolbar>

        <v-card-text class="pa-0" style="max-height: 70vh; overflow-y: auto;">
          <v-tabs v-model="detailTab" bg-color="transparent" class="border-b">
            <v-tab value="request">{{ $t('execution.tabs.request') }}</v-tab>
            <v-tab value="response">{{ $t('execution.tabs.response') }}</v-tab>
            <v-tab value="assertions">{{ $t('execution.tabs.assertions') }}</v-tab>
            <v-tab v-if="selectedRecord.error_message" value="error">{{ $t('execution.tabs.error') }}</v-tab>
          </v-tabs>

          <v-window v-model="detailTab" class="pa-5">
            <v-window-item value="request">
              <div class="d-flex align-center mb-3">
                <v-chip :color="methodColor(selectedRecord.request_method)" variant="flat" label size="small" class="font-weight-bold mr-2">
                  {{ selectedRecord.request_method }}
                </v-chip>
                <code class="text-body-2" style="word-break: break-all;">{{ selectedRecord.request_url }}</code>
              </div>
              <div class="text-subtitle-2 mb-1">{{ $t('execution.detail.requestHeaders') }}</div>
              <pre class="json-block">{{ formatJson(selectedRecord.request_headers) }}</pre>
              <div class="text-subtitle-2 mt-3 mb-1">{{ $t('execution.detail.requestBody') }}</div>
              <pre class="json-block">{{ formatJson(selectedRecord.request_body) }}</pre>
            </v-window-item>

            <v-window-item value="response">
              <v-row dense class="mb-3">
                <v-col cols="auto">
                  <div class="text-caption text-medium-emphasis">{{ $t('execution.detail.statusCode') }}</div>
                  <v-chip :color="selectedRecord.response_status >= 400 ? 'error' : 'success'" size="small" variant="flat">
                    {{ selectedRecord.response_status }}
                  </v-chip>
                </v-col>
                <v-col cols="auto">
                  <div class="text-caption text-medium-emphasis">{{ $t('execution.detail.responseTime') }}</div>
                  <span class="text-body-2 font-weight-medium">{{ selectedRecord.response_time_ms }}ms</span>
                </v-col>
              </v-row>
              <div class="text-subtitle-2 mb-1">{{ $t('execution.detail.responseHeaders') }}</div>
              <pre class="json-block">{{ formatJson(selectedRecord.response_headers) }}</pre>
              <div class="text-subtitle-2 mt-3 mb-1">{{ $t('execution.detail.responseBody') }}</div>
              <pre class="json-block">{{ formatJson(selectedRecord.response_body) }}</pre>
            </v-window-item>

            <v-window-item value="assertions">
              <v-list v-if="selectedRecord.assertion_details?.length" lines="two">
                <v-list-item
                  v-for="(a, idx) in selectedRecord.assertion_details"
                  :key="idx"
                  :prepend-icon="a.passed ? 'mdi-check-circle' : 'mdi-alert-circle'"
                  :base-color="a.passed ? 'success' : 'error'"
                >
                  <v-list-item-title>{{ a.message }}</v-list-item-title>
                  <v-list-item-subtitle v-if="a.description">{{ a.description }}</v-list-item-subtitle>
                </v-list-item>
              </v-list>
              <v-empty-state v-else icon="mdi-check-all" title="No assertions" class="py-6" />
            </v-window-item>

            <v-window-item v-if="selectedRecord.error_message" value="error">
              <v-alert type="error" prominent class="mb-3">{{ selectedRecord.error_message }}</v-alert>
              <pre v-if="selectedRecord.error_traceback" class="json-block">{{ selectedRecord.error_traceback }}</pre>
            </v-window-item>
          </v-window>
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { getExecutionList, getExecutionStats } from '@/api/execution'
import { getInterfaces } from '@/api/interface'
import { getDirectories } from '@/api/directory'
import { paginatedRequest } from '@/utils/axios'

const { t } = useI18n()
const route = useRoute()

const loading = ref(false)
const records = ref<any[]>([])
const totalCount = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const search = ref('')
const detailDialog = ref(false)
const detailTab = ref('request')
const selectedRecord = ref<any>(null)
const projects = ref<any[]>([])
const interfaces = ref<any[]>([])

const filters = ref({
  project: null as number | null,
  interface: null as number | null,
  status: null as string | null,
  startDate: null as string | null,
  endDate: null as string | null,
})

const stats = ref({
  total: 0,
  passed: 0,
  failed: 0,
  error: 0,
  avg_response_time: null as number | null,
})

const statusItems = computed(() => [
  { value: 'passed', title: t('execution.status.passed') },
  { value: 'failed', title: t('execution.status.failed') },
  { value: 'error', title: t('execution.status.error') },
  { value: 'pending', title: t('execution.status.pending') },
  { value: 'running', title: t('execution.status.running') },
])

const tableHeaders = computed(() => [
  { title: t('executionRecords.headers.caseName'), key: 'test_case_name', minWidth: '200px' },
  { title: t('executionRecords.headers.interface'), key: 'test_case_interface' },
  { title: t('executionRecords.headers.project'), key: 'project_name' },
  { title: t('executionRecords.headers.method'), key: 'request_method', width: '80px' },
  { title: t('executionRecords.headers.status'), key: 'status', width: '100px' },
  { title: t('executionRecords.headers.responseTime'), key: 'response_time_ms', width: '100px' },
  { title: t('executionRecords.headers.assertions'), key: 'assertions', sortable: false, width: '90px' },
  { title: t('executionRecords.headers.startedAt'), key: 'started_at', width: '160px' },
  { title: t('executionRecords.headers.actions'), key: 'actions', sortable: false, width: '70px', align: 'center' as const },
])

const buildParams = () => {
  const params: Record<string, any> = {
    page: currentPage.value,
    page_size: pageSize.value,
  }
  if (search.value) params.search = search.value
  if (filters.value.project) params.test_case__project = filters.value.project
  if (filters.value.interface) params.test_case__interface = filters.value.interface
  if (filters.value.status) params.status = filters.value.status
  if (filters.value.startDate) params.started_at__gte = `${filters.value.startDate}T00:00:00`
  if (filters.value.endDate) params.started_at__lte = `${filters.value.endDate}T23:59:59`
  return params
}

const loadRecords = async () => {
  loading.value = true
  try {
    const params = buildParams()
    params.ordering = '-started_at'
    const res = await paginatedRequest<any>({ url: 'executions/', method: 'get', params })
    records.value = res.results
    totalCount.value = res.count
  } catch (e) {
    console.error('Failed to load execution records', e)
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const params = buildParams()
    delete params.page
    delete params.page_size
    const res = await getExecutionStats(params)
    stats.value = res as any
  } catch (e) {
    console.error('Failed to load stats', e)
  }
}

const loadMetadata = async () => {
  try {
    const [dirs, ifaces] = await Promise.all([getDirectories(), getInterfaces({ no_page: true })])
    projects.value = dirs as any[]
    interfaces.value = ifaces as any[]
  } catch (e) {
    console.error(e)
  }
}

const onTableOptionsUpdate = (options: any) => {
  currentPage.value = options.page
  pageSize.value = options.itemsPerPage
  loadRecords()
  loadStats()
}

let searchTimer: ReturnType<typeof setTimeout> | null = null
watch(search, () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    currentPage.value = 1
    loadRecords()
    loadStats()
  }, 400)
})

watch([() => filters.value.project, () => filters.value.interface, () => filters.value.status, () => filters.value.startDate, () => filters.value.endDate], () => {
  currentPage.value = 1
  loadRecords()
  loadStats()
})

const openDetail = (item: any) => {
  selectedRecord.value = item
  detailTab.value = 'request'
  detailDialog.value = true
}

const statusColor = (s: string) => {
  const m: Record<string, string> = { passed: 'success', failed: 'error', error: 'warning', pending: 'grey', running: 'info' }
  return m[s] || 'grey'
}

const methodColor = (m: string) => {
  const c: Record<string, string> = { GET: 'green', POST: 'blue', PUT: 'orange', DELETE: 'red', PATCH: 'purple' }
  return c[m] || 'grey'
}

const formatTime = (dt: string) => {
  if (!dt) return '-'
  return new Date(dt).toLocaleString()
}

const formatJson = (obj: any) => {
  if (!obj) return '{}'
  try {
    return typeof obj === 'string' ? obj : JSON.stringify(obj, null, 2)
  } catch { return String(obj) }
}

onMounted(() => {
  // Apply query params from router (e.g. ?project=1&interface=2)
  if (route.query.project) filters.value.project = Number(route.query.project)
  if (route.query.interface) filters.value.interface = Number(route.query.interface)

  loadMetadata()
})
</script>

<style scoped>
.json-block {
  background: rgba(var(--v-theme-on-surface), 0.04);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 8px;
  padding: 12px 16px;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 0.8125rem;
  line-height: 1.6;
  overflow-x: auto;
  white-space: pre;
  max-height: 300px;
  overflow-y: auto;
  margin: 0;
}
</style>

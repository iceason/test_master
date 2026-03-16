<template>
  <v-container fluid>
    <v-row>
      <!-- 配置卡片 -->
      <v-col cols="12">
        <v-card>
          <v-card-title>
            <v-icon class="mr-2">mdi-play-circle</v-icon>
            {{ $t('execution.title') }}
          </v-card-title>
          
          <v-card-text>
            <v-row>
              <!-- 环境选择 -->
              <v-col cols="12" md="4">
                <v-select
                  v-model="config.environment"
                  :items="environments"
                  item-title="name"
                  item-value="id"
                  :label="$t('execution.fields.environment')"
                  prepend-icon="mdi-earth"
                  required
                />
              </v-col>
              
              <!-- 批次名称 -->
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="config.name"
                  :label="$t('execution.fields.batchName')"
                  prepend-icon="mdi-label"
                />
              </v-col>
              
              <!-- 并发执行 -->
              <v-col cols="12" md="4">
                <v-switch
                  v-model="config.parallel"
                  :label="$t('execution.fields.parallel')"
                  color="primary"
                />
              </v-col>
            </v-row>
            
            <!-- 用例选择 -->
            <v-row>
              <v-col cols="12">
                <v-card variant="outlined">
                  <v-card-title>{{ $t('execution.selectTestCases') }}</v-card-title>
                  <v-card-text>
                    <v-chip-group
                      v-model="selectedCases"
                      column
                      multiple
                    >
                      <v-chip
                        v-for="testCase in testCases"
                        :key="testCase.id"
                        :value="testCase.id"
                        filter
                        variant="outlined"
                      >
                        {{ testCase.name }}
                      </v-chip>
                    </v-chip-group>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-card-text>
          
          <v-card-actions>
            <v-spacer />
            <v-btn
              color="primary"
              size="large"
              :loading="executing"
              :disabled="!canExecute"
              @click="executeTests"
            >
              <v-icon start>mdi-play</v-icon>
              {{ $t('execution.runTests') }}
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
      
      <!-- 执行结果 -->
      <v-col v-if="currentBatch" cols="12">
        <v-card>
          <v-card-title>
            <v-icon class="mr-2">mdi-chart-line</v-icon>
            {{ $t('execution.results') }}
            <v-spacer />
            <v-chip
              :color="getBatchStatusColor(currentBatch.status)"
              variant="flat"
            >
              {{ getBatchStatusText(currentBatch.status) }}
            </v-chip>
          </v-card-title>
          
          <v-card-text>
            <!-- 统计信息 -->
            <v-row>
              <v-col cols="6" md="3">
                <v-card color="blue" variant="tonal">
                  <v-card-text class="text-center">
                    <div class="text-h4">{{ currentBatch.total_cases }}</div>
                    <div class="text-caption">{{ $t('execution.stats.totalCases') }}</div>
                  </v-card-text>
                </v-card>
              </v-col>
              
              <v-col cols="6" md="3">
                <v-card color="green" variant="tonal">
                  <v-card-text class="text-center">
                    <div class="text-h4">{{ currentBatch.passed_cases }}</div>
                    <div class="text-caption">{{ $t('execution.stats.passed') }}</div>
                  </v-card-text>
                </v-card>
              </v-col>
              
              <v-col cols="6" md="3">
                <v-card color="red" variant="tonal">
                  <v-card-text class="text-center">
                    <div class="text-h4">{{ currentBatch.failed_cases }}</div>
                    <div class="text-caption">{{ $t('execution.stats.failed') }}</div>
                  </v-card-text>
                </v-card>
              </v-col>
              
              <v-col cols="6" md="3">
                <v-card color="orange" variant="tonal">
                  <v-card-text class="text-center">
                    <div class="text-h4">{{ currentBatch.error_cases }}</div>
                    <div class="text-caption">{{ $t('execution.stats.error') }}</div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
            
            <!-- 成功率 -->
            <v-row>
              <v-col cols="12">
                <div class="text-subtitle-1 mb-2">
                  {{ $t('execution.successRate') }}: {{ currentBatch.success_rate?.toFixed(1) }}%
                </div>
                <v-progress-linear
                  :model-value="currentBatch.success_rate"
                  :color="currentBatch.success_rate === 100 ? 'green' : 'orange'"
                  height="20"
                />
              </v-col>
            </v-row>
            
            <!-- 执行详情 -->
            <v-row v-if="currentBatch.execution_records">
              <v-col cols="12">
                <v-data-table
                  :headers="executionHeaders"
                  :items="currentBatch.execution_records"
                  :items-per-page="10"
                  @click:row="showExecutionDetail"
                >
                  <template #item.status="{ item }">
                    <v-chip
                      :color="getStatusColor(item.status)"
                      size="small"
                    >
                      {{ getStatusText(item.status) }}
                    </v-chip>
                  </template>
                  
                  <template #item.response_time_ms="{ item }">
                    {{ item.response_time_ms }}ms
                  </template>
                  
                  <template #item.assertions="{ item }">
                    {{ item.assertions_passed }}✓ / {{ item.assertions_failed }}✗
                  </template>
                </v-data-table>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    
    <!-- 执行详情对话框 -->
    <v-dialog v-model="detailDialog" max-width="1200">
      <v-card v-if="selectedExecution">
        <v-card-title>
          {{ selectedExecution.test_case_name }}
          <v-spacer />
          <v-btn icon @click="detailDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        
        <v-card-text>
          <v-tabs v-model="detailTab">
            <v-tab value="request">{{ $t('execution.tabs.request') }}</v-tab>
            <v-tab value="response">{{ $t('execution.tabs.response') }}</v-tab>
            <v-tab value="assertions">{{ $t('execution.tabs.assertions') }}</v-tab>
            <v-tab v-if="selectedExecution.error_message" value="error">{{ $t('execution.tabs.error') }}</v-tab>
          </v-tabs>
          
          <v-window v-model="detailTab" class="mt-4">
            <v-window-item value="request">
              <div class="mb-2"><strong>{{ $t('execution.detail.method') }}:</strong> {{ selectedExecution.request_method }}</div>
              <div class="mb-2"><strong>{{ $t('execution.detail.url') }}:</strong> {{ selectedExecution.request_url }}</div>
              <div class="mb-2"><strong>{{ $t('execution.detail.requestHeaders') }}:</strong></div>
              <pre class="code-block">{{ JSON.stringify(selectedExecution.request_headers, null, 2) }}</pre>
              <div class="mb-2"><strong>{{ $t('execution.detail.requestBody') }}:</strong></div>
              <pre class="code-block">{{ JSON.stringify(selectedExecution.request_body, null, 2) }}</pre>
            </v-window-item>
            
            <v-window-item value="response">
              <div class="mb-2"><strong>{{ $t('execution.detail.statusCode') }}:</strong> {{ selectedExecution.response_status }}</div>
              <div class="mb-2"><strong>{{ $t('execution.detail.responseTime') }}:</strong> {{ selectedExecution.response_time_ms }}ms</div>
              <div class="mb-2"><strong>{{ $t('execution.detail.responseHeaders') }}:</strong></div>
              <pre class="code-block">{{ JSON.stringify(selectedExecution.response_headers, null, 2) }}</pre>
              <div class="mb-2"><strong>{{ $t('execution.detail.responseBody') }}:</strong></div>
              <pre class="code-block">{{ JSON.stringify(selectedExecution.response_body, null, 2) }}</pre>
            </v-window-item>
            
            <v-window-item value="assertions">
              <v-list>
                <v-list-item
                  v-for="(assertion, index) in selectedExecution.assertion_details"
                  :key="index"
                  :prepend-icon="assertion.passed ? 'mdi-check-circle' : 'mdi-alert-circle'"
                  :color="assertion.passed ? 'green' : 'red'"
                >
                  <v-list-item-title>{{ assertion.message }}</v-list-item-title>
                  <v-list-item-subtitle>{{ assertion.description }}</v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-window-item>
            
            <v-window-item v-if="selectedExecution.error_message" value="error">
              <v-alert type="error" prominent>
                {{ selectedExecution.error_message }}
              </v-alert>
              <pre v-if="selectedExecution.error_traceback" class="code-block mt-4">{{ selectedExecution.error_traceback }}</pre>
            </v-window-item>
          </v-window>
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { getEnvironments, executeTestCases, getBatchDetail } from '@/api/execution'
import { getTestCases } from '@/api/testcase'

const { t } = useI18n()

const environments = ref([])
const testCases = ref([])
const selectedCases = ref<number[]>([])
const executing = ref(false)
const currentBatch = ref<any>(null)
const detailDialog = ref(false)
const selectedExecution = ref<any>(null)
const detailTab = ref('request')

const config = ref({
  name: `Batch-${new Date().toLocaleString()}`,
  environment: null,
  parallel: false
})

const executionHeaders = computed(() => [
  { title: t('execution.headers.testCaseName'), key: 'test_case_name' },
  { title: t('execution.headers.status'), key: 'status' },
  { title: t('execution.headers.responseTime'), key: 'response_time_ms' },
  { title: t('execution.headers.assertions'), key: 'assertions' },
])

const canExecute = computed(() => {
  return config.value.environment && selectedCases.value.length > 0
})

const loadEnvironments = async () => {
  try {
    const res = await getEnvironments({ no_page: true })
    environments.value = Array.isArray(res) ? res : []
  } catch (error) {
    console.error('加载环境失败:', error)
  }
}

const loadTestCases = async () => {
  try {
    const res = await getTestCases({ no_page: true })
    testCases.value = Array.isArray(res) ? res : []
  } catch (error) {
    console.error('加载用例失败:', error)
  }
}

const executeTests = async () => {
  if (!canExecute.value) return
  
  executing.value = true
  try {
    const res = await executeTestCases({
      name: config.value.name,
      case_ids: selectedCases.value,
      environment: config.value.environment!,
      parallel: config.value.parallel
    })
    
    // 轮询查询结果
    const batchId = res.batch_db_id
    pollBatchStatus(batchId)
  } catch (error) {
    console.error('执行失败:', error)
    executing.value = false
  }
}

const pollBatchStatus = async (batchId: number) => {
  const poll = async () => {
    try {
      const batch = await getBatchDetail(batchId)
      currentBatch.value = batch
      
      if (batch.status === 'completed' || batch.status === 'cancelled') {
        executing.value = false
      } else {
        setTimeout(poll, 2000) // 2秒后再次查询
      }
    } catch (error) {
      console.error('查询状态失败:', error)
      executing.value = false
    }
  }
  
  poll()
}

const showExecutionDetail = (event: any, { item }: any) => {
  selectedExecution.value = item
  detailDialog.value = true
}

const getBatchStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    pending: 'grey',
    running: 'blue',
    completed: 'green',
    cancelled: 'orange'
  }
  return colors[status] || 'grey'
}

const getBatchStatusText = (status: string) => {
  return t(`execution.batchStatus.${status}`, status)
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    pending: 'grey',
    running: 'blue',
    passed: 'green',
    failed: 'red',
    error: 'orange'
  }
  return colors[status] || 'grey'
}

const getStatusText = (status: string) => {
  return t(`execution.status.${status}`, status)
}

onMounted(() => {
  loadEnvironments()
  loadTestCases()
})
</script>

<style scoped>
.code-block {
  background-color: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 12px;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.5;
}
</style>

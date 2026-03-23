<template>
  <div class="fill-height d-flex flex-column pa-0">
    <!-- 头部操作区 -->
    <div class="d-flex align-center pa-4 bg-surface border-b">
      <div class="d-flex align-center">
        <v-avatar color="primary-lighten-4" size="40" class="mr-3 rounded-lg">
          <v-icon icon="mdi-file-code-outline" color="primary" size="24"></v-icon>
        </v-avatar>
        <div>
          <div class="text-subtitle-1 font-weight-bold text-on-surface">{{ form.name || $t('generation.untitledInterface') }}</div>
          <div class="text-caption text-medium-emphasis">{{ $t('generation.subtitle') }}</div>
        </div>
      </div>
      <v-spacer></v-spacer>
      <v-btn
        variant="flat"
        color="primary"
        elevation="2"
        rounded="lg"
        prepend-icon="mdi-content-save-outline"
        @click="saveInterface"
        :loading="saving"
        class="text-none font-weight-bold"
      >
        {{ $t('common.save') }}
      </v-btn>
    </div>

    <!-- 顶部 Tabs -->
    <v-tabs
      v-model="activeTab"
      color="primary"
      align-tabs="start"
      class="border-b bg-surface"
      density="compact"
    >
      <v-tab value="config" class="text-none px-6">
        <v-icon start icon="mdi-cog-outline" size="small"></v-icon>
        {{ $t('generation.tabDefinition') }}
      </v-tab>
      <v-tab value="generation" class="text-none px-6">
        <v-icon start icon="mdi-creation" size="small"></v-icon>
        {{ $t('generation.tabGeneration') }}
      </v-tab>
      <v-tab value="results" class="text-none px-6">
        <v-icon start icon="mdi-flask-outline" size="small"></v-icon>
        {{ $t('generation.tabResults') }}
        <v-badge
          v-if="resultTotalCount > 0"
          :content="resultTotalCount"
          color="secondary"
          inline
          class="ml-2"
        ></v-badge>
      </v-tab>
    </v-tabs>

    <!-- Tab 内容区 -->
    <div class="flex-grow-1 overflow-hidden bg-background">
        <!-- Tab 1: 配置与定义 -->
        <div v-show="activeTab === 'config'" class="fill-height overflow-y-auto custom-scroll pa-6">
          <div style="max-width: 900px; margin: 0 auto;">
            
            <!-- Basic Info -->
            <v-card variant="flat" class="mb-6 rounded-xl border-thin bg-surface">
              <v-card-title class="text-subtitle-2 font-weight-bold py-3 px-4 border-b bg-grey-lighten-5">
                {{ $t('generation.basicInfo') }}
              </v-card-title>
              <v-card-text class="pa-4 pt-6">
                <v-row>
                  <v-col cols="12" md="8">
                    <v-text-field
                      v-model="form.name"
                      :label="$t('interface.fields.name')"
                      variant="outlined"
                      density="comfortable"
                      :placeholder="$t('generation.namePlaceholder')"
                      bg-color="background"
                    ></v-text-field>
                  </v-col>
                  <v-col cols="12" md="4">
                    <v-select
                      v-model="form.method"
                      :items="['GET', 'POST', 'PUT', 'DELETE', 'PATCH']"
                      :label="$t('interface.fields.method')"
                      variant="outlined"
                      density="comfortable"
                      bg-color="background"
                    ></v-select>
                  </v-col>
                  <v-col cols="12">
                    <v-text-field
                      v-model="form.path"
                      :label="$t('interface.fields.path')"
                      variant="outlined"
                      density="comfortable"
                      placeholder="/api/v1/..."
                      prefix="API"
                      bg-color="background"
                    ></v-text-field>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>

            <!-- Schema -->
            <v-card variant="flat" class="mb-6 rounded-xl border-thin bg-surface">
              <v-card-title class="text-subtitle-2 font-weight-bold py-3 px-4 border-b bg-grey-lighten-5 d-flex justify-space-between align-center">
                <span>{{ $t('generation.schemaDefinition') }}</span>
                <v-chip size="x-small" color="secondary" variant="flat" label class="font-weight-bold">JSON / YAML</v-chip>
              </v-card-title>
              <div class="bg-background pa-4">
                <textarea
                  v-model="form.schema_yaml"
                  class="w-100 text-body-2 font-monospace text-grey-darken-3 bg-transparent border-none"
                  style="outline: none; resize: vertical; min-height: 240px; line-height: 1.5;"
                  :placeholder="$t('generation.schemaPlaceholder')"
                  spellcheck="false"
                ></textarea>
              </div>
            </v-card>

          </div>
        </div>

        <!-- Tab 2: AI生成用例 -->
        <div v-show="activeTab === 'generation'" class="fill-height overflow-y-auto custom-scroll pa-6">
          <div style="max-width: 1200px; margin: 0 auto;">
            
            <div class="text-h6 font-weight-bold mb-4">{{ $t('generation.selectStrategies') }}</div>
            
            <v-chip-group
              v-model="selectedCategories"
              multiple
              class="mb-8"
            >
              <!-- 2x2 Grid Layout for Strategy Categories -->
              <v-row>
                <v-col cols="12" md="6" v-for="(group, key) in strategies" :key="key">
                  <v-card variant="outlined" class="rounded-xl border-thin h-100 d-flex flex-column">
                    <!-- Card Header -->
                    <div class="pa-4 d-flex align-center border-b bg-grey-lighten-5">
                      <v-avatar :color="getCategoryColor(group.title)" size="40" class="mr-3 rounded-lg" variant="tonal">
                        <v-icon :icon="getCategoryIcon(group.title)" :color="getCategoryColor(group.title)"></v-icon>
                      </v-avatar>
                      <div class="flex-grow-1">
                        <div class="text-subtitle-1 font-weight-bold text-grey-darken-3">
                          {{ $t(`strategies.${key}.title`) }}
                        </div>
                        <div class="text-caption text-medium-emphasis">
                          {{ group.items.length }} Options
                        </div>
                      </div>
                      <v-switch
                        :model-value="isGroupSelected(key)"
                        @update:model-value="toggleGroup(key)"
                        color="primary"
                        hide-details
                        inset
                        density="compact"
                      ></v-switch>
                    </div>
                    
                    <!-- Card Content -->
                    <div class="pa-4 flex-grow-1">
                      <div class="d-flex flex-column">
                        <v-chip
                          v-for="sub in group.items"
                          :key="sub.id"
                          :value="sub.id"
                          variant="outlined"
                          size="default"
                          class="font-weight-medium mb-2"
                        >
                          {{ $t(`strategies.${key}.${sub.code}`) }}
                        </v-chip>
                      </div>
                    </div>
                  </v-card>
                </v-col>
              </v-row>
            </v-chip-group>

            <!-- Fixed Bottom Action Bar (Floating) -->
            <div class="position-sticky bottom-0 mt-8 mb-4 d-flex justify-center">
              <v-sheet class="pa-2 rounded-pill elevation-4 d-flex align-center bg-surface border-thin">
                <div class="px-4 text-body-2 font-weight-medium text-grey-darken-2">
                  <span class="text-primary font-weight-bold">{{ selectedCategories.length }}</span> strategies selected
                </div>
                <v-divider vertical class="mx-2 my-2"></v-divider>
                <v-btn
                  color="primary"
                  size="large"
                  prepend-icon="mdi-creation"
                  rounded="pill"
                  elevation="0"
                  class="px-8"
                  @click="startGenerate"
                  :loading="generating"
                  :disabled="selectedCategories.length === 0"
                >
                  {{ $t('generation.startGenerate') }}
                </v-btn>
              </v-sheet>
            </div>

          </div>
        </div>

        <!-- Tab 3: 测试结果 -->
        <div v-if="activeTab === 'results'" class="fill-height d-flex flex-column">
          <!-- 操作栏 -->
          <v-sheet v-if="resultTotalCount > 0" class="pa-3 border-b d-flex align-center bg-surface" elevation="0">
            <v-spacer></v-spacer>
            <v-btn
              color="error"
              variant="tonal"
              prepend-icon="mdi-delete-outline"
              size="small"
              @click="handleResultBatchDelete"
              class="text-none"
              rounded="lg"
            >
              {{ $t('common.batchDelete') }}
            </v-btn>
            <v-menu>
              <template v-slot:activator="{ props: menuProps }">
                <v-btn color="secondary" variant="tonal" prepend-icon="mdi-export" v-bind="menuProps" class="text-none ml-2" size="small" rounded="lg">
                  {{ $t('common.export') }}
                </v-btn>
              </template>
              <v-list density="compact" rounded="xl" elevation="2">
                <v-list-item @click="handleResultExport('excel')" :title="$t('common.exportToExcel')" prepend-icon="mdi-file-excel-outline" rounded="xl" class="mx-2 my-1"></v-list-item>
                <v-list-item @click="handleResultExport('xmind')" :title="$t('common.exportToXMind')" prepend-icon="mdi-brain" rounded="xl" class="mx-2 my-1"></v-list-item>
                <v-list-item @click="handleResultExport('json')" :title="$t('common.exportToJSON')" prepend-icon="mdi-code-json" rounded="xl" class="mx-2 my-1"></v-list-item>
              </v-list>
            </v-menu>
          </v-sheet>

          <div class="flex-grow-1 overflow-hidden">
            <v-data-table-server
              v-model:items-per-page="resultPageSize"
              v-model:page="resultPage"
              :headers="resultHeaders"
              :items="testCases"
              :items-length="resultTotalCount"
              :loading="resultLoading"
              fixed-header
              hover
              item-key="id"
              class="fill-height"
              density="comfortable"
              @update:options="onResultTableOptions"
            >
              <template v-slot:header.select>
                <v-checkbox
                  v-model="resultAllSelected"
                  :indeterminate="resultSelectedIds.length > 0 && resultSelectedIds.length < testCases.length"
                  @change="toggleResultSelectAll"
                  hide-details
                ></v-checkbox>
              </template>

              <template v-slot:item.select="{ item }">
                <v-checkbox
                  :model-value="resultSelectedSet.has(item.id)"
                  @update:model-value="toggleResultItem(item.id)"
                  hide-details
                ></v-checkbox>
              </template>

              <template v-slot:item.test_type="{ item }">
                <v-chip v-if="item.test_type" size="small" label :color="getTestTypeColor(item.test_type)">
                  {{ getTestTypeTitle(item.test_type) }}
                </v-chip>
                <span v-else class="text-grey">-</span>
              </template>

              <template v-slot:item.category_name="{ item }">
                <v-chip v-if="item.category_name" size="small" label color="info" variant="tonal">
                  {{ item.category_name }}
                </v-chip>
                <span v-else class="text-grey text-caption">-</span>
              </template>

              <template v-slot:item.test_field="{ item }">
                <code v-if="item.test_field" class="text-grey-darken-3 bg-grey-lighten-4 px-1 rounded">{{ item.test_field }}</code>
                <span v-else class="text-grey">-</span>
              </template>

              <template v-slot:item.actions="{ item }">
                <v-tooltip location="top" :text="$t('common.detail')">
                  <template v-slot:activator="{ props: tipProps }">
                    <v-btn v-bind="tipProps" icon="mdi-eye" variant="text" size="small" color="info" @click="openResultDetail(item)"></v-btn>
                  </template>
                </v-tooltip>
                <v-tooltip location="top" :text="$t('common.delete')">
                  <template v-slot:activator="{ props: tipProps }">
                    <v-btn v-bind="tipProps" icon="mdi-delete" variant="text" size="small" color="error" @click="openResultDeleteDialog(item)"></v-btn>
                  </template>
                </v-tooltip>
              </template>

              <template v-slot:no-data>
                <div class="d-flex flex-column align-center justify-center py-12 text-medium-emphasis">
                  <v-icon icon="mdi-clipboard-text-outline" size="64" class="mb-4 opacity-20"></v-icon>
                  <div class="text-h6 font-weight-medium opacity-50">{{ $t('generation.noCases') }}</div>
                  <div class="text-caption opacity-40">{{ $t('generation.switchTabTip') }}</div>
                  <v-btn color="primary" variant="text" class="mt-4" @click="activeTab = 'generation'">
                    {{ $t('generation.goToGeneration') }}
                  </v-btn>
                </div>
              </template>
            </v-data-table-server>
          </div>

          <!-- Detail Dialog -->
          <v-dialog v-model="resultDetailDialog" max-width="960px" scrollable>
            <v-card class="rounded-xl">
              <v-toolbar color="primary" density="compact" class="px-2">
                <v-toolbar-title class="text-subtitle-1 font-weight-bold text-white">{{ $t('common.detail') }}</v-toolbar-title>
                <v-spacer />
                <v-btn icon="mdi-close" variant="text" color="white" size="small" @click="resultDetailDialog = false" />
              </v-toolbar>
              <v-card-text v-if="resultDetailItem" class="pa-0" style="max-height: 75vh; overflow-y: auto;">
                <div class="px-6 pt-5 pb-3">
                  <div class="text-h6 font-weight-bold" style="word-break: break-word;">{{ resultDetailItem.name }}</div>
                  <div class="text-caption text-medium-emphasis mt-1">ID: {{ resultDetailItem.id }}</div>
                </div>
                <v-divider />
                <div class="px-6 py-4">
                  <v-row dense>
                    <v-col cols="6" sm="4">
                      <div class="detail-field">
                        <div class="detail-label">{{ $t('testcase.fields.testType') }}</div>
                        <v-chip v-if="resultDetailItem.test_type" size="small" label :color="getTestTypeColor(resultDetailItem.test_type)">
                          {{ getTestTypeTitle(resultDetailItem.test_type) }}
                        </v-chip>
                        <span v-else class="text-medium-emphasis">-</span>
                      </div>
                    </v-col>
                    <v-col cols="6" sm="4">
                      <div class="detail-field">
                        <div class="detail-label">{{ $t('testcase.fields.category') }}</div>
                        <div class="detail-value">{{ resultDetailItem.category_name || '-' }}</div>
                      </div>
                    </v-col>
                    <v-col cols="6" sm="4">
                      <div class="detail-field">
                        <div class="detail-label">{{ $t('testcase.fields.testField') }}</div>
                        <code v-if="resultDetailItem.test_field" class="text-body-2">{{ resultDetailItem.test_field }}</code>
                        <span v-else class="text-medium-emphasis">-</span>
                      </div>
                    </v-col>
                    <v-col cols="6" sm="4">
                      <div class="detail-field">
                        <div class="detail-label">{{ $t('testcase.fields.createdAt') }}</div>
                        <div class="detail-value">{{ resultDetailItem.created_at || '-' }}</div>
                      </div>
                    </v-col>
                  </v-row>
                </div>
                <template v-if="resultDetailItem.description">
                  <v-divider />
                  <div class="px-6 py-4">
                    <div class="detail-label mb-2">{{ $t('testcase.fields.description') }}</div>
                    <div class="text-body-2" style="word-break: break-word; white-space: pre-wrap;">{{ resultDetailItem.description }}</div>
                  </div>
                </template>
                <v-divider />
                <div class="px-6 py-4">
                  <v-row>
                    <v-col cols="12" md="6">
                      <div class="detail-label mb-2">{{ $t('testcase.fields.requestData') }}</div>
                      <pre class="detail-json-block">{{ resultDetailItem.request_data ? JSON.stringify(resultDetailItem.request_data, null, 2) : '{}' }}</pre>
                    </v-col>
                    <v-col cols="12" md="6">
                      <div class="detail-label mb-2">{{ $t('testcase.fields.expectedValue') }}</div>
                      <pre class="detail-json-block">{{ resultDetailItem.expected_value ? JSON.stringify(resultDetailItem.expected_value, null, 2) : '{}' }}</pre>
                    </v-col>
                  </v-row>
                </div>
              </v-card-text>
            </v-card>
          </v-dialog>

          <!-- Delete Confirmation -->
          <v-dialog v-model="resultDeleteDialog" max-width="400px">
            <v-card class="rounded-xl">
              <v-card-title class="text-subtitle-1 font-weight-bold pa-4 bg-error text-white">{{ $t('common.delete') }}</v-card-title>
              <v-card-text class="pa-4 text-body-2">
                {{ resultDeleteName ? $t('common.confirmDelete', { name: resultDeleteName }) : '' }}
              </v-card-text>
              <v-card-actions class="px-6 pb-4">
                <v-spacer></v-spacer>
                <v-btn variant="text" color="grey-darken-1" rounded="lg" class="text-none" @click="resultDeleteDialog = false">{{ $t('common.cancel') }}</v-btn>
                <v-btn color="error" variant="flat" rounded="lg" class="text-none ml-3" @click="confirmResultDelete">{{ $t('common.delete') }}</v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>

          <!-- Batch Delete Confirmation -->
          <v-dialog v-model="resultBatchDeleteDialog" max-width="400px">
            <v-card class="rounded-xl">
              <v-card-title class="text-subtitle-1 font-weight-bold pa-4 bg-error text-white">{{ $t('common.batchDelete') }}</v-card-title>
              <v-card-text class="pa-4 text-body-2">
                {{ $t('common.confirmBatchDelete', { count: resultSelectedIds.length }) }}
              </v-card-text>
              <v-card-actions class="px-6 pb-4">
                <v-spacer></v-spacer>
                <v-btn variant="text" color="grey-darken-1" rounded="lg" class="text-none" @click="resultBatchDeleteDialog = false">{{ $t('common.cancel') }}</v-btn>
                <v-btn color="error" variant="flat" rounded="lg" class="text-none ml-3" @click="confirmResultBatchDelete">{{ $t('common.delete') }}</v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>
        </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { updateInterface, generateTestCases, getInterfaces } from '@/api/interface'
import { getTestCasesPaginated, deleteTestCase, exportTestCases, batchDeleteTestCases } from '@/api/testcase'
import { getCategories } from '@/api/category'
import type { Interface } from '@/api/interface'
import type { TestCase } from '@/api/testcase'
import type { TestCaseCategory } from '@/api/category'

const props = defineProps<{ interfaceId: number }>()
const emit = defineEmits(['refresh-tree'])
const { t } = useI18n()

// 状态
const activeTab = ref('config')
const loading = ref(false)
const generating = ref(false)
const saving = ref(false)
const form = ref<Partial<Interface>>({})
const testCases = ref<TestCase[]>([])
const allCategories = ref<TestCaseCategory[]>([])
const selectedCategories = ref<number[]>([])

// 策略分组结构
const strategies = ref<Record<string, any>>({
  positive: { title: 'Positive', items: [] },
  negative: { title: 'Negative', items: [] },
  boundary: { title: 'Boundary', items: [] },
  security: { title: 'Security', items: [] }
})

// 图标映射
// --- Results tab: pagination state ---
const resultPage = ref(1)
const resultPageSize = ref(20)
const resultTotalCount = ref(0)
const resultLoading = ref(false)
const resultSortBy = ref<{ key: string; order: string }[]>([])

const loadTestCases = async () => {
  if (!props.interfaceId) return
  resultLoading.value = true
  try {
    let ordering = '-created_at'
    if (resultSortBy.value.length > 0) {
      const s = resultSortBy.value[0]
      ordering = s.order === 'desc' ? `-${s.key}` : s.key
    }
    const res = await getTestCasesPaginated({
      interface: props.interfaceId,
      page: resultPage.value,
      page_size: resultPageSize.value,
      ordering,
    })
    testCases.value = res.results
    resultTotalCount.value = res.count
  } catch (e) {
    console.error(e)
  } finally {
    resultLoading.value = false
  }
}

const onResultTableOptions = (options: any) => {
  resultPage.value = options.page
  resultPageSize.value = options.itemsPerPage
  if (options.sortBy?.length > 0) {
    resultSortBy.value = options.sortBy
  } else {
    resultSortBy.value = []
  }
  loadTestCases()
}

// --- Results tab: table headers ---
const resultHeaders = computed(() => [
  { title: '', key: 'select', sortable: false, width: '50px', align: 'center' as const },
  { title: 'ID', key: 'id', align: 'start' as const, width: '70px' },
  { title: t('testcase.fields.name'), key: 'name', minWidth: '220px' },
  { title: t('testcase.fields.testType'), key: 'test_type', width: '110px' },
  { title: t('testcase.fields.category'), key: 'category_name', width: '140px' },
  { title: t('testcase.fields.testField'), key: 'test_field', width: '130px' },
  { title: t('common.actions'), key: 'actions', sortable: false, align: 'end' as const, width: '120px' },
])

// --- Results tab: selection state ---
const resultSelectedSet = ref(new Set<number>())
const resultSelectedIds = computed(() => Array.from(resultSelectedSet.value))
const resultAllSelected = computed(() => testCases.value.length > 0 && resultSelectedIds.value.length === testCases.value.length)

const toggleResultItem = (id: number) => {
  if (resultSelectedSet.value.has(id)) {
    resultSelectedSet.value.delete(id)
  } else {
    resultSelectedSet.value.add(id)
  }
}

const toggleResultSelectAll = () => {
  if (resultSelectedIds.value.length === testCases.value.length) {
    resultSelectedSet.value.clear()
  } else {
    resultSelectedSet.value = new Set(testCases.value.map(c => c.id))
  }
}

// --- Results tab: detail dialog ---
const resultDetailDialog = ref(false)
const resultDetailItem = ref<TestCase | null>(null)
const openResultDetail = (item: TestCase) => {
  resultDetailItem.value = item
  resultDetailDialog.value = true
}

// --- Results tab: delete ---
const resultDeleteDialog = ref(false)
const resultDeleteId = ref<number | null>(null)
const resultDeleteName = ref('')
const resultBatchDeleteDialog = ref(false)

const openResultDeleteDialog = (item: TestCase) => {
  resultDeleteId.value = item.id
  resultDeleteName.value = item.name
  resultDeleteDialog.value = true
}

const confirmResultDelete = async () => {
  if (resultDeleteId.value) {
    await deleteTestCase(resultDeleteId.value)
    resultDeleteDialog.value = false
    loadTestCases()
  }
}

const handleResultBatchDelete = () => {
  if (resultSelectedIds.value.length === 0) return
  resultBatchDeleteDialog.value = true
}

const confirmResultBatchDelete = async () => {
  if (resultSelectedIds.value.length > 0) {
    await batchDeleteTestCases(resultSelectedIds.value)
    resultSelectedSet.value.clear()
    resultBatchDeleteDialog.value = false
    loadTestCases()
  }
}

// --- Results tab: export ---
const handleResultExport = async (format: 'excel' | 'xmind' | 'json') => {
  const ids = resultSelectedIds.value.length > 0
    ? resultSelectedIds.value
    : testCases.value.map(c => c.id)
  if (ids.length === 0) return
  try {
    const blob = await exportTestCases(format, ids)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `test_cases.${format === 'excel' ? 'xlsx' : format}`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  } catch (e) {
    console.error(e)
  }
}

// --- Results tab: test type helpers ---
const getTestTypeColor = (type: string) => {
  const map: Record<string, string> = { positive: 'green', negative: 'red', boundary: 'orange', security: 'purple' }
  return map[type] || 'grey'
}
const getTestTypeTitle = (type: string) => t(`testcase.testType.${type}`, type)

const getCategoryIcon = (name?: string) => {
  if (!name) return 'mdi-checkbox-blank-circle-outline'
  if (name.includes('Positive')) return 'mdi-check-circle-outline'
  if (name.includes('Negative')) return 'mdi-alert-circle-outline'
  if (name.includes('Boundary')) return 'mdi-arrow-expand-horizontal'
  if (name.includes('Security')) return 'mdi-shield-outline'
  return 'mdi-checkbox-blank-circle-outline'
}

const getCategoryColor = (name?: string) => {
  if (!name) return 'grey'
  if (name.includes('Positive')) return 'success'
  if (name.includes('Negative')) return 'warning'
  if (name.includes('Boundary')) return 'info'
  if (name.includes('Security')) return 'error'
  return 'grey'
}

// 加载接口定义
const loadInterfaceData = async () => {
  if (!props.interfaceId) return
  loading.value = true
  try {
    const ifaces = await getInterfaces({ id: props.interfaceId })
    const iface = ifaces.find(i => i.id === props.interfaceId)
    if (iface) {
      form.value = { ...iface }
      if (iface.schema) {
        form.value.schema_yaml = JSON.stringify(iface.schema, null, 2)
      }
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const loadData = async () => {
  await loadInterfaceData()
}

// 加载分类并分组
const loadCategories = async () => {
  try {
    const cats = await getCategories()
    allCategories.value = cats
    
    // 提取所有子分类到一个扁平数组
    const allSubCategories = cats.flatMap(root => root.sub_categories || [])

    const groupMap: Record<string, string[]> = {
      positive: ['positive_necessary', 'positive_valid', 'positive_enum', 'positive_other'],
      negative: ['negative_invalid_class', 'negative_missing_required', 'negative_format_error', 'negative_type_error', 'negative_semantic_invalid', 'negative_other'],
      boundary: ['boundary_max_min', 'boundary_out_of_range', 'boundary_null_empty', 'boundary_length', 'boundary_time', 'boundary_file_size', 'boundary_array'],
      security: ['security_auth', 'security_sql_injection', 'security_fuzz', 'security_xss', 'security_cmd_injection', 'security_json_injection', 'security_nosql_injection', 'security_jwt', 'security_rate_limit']
    }

    for (const key in groupMap) {
      const groupCodes = groupMap[key]
      if (groupCodes) {
        strategies.value[key].items = allSubCategories.filter(c => groupCodes.includes(c.code))
      }
    }
  } catch (e) {
    console.error(e)
  }
}

// 保存接口
const saveInterface = async () => {
  saving.value = true
  try {
    if (form.value.schema_yaml) {
      try {
        JSON.parse(form.value.schema_yaml)
      } catch (e) {
        // Ignore
      }
    }
    await updateInterface(props.interfaceId, form.value)
    emit('refresh-tree')
  } catch (e) {
    console.error(e)
  } finally {
    saving.value = false
  }
}

// 切换分类选择 (Deprecated: handled by v-chip-group v-model)
const toggleCategory = (id: number) => {
  // Logic moved to v-chip-group v-model
}

// 判断组是否全选
const isGroupSelected = (key: string) => {
  const groupItems = strategies.value[key].items
  if (groupItems.length === 0) return false
  return groupItems.every((item: any) => selectedCategories.value.includes(item.id))
}

// 切换组全选
const toggleGroup = (key: string) => {
  const groupItems = strategies.value[key].items
  const allSelected = isGroupSelected(key)
  
  if (allSelected) {
    // 取消全选
    const idsToRemove = groupItems.map((item: any) => item.id)
    selectedCategories.value = selectedCategories.value.filter(id => !idsToRemove.includes(id))
  } else {
    // 全选
    const idsToAdd = groupItems.map((item: any) => item.id)
    const newIds = idsToAdd.filter((id: number) => !selectedCategories.value.includes(id))
    selectedCategories.value = [...selectedCategories.value, ...newIds]
  }
}

// 生成用例
const startGenerate = async () => {
  if (selectedCategories.value.length === 0) return
  
  generating.value = true
  try {
    await generateTestCases(props.interfaceId, { category_ids: selectedCategories.value })
    activeTab.value = 'results'
    resultPage.value = 1
    await loadTestCases()
  } catch (e) {
    console.error(e)
  } finally {
    generating.value = false
  }
}

watch(() => props.interfaceId, () => {
  loadData()
  selectedCategories.value = []
  resultSelectedSet.value.clear()
  resultPage.value = 1
  resultTotalCount.value = 0
  testCases.value = []
  activeTab.value = 'config'
})

onMounted(() => {
  loadData()
  loadCategories()
})
</script>

<style scoped>
.gap-2 { gap: 8px; }
.gap-3 { gap: 12px; }
.letter-spacing-1 { letter-spacing: 1px; }
.custom-scroll::-webkit-scrollbar { width: 6px; }
.custom-scroll::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.1); border-radius: 3px; }

.detail-field { margin-bottom: 12px; }
.detail-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-bottom: 4px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}
.detail-value {
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.87);
}
.detail-json-block {
  background: rgba(var(--v-theme-on-surface), 0.04);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 8px;
  padding: 12px 16px;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 0.8125rem;
  line-height: 1.6;
  overflow-x: auto;
  white-space: pre;
  max-height: 320px;
  overflow-y: auto;
  margin: 0;
}
</style>

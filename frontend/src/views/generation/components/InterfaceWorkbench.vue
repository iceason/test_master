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
          v-if="testCases.length > 0"
          :content="testCases.length"
          color="secondary"
          inline
          class="ml-2"
        ></v-badge>
      </v-tab>
    </v-tabs>

    <!-- Tab 内容区 -->
    <div class="flex-grow-1 overflow-hidden bg-background">
      <v-window v-model="activeTab" class="fill-height">
        
        <!-- Tab 1: 配置与定义 -->
        <v-window-item value="config" class="fill-height overflow-y-auto custom-scroll pa-6">
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
        </v-window-item>

        <!-- Tab 2: AI生成用例 -->
        <v-window-item value="generation" class="fill-height overflow-y-auto custom-scroll pa-6">
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
        </v-window-item>

        <!-- Tab 3: 测试结果 -->
        <v-window-item value="results" class="fill-height overflow-y-auto custom-scroll pa-6">
          <div style="max-width: 900px; margin: 0 auto;">
            
            <!-- UML 简图 -->
            <v-card variant="flat" class="mb-6 bg-surface border-thin rounded-xl pa-6 d-flex justify-center align-center" style="min-height: 140px;">
              <div class="d-flex align-center w-100 justify-center">
                <div class="d-flex flex-column align-center">
                  <v-icon icon="mdi-account-circle" size="48" color="primary" class="mb-2"></v-icon>
                  <div class="text-caption font-weight-bold">{{ $t('generation.actor') }}</div>
                </div>
                
                <div class="mx-6 flex-grow-1 d-flex flex-column align-center" style="max-width: 200px;">
                  <div class="text-caption font-weight-bold text-primary mb-1">{{ form.method || 'METHOD' }}</div>
                  <div class="w-100 border-t border-primary border-opacity-50 mb-1 position-relative" style="height: 1px;">
                    <v-icon icon="mdi-menu-right" color="primary" size="small" style="position: absolute; right: -6px; top: -11px;"></v-icon>
                  </div>
                  <div class="text-caption text-truncate w-100 text-center text-medium-emphasis">{{ form.path || '/api/...' }}</div>
                </div>

                <div class="d-flex flex-column align-center">
                  <v-icon icon="mdi-server-network" size="48" color="secondary" class="mb-2"></v-icon>
                  <div class="text-caption font-weight-bold">{{ $t('generation.system') }}</div>
                </div>
              </div>
            </v-card>

            <!-- 用例列表 -->
            <div v-if="testCases.length > 0">
              <v-expansion-panels variant="accordion" class="rounded-xl overflow-hidden border-thin">
                <v-expansion-panel
                  v-for="item in testCases"
                  :key="item.id"
                  elevation="0"
                  class="bg-surface border-b"
                >
                  <v-expansion-panel-title class="py-3">
                    <div class="d-flex align-center w-100 overflow-hidden">
                      <v-icon 
                        :icon="getCategoryIcon(item.category_name)" 
                        size="24" 
                        :color="getCategoryColor(item.category_name)" 
                        class="mr-4"
                      ></v-icon>
                      <div class="d-flex flex-column overflow-hidden">
                        <span class="text-body-1 font-weight-bold text-truncate">{{ item.name }}</span>
                        <span class="text-caption text-medium-emphasis text-truncate">{{ item.description }}</span>
                      </div>
                      <v-spacer></v-spacer>
                      <v-chip size="small" :color="getCategoryColor(item.category_name)" variant="tonal" class="mr-2">
                        {{ item.category_name?.split('_')[0] || $t('generation.general') }}
                      </v-chip>
                    </div>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text class="bg-grey-lighten-5 pt-4">
                    <div class="d-flex flex-column gap-3">
                      <div>
                        <div class="text-caption font-weight-bold text-medium-emphasis mb-1">{{ $t('testcase.fields.requestData') }}:</div>
                        <div class="bg-surface border-thin rounded-lg pa-4 text-caption font-monospace text-grey-darken-3">
                          {{ JSON.stringify(item.request_data, null, 2) }}
                        </div>
                      </div>
                      <div class="d-flex justify-end mt-2">
                        <v-btn 
                          size="small" 
                          variant="text" 
                          color="error" 
                          prepend-icon="mdi-delete-outline"
                          @click="deleteCase(item.id)"
                          class="text-none"
                        >
                          {{ $t('generation.deleteCase') }}
                        </v-btn>
                      </div>
                    </div>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>
            </div>
            
            <div v-else class="d-flex flex-column align-center justify-center py-12 text-medium-emphasis">
              <v-icon icon="mdi-clipboard-text-outline" size="64" class="mb-4 opacity-20"></v-icon>
              <div class="text-h6 font-weight-medium opacity-50">{{ $t('generation.noCases') }}</div>
              <div class="text-caption opacity-40">{{ $t('generation.switchTabTip') }}</div>
              <v-btn color="primary" variant="text" class="mt-4" @click="activeTab = 'config'">
                {{ $t('generation.goToGeneration') }}
              </v-btn>
            </div>
          </div>
        </v-window-item>
      </v-window>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { updateInterface, generateTestCases, getInterfaces } from '@/api/interface'
import { getTestCases, deleteTestCase } from '@/api/testcase'
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

// 加载数据
const loadData = async () => {
  if (!props.interfaceId) return
  loading.value = true
  try {
    const [ifaces, cases] = await Promise.all([
      getInterfaces({ id: props.interfaceId }), 
      getTestCases({ interface: props.interfaceId, no_page: true })
    ])
    
    const iface = ifaces.find(i => i.id === props.interfaceId)
    if (iface) {
      form.value = { ...iface }
      if (iface.schema) {
        form.value.schema_yaml = JSON.stringify(iface.schema, null, 2)
      }
    }
    
    testCases.value = cases
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
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
    // 自动切换到结果 Tab
    activeTab.value = 'results'
    // 立即加载一次数据，后台生成完成后用户可手动刷新
    await loadData()
  } catch (e) {
    console.error(e)
  } finally {
    generating.value = false
  }
}

const deleteCase = async (id: number) => {
  if (confirm(t('common.confirmDelete', { name: 'Case' }))) {
    await deleteTestCase(id)
    loadData()
  }
}

watch(() => props.interfaceId, () => {
  loadData()
  selectedCategories.value = [] // 重置选择
  activeTab.value = 'config' // 切回配置页
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
</style>

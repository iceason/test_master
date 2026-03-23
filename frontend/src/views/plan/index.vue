<template>
  <v-container fluid>
    <!-- 顶部操作栏 -->
    <v-sheet class="pa-4 rounded-xl border-thin" elevation="0" color="surface">
      <v-row dense align="center">
        <v-col cols="12" md="4">
          <v-text-field
            v-model="search"
            :placeholder="$t('common.search')"
            prepend-inner-icon="mdi-magnify"
            variant="outlined"
            density="compact"
            hide-details
            bg-color="background"
            class="rounded-lg"
          ></v-text-field>
        </v-col>
        <v-col cols="12" md="3">
          <v-select
            v-model="statusFilter"
            :items="statusOptions"
            :placeholder="$t('plan.fields.status')"
            variant="outlined"
            density="compact"
            hide-details
            bg-color="background"
            class="rounded-lg"
            clearable
          ></v-select>
        </v-col>
        <v-col cols="12" md="2">
          <v-btn
            color="primary"
            prepend-icon="mdi-plus"
            @click="openDialog()"
            class="text-none font-weight-bold w-100"
          >
            {{ $t('plan.new') }}
          </v-btn>
        </v-col>
        <v-spacer></v-spacer>
      </v-row>
    </v-sheet>

    <!-- 列表区域 -->
    <v-card class="mt-4" elevation="1">
      <v-data-table
        :headers="headers"
        :items="filteredItems"
        :loading="loading"
        hover
      >
        <!-- 状态列 -->
        <template v-slot:item.status="{ item }">
          <v-chip
            :color="getStatusColor(item.status)"
            size="small"
            variant="flat"
            class="font-weight-medium"
          >
            {{ $t(`plan.status.${item.status}`) }}
          </v-chip>
        </template>

        <!-- 操作列 -->
        <template v-slot:item.actions="{ item }">
          <div class="d-flex align-center">
            <v-tooltip location="top" :text="$t('plan.run')">
              <template v-slot:activator="{ props }">
                <v-btn
                  v-bind="props"
                  icon="mdi-play-circle-outline"
                  variant="text"
                  color="success"
                  size="small"
                  @click="runPlan(item)"
                ></v-btn>
              </template>
            </v-tooltip>
            <v-tooltip location="top" :text="$t('common.edit')">
              <template v-slot:activator="{ props }">
                <v-btn
                  v-bind="props"
                  icon="mdi-pencil-outline"
                  variant="text"
                  color="primary"
                  size="small"
                  @click="openDialog(item)"
                ></v-btn>
              </template>
            </v-tooltip>
            <v-tooltip location="top" :text="$t('common.delete')">
              <template v-slot:activator="{ props }">
                <v-btn
                  v-bind="props"
                  icon="mdi-delete-outline"
                  variant="text"
                  color="error"
                  size="small"
                  @click="deleteItem(item)"
                ></v-btn>
              </template>
            </v-tooltip>
          </div>
        </template>
        
        <template v-slot:no-data>
          <v-empty-state
            icon="mdi-clipboard-text-off-outline"
            :title="$t('common.noData')"
            class="py-10"
          ></v-empty-state>
        </template>
      </v-data-table>
    </v-card>

    <!-- 创建/编辑对话框 -->
    <v-dialog v-model="dialog" max-width="600px">
      <v-card class="rounded-xl">
        <v-card-title class="pa-4 bg-primary text-white d-flex align-center justify-space-between">
          <span class="text-subtitle-1 font-weight-bold">{{ form.id ? $t('plan.edit') : $t('plan.new') }}</span>
          <v-btn icon="mdi-close" variant="text" color="white" density="compact" @click="dialog = false"></v-btn>
        </v-card-title>
        
        <v-card-text class="pa-6">
          <v-form ref="formRef" @submit.prevent="saveItem">
            <v-text-field
              v-model="form.name"
              :label="$t('plan.fields.name')"
              variant="outlined"
              density="compact"
              class="mb-4"
              :rules="[v => !!v || $t('common.required')]"
            ></v-text-field>
            
            <v-row>
              <v-col cols="6">
                <v-text-field
                  v-model="form.version"
                  :label="$t('plan.fields.version')"
                  variant="outlined"
                  density="compact"
                  class="mb-4"
                  placeholder="v1.0.0"
                ></v-text-field>
              </v-col>
              <v-col cols="6">
                <v-select
                  v-model="form.environment"
                  :items="environmentOptions"
                  :label="$t('plan.fields.environment')"
                  variant="outlined"
                  density="comfortable"
                  class="mb-4"
                ></v-select>
              </v-col>
            </v-row>

            <v-textarea
              v-model="form.description"
              :label="$t('plan.fields.description')"
              variant="outlined"
              density="compact"
              rows="3"
            ></v-textarea>
          </v-form>
        </v-card-text>
        
        <v-divider></v-divider>
        
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn
            variant="text"
            color="grey-darken-1"
            @click="dialog = false"
            class="px-6 rounded-lg"
          >
            {{ $t('common.cancel') }}
          </v-btn>
          <v-btn
            color="primary"
            variant="flat"
            @click="saveItem"
            :loading="saving"
            class="px-6 rounded-lg ml-2"
          >
            {{ $t('common.save') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useSnackbarStore } from '@/store/snackbar'

const { t } = useI18n()
const snackbar = useSnackbarStore()

// 状态定义
const loading = ref(false)
const saving = ref(false)
const search = ref('')
const statusFilter = ref(null)
const dialog = ref(false)
const formRef = ref<any>(null)

// 模拟数据结构
interface Plan {
  id: number
  name: string
  version: string
  status: 'pending' | 'running' | 'completed'
  caseCount: number
  creator: string
  createTime: string
  description?: string
  environment?: string
}

// 模拟数据源
const items = ref<Plan[]>([
  { id: 1, name: 'Regression Test V1.0', version: 'v1.0.0', status: 'completed', caseCount: 45, creator: 'Admin', createTime: '2025-01-20 10:00', environment: 'Testing' },
  { id: 2, name: 'Login Module Smoke Test', version: 'v1.1.0', status: 'pending', caseCount: 12, creator: 'Tester', createTime: '2025-01-24 14:30', environment: 'Development' },
])

const form = ref<Partial<Plan>>({})

// 表格配置
const headers = computed(() => [
  { title: t('plan.fields.name'), key: 'name', align: 'start' as const },
  { title: t('plan.fields.version'), key: 'version' },
  { title: t('plan.fields.status'), key: 'status' },
  { title: t('plan.fields.caseCount'), key: 'caseCount' },
  { title: t('plan.fields.environment'), key: 'environment' },
  { title: t('plan.fields.creator'), key: 'creator' },
  { title: t('plan.fields.createTime'), key: 'createTime' },
  { title: t('common.actions'), key: 'actions', sortable: false, align: 'end' as const },
])

const statusOptions = computed(() => [
  { title: t('plan.status.pending'), value: 'pending' },
  { title: t('plan.status.running'), value: 'running' },
  { title: t('plan.status.completed'), value: 'completed' },
])

const environmentOptions = computed(() => [
  { title: t('plan.environment.development'), value: 'Development' },
  { title: t('plan.environment.testing'), value: 'Testing' },
  { title: t('plan.environment.staging'), value: 'Staging' },
  { title: t('plan.environment.production'), value: 'Production' },
])

// 过滤逻辑
const filteredItems = computed(() => {
  return items.value.filter(item => {
    const matchesSearch = !search.value || item.name.toLowerCase().includes(search.value.toLowerCase())
    const matchesStatus = !statusFilter.value || item.status === statusFilter.value
    return matchesSearch && matchesStatus
  })
})

// 方法
const getStatusColor = (status: string) => {
  const map: Record<string, string> = {
    pending: 'grey',
    running: 'info',
    completed: 'success',
  }
  return map[status] || 'grey'
}

const openDialog = (item?: Plan) => {
  if (item) {
    form.value = { ...item }
  } else {
    form.value = {
      name: '',
      version: '',
      status: 'pending',
      caseCount: 0,
      environment: 'Testing'
    }
  }
  dialog.value = true
}

const saveItem = async () => {
  const { valid } = await formRef.value.validate()
  if (!valid) return

  saving.value = true
  // 模拟 API 调用
  setTimeout(() => {
    if (form.value.id) {
      // 编辑
      const index = items.value.findIndex(i => i.id === form.value.id)
      if (index !== -1) items.value[index] = { ...items.value[index], ...form.value } as Plan
    } else {
      // 新建
      items.value.unshift({
        id: Date.now(),
        name: form.value.name!,
        version: form.value.version || 'v1.0',
        status: 'pending',
        caseCount: 0,
        creator: 'Admin', // Mock user
        createTime: new Date().toISOString().slice(0, 16).replace('T', ' '),
        environment: form.value.environment,
        description: form.value.description
      })
    }
    
    saving.value = false
    dialog.value = false
    snackbar.notify(t('common.success'), 'success')
  }, 600)
}

const deleteItem = (item: Plan) => {
  if (confirm(t('common.confirmDelete', { name: item.name }))) {
    items.value = items.value.filter(i => i.id !== item.id)
    snackbar.notify(t('common.success'), 'success')
  }
}

const runPlan = (item: Plan) => {
  item.status = 'running'
  snackbar.notify(t('plan.status.running'), 'info')
  // 模拟运行
  setTimeout(() => {
    item.status = 'completed'
    snackbar.notify(t('plan.status.completed'), 'success')
  }, 2000)
}
</script>

<style scoped>
.border-b { border-bottom: 1px solid rgba(0,0,0,0.08) !important; }
</style>

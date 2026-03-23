<template>
  <v-container fluid>
    <!-- 页头 + 操作栏 -->
    <v-sheet class="pa-4 rounded-xl border-thin" elevation="0" color="surface">
      <v-row dense align="center" class="mb-3">
        <v-col>
          <div class="d-flex align-center">
            <v-avatar color="primary" variant="tonal" size="40" class="mr-3">
              <v-icon icon="mdi-server-outline" size="22"></v-icon>
            </v-avatar>
            <div>
              <div class="text-h6 font-weight-bold">{{ $t('testing.agents.title') }}</div>
              <div class="text-caption text-medium-emphasis">{{ $t('testing.agents.subtitle') }}</div>
            </div>
          </div>
        </v-col>
      </v-row>
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
          />
        </v-col>
        <v-col cols="12" md="3">
          <v-select
            v-model="statusFilter"
            :items="statusOptions"
            :placeholder="$t('testing.agents.fields.status')"
            variant="outlined"
            density="compact"
            hide-details
            bg-color="background"
            class="rounded-lg"
            clearable
          />
        </v-col>
        <v-col cols="12" md="2">
          <v-btn
            color="primary"
            prepend-icon="mdi-plus"
            @click="openDialog()"
            class="text-none font-weight-bold w-100"
          >
            {{ $t('testing.agents.new') }}
          </v-btn>
        </v-col>
        <v-spacer />
      </v-row>
    </v-sheet>

    <!-- Table -->
    <v-card class="mt-4" elevation="1">
      <v-data-table
        :headers="headers"
        :items="filteredItems"
        :loading="loading"
        hover
      >
        <template v-slot:item.status="{ item }">
          <v-chip :color="getStatusColor(item.status)" size="small" variant="flat" class="font-weight-medium">
            {{ $t(`testing.agents.${item.status}`) }}
          </v-chip>
        </template>

        <template v-slot:item.labels="{ item }">
          <v-chip v-for="label in (item.labels || [])" :key="label" size="x-small" class="mr-1" variant="outlined">
            {{ label }}
          </v-chip>
        </template>

        <template v-slot:item.actions="{ item }">
          <div class="d-flex align-center">
            <v-tooltip location="top" :text="$t('testing.agents.ping')">
              <template v-slot:activator="{ props }">
                <v-btn v-bind="props" icon="mdi-access-point" variant="text" color="info" size="small" @click="pingMachine(item)" :loading="item._pinging" />
              </template>
            </v-tooltip>
            <v-tooltip location="top" :text="$t('common.edit')">
              <template v-slot:activator="{ props }">
                <v-btn v-bind="props" icon="mdi-pencil-outline" variant="text" color="primary" size="small" @click="openDialog(item)" />
              </template>
            </v-tooltip>
            <v-tooltip location="top" :text="$t('common.delete')">
              <template v-slot:activator="{ props }">
                <v-btn v-bind="props" icon="mdi-delete-outline" variant="text" color="error" size="small" @click="deleteItem(item)" />
              </template>
            </v-tooltip>
          </div>
        </template>

        <template v-slot:no-data>
          <v-empty-state icon="mdi-server-off" :title="$t('common.noData')" class="py-10" />
        </template>
      </v-data-table>
    </v-card>

    <!-- Delete Confirm Dialog -->
    <v-dialog v-model="deleteConfirmDialog" max-width="400">
      <v-card class="rounded-xl">
        <v-toolbar color="error" density="compact">
          <v-toolbar-title class="text-subtitle-1 font-weight-bold">{{ $t('common.delete') }}</v-toolbar-title>
        </v-toolbar>
        <v-card-text class="pa-4">{{ $t('common.confirmDelete', { name: deleteTarget?.name }) }}</v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="deleteConfirmDialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="error" variant="flat" @click="confirmDeleteItem">{{ $t('common.delete') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Create/Edit Dialog -->
    <v-dialog v-model="dialog" max-width="650px">
      <v-card class="rounded-xl">
        <v-toolbar color="primary" density="compact">
          <v-toolbar-title class="text-subtitle-1 font-weight-bold">{{ form.id ? $t('testing.agents.edit') : $t('testing.agents.new') }}</v-toolbar-title>
          <v-spacer />
          <v-btn icon="mdi-close" variant="text" @click="dialog = false" />
        </v-toolbar>

        <v-card-text class="pa-6">
          <v-form ref="formRef" @submit.prevent="saveItem">
            <v-text-field v-model="form.name" :label="$t('testing.agents.fields.name')" variant="outlined" density="compact" class="mb-3" :rules="[v => !!v || $t('common.required')]" />
            <v-row>
              <v-col cols="8">
                <v-text-field v-model="form.hostname" :label="$t('testing.agents.fields.hostname')" variant="outlined" density="compact" />
              </v-col>
              <v-col cols="4">
                <v-select v-model="form.os_type" :items="osOptions" :label="$t('testing.agents.fields.osType')" variant="outlined" density="compact" />
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="8">
                <v-text-field v-model="form.ip_address" :label="$t('testing.agents.fields.ipAddress')" variant="outlined" density="compact" :rules="[v => !!v || $t('common.required')]" />
              </v-col>
              <v-col cols="4">
                <v-text-field v-model.number="form.port" :label="$t('testing.agents.fields.port')" variant="outlined" density="compact" type="number" />
              </v-col>
            </v-row>
            <v-text-field v-model="form.jenkins_node_name" :label="$t('testing.agents.fields.jenkinsNodeName')" variant="outlined" density="compact" class="mb-3" />
            <v-combobox v-model="form.labels" :label="$t('testing.agents.fields.labels')" variant="outlined" density="compact" multiple chips closable-chips class="mb-3" />
            <v-textarea v-model="form.description" :label="$t('testing.agents.fields.description')" variant="outlined" density="compact" rows="2" class="mb-3" />

            <!-- Jenkins Configuration -->
            <v-divider class="my-4" />
            <div class="text-subtitle-2 font-weight-bold mb-2">Jenkins</div>
            <v-text-field v-model="form.jenkins_url" :label="$t('testing.agents.fields.jenkinsUrl')" variant="outlined" density="compact" class="mb-2" placeholder="http://127.0.0.1:8080" />
            <v-row>
              <v-col cols="6">
                <v-text-field v-model="form.jenkins_username" :label="$t('testing.agents.fields.jenkinsUsername')" variant="outlined" density="compact" />
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model="form.jenkins_token"
                  :label="$t('testing.agents.fields.jenkinsToken')"
                  variant="outlined"
                  density="compact"
                  type="password"
                  :placeholder="form.id && form.has_jenkins_token ? '●●●●●● (已配置，留空不修改)' : ''"
                  :hint="form.id && form.has_jenkins_token ? '留空表示不修改' : ''"
                  persistent-hint
                />
              </v-col>
            </v-row>
            <v-btn
              v-if="form.jenkins_url"
              variant="tonal"
              color="info"
              size="small"
              prepend-icon="mdi-connection"
              class="text-none mt-1"
              :loading="testingJenkins"
              @click="testJenkins"
            >
              {{ $t('testing.agents.fields.testConnection') }}
            </v-btn>
            <v-alert v-if="jenkinsTestResult" :type="jenkinsTestResult.ok ? 'success' : 'error'" variant="tonal" density="compact" class="mt-2 text-caption" closable @click:close="jenkinsTestResult = null">
              {{ jenkinsTestResult.message }}
            </v-alert>
          </v-form>
        </v-card-text>

        <v-divider />
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" color="grey-darken-1" @click="dialog = false" class="px-6 rounded-lg">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="primary" variant="flat" @click="saveItem" :loading="saving" class="px-6 rounded-lg ml-2">{{ $t('common.save') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useSnackbarStore } from '@/store/snackbar'
import {
  getExecutorMachines, createExecutorMachine, updateExecutorMachine,
  deleteExecutorMachine, pingExecutorMachine, testJenkinsConnection,
} from '@/api/testing'

const { t } = useI18n()
const snackbar = useSnackbarStore()

const loading = ref(false)
const saving = ref(false)
const search = ref('')
const statusFilter = ref(null)
const dialog = ref(false)
const formRef = ref<any>(null)
const items = ref<any[]>([])

const form = ref<any>({})
const testingJenkins = ref(false)
const jenkinsTestResult = ref<{ ok: boolean; message: string } | null>(null)

const headers = computed(() => [
  { title: t('testing.agents.fields.name'), key: 'name', align: 'start' as const },
  { title: t('testing.agents.fields.ipAddress'), key: 'ip_address' },
  { title: t('testing.agents.fields.port'), key: 'port', width: 80 },
  { title: t('testing.agents.fields.osType'), key: 'os_type', width: 100 },
  { title: t('testing.agents.fields.labels'), key: 'labels' },
  { title: t('testing.agents.fields.status'), key: 'status', width: 100 },
  { title: t('common.actions'), key: 'actions', sortable: false, align: 'end' as const, width: 150 },
])

const statusOptions = computed(() => [
  { title: t('testing.agents.online'), value: 'online' },
  { title: t('testing.agents.offline'), value: 'offline' },
  { title: t('testing.agents.busy'), value: 'busy' },
])

const osOptions = [
  { title: 'Linux', value: 'linux' },
  { title: 'Windows', value: 'windows' },
  { title: 'macOS', value: 'macos' },
]

const filteredItems = computed(() => {
  return items.value.filter(item => {
    const matchesSearch = !search.value || item.name.toLowerCase().includes(search.value.toLowerCase()) || item.ip_address.includes(search.value)
    const matchesStatus = !statusFilter.value || item.status === statusFilter.value
    return matchesSearch && matchesStatus
  })
})

const getStatusColor = (s: string) => ({ online: 'success', offline: 'grey', busy: 'warning' }[s] || 'grey')

const loadData = async () => {
  loading.value = true
  try {
    const res = await getExecutorMachines({ no_page: true })
    items.value = (Array.isArray(res) ? res : []).map((i: any) => ({ ...i, _pinging: false }))
  } catch (e) { console.error(e) }
  loading.value = false
}

const openDialog = (item?: any) => {
  if (item) {
    form.value = { ...item, jenkins_token: '' }
  } else {
    form.value = { name: '', hostname: '', ip_address: '', port: 22, os_type: 'linux', labels: [], description: '', jenkins_node_name: '', jenkins_url: '', jenkins_username: '', jenkins_token: '' }
  }
  jenkinsTestResult.value = null
  dialog.value = true
}

const testJenkins = async () => {
  if (!form.value.id) {
    jenkinsTestResult.value = { ok: false, message: '请先保存执行机后再测试 Jenkins 连接' }
    return
  }
  testingJenkins.value = true
  jenkinsTestResult.value = null
  try {
    const res = await testJenkinsConnection(form.value.id)
    jenkinsTestResult.value = { ok: res.status === 'ok', message: res.version ? `连接成功 (v${res.version})` : (res.message || '连接失败') }
  } catch (e: any) {
    jenkinsTestResult.value = { ok: false, message: e?.message || '连接失败' }
  }
  testingJenkins.value = false
}

const saveItem = async () => {
  const { valid } = await formRef.value.validate()
  if (!valid) return
  saving.value = true
  try {
    const data = { ...form.value }
    if (data.id && !data.jenkins_token) {
      delete data.jenkins_token
    }
    delete data.has_jenkins_token
    delete data._pinging

    if (data.id) {
      await updateExecutorMachine(data.id, data)
    } else {
      await createExecutorMachine(data)
    }
    dialog.value = false
    snackbar.notify(t('common.success'), 'success')
    loadData()
  } catch (e: any) {
    snackbar.notify(e?.message || t('common.error'), 'error')
  }
  saving.value = false
}

const deleteConfirmDialog = ref(false)
const deleteTarget = ref<any>(null)

const deleteItem = (item: any) => {
  deleteTarget.value = item
  deleteConfirmDialog.value = true
}

const confirmDeleteItem = async () => {
  deleteConfirmDialog.value = false
  if (!deleteTarget.value) return
  try {
    await deleteExecutorMachine(deleteTarget.value.id)
    snackbar.notify(t('common.success'), 'success')
    loadData()
  } catch (e: any) {
    snackbar.notify(e?.message || t('common.error'), 'error')
  }
}

const pingMachine = async (item: any) => {
  item._pinging = true
  try {
    const res = await pingExecutorMachine(item.id)
    item.status = res.status
    snackbar.notify(`${item.name}: ${res.status} - ${res.message}`, res.status === 'online' ? 'success' : 'warning')
  } catch (e: any) {
    snackbar.notify(e?.message || 'Ping failed', 'error')
  }
  item._pinging = false
}

onMounted(loadData)
</script>

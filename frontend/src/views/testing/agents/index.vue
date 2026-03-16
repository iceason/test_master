<template>
  <v-container fluid>
    <!-- Top bar -->
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
            rounded="lg"
            elevation="2"
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

    <!-- Create/Edit Dialog -->
    <v-dialog v-model="dialog" max-width="650px">
      <v-card class="rounded-xl">
        <v-card-title class="pa-4 bg-primary text-white d-flex align-center justify-space-between">
          <span class="text-subtitle-1 font-weight-bold">{{ form.id ? $t('testing.agents.edit') : $t('testing.agents.new') }}</span>
          <v-btn icon="mdi-close" variant="text" color="white" density="compact" @click="dialog = false" />
        </v-card-title>

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
            <v-textarea v-model="form.description" :label="$t('testing.agents.fields.description')" variant="outlined" density="compact" rows="2" />
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
  deleteExecutorMachine, pingExecutorMachine
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
  form.value = item ? { ...item } : { name: '', hostname: '', ip_address: '', port: 22, os_type: 'linux', labels: [], description: '', jenkins_node_name: '' }
  dialog.value = true
}

const saveItem = async () => {
  const { valid } = await formRef.value.validate()
  if (!valid) return
  saving.value = true
  try {
    if (form.value.id) {
      await updateExecutorMachine(form.value.id, form.value)
    } else {
      await createExecutorMachine(form.value)
    }
    dialog.value = false
    snackbar.notify(t('common.success'), 'success')
    loadData()
  } catch (e: any) {
    snackbar.notify(e?.message || t('common.error'), 'error')
  }
  saving.value = false
}

const deleteItem = async (item: any) => {
  if (!confirm(t('common.confirmDelete', { name: item.name }))) return
  try {
    await deleteExecutorMachine(item.id)
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

<template>
  <v-container fluid>
    <!-- Top bar -->
    <v-sheet class="pa-4 rounded-xl border-thin" elevation="0" color="surface">
      <v-row dense align="center">
        <v-col cols="12" md="4">
          <v-text-field v-model="search" :placeholder="$t('common.search')" prepend-inner-icon="mdi-magnify" variant="outlined" density="compact" hide-details bg-color="background" class="rounded-lg" />
        </v-col>
        <v-col cols="12" md="3">
          <v-select v-model="statusFilter" :items="statusOptions" :placeholder="$t('testing.plans.fields.status')" variant="outlined" density="compact" hide-details bg-color="background" class="rounded-lg" clearable />
        </v-col>
        <v-col cols="12" md="2">
          <v-btn color="primary" prepend-icon="mdi-plus" @click="openDialog()" class="text-none font-weight-bold w-100" rounded="lg" elevation="2">
            {{ $t('testing.plans.new') }}
          </v-btn>
        </v-col>
        <v-spacer />
      </v-row>
    </v-sheet>

    <!-- Table -->
    <v-card class="mt-4" elevation="1">
      <v-data-table :headers="headers" :items="filteredItems" :loading="loading" hover @click:row="(_e: any, { item }: any) => goToDetail(item)">
        <template v-slot:item.is_cron_enabled="{ item }">
          <v-chip v-if="item.is_cron_enabled" color="info" size="small" variant="flat">
            <v-icon start size="14">mdi-clock-outline</v-icon>
            {{ item.cron_expression }}
          </v-chip>
          <span v-else class="text-grey">-</span>
        </template>

        <template v-slot:item.status="{ item }">
          <v-chip :color="item.status === 'active' ? 'success' : 'grey'" size="small" variant="flat">
            {{ $t(`testing.plans.status.${item.status}`) }}
          </v-chip>
        </template>

        <template v-slot:item.last_execution_status="{ item }">
          <v-chip v-if="item.last_execution_status" :color="getExecStatusColor(item.last_execution_status.status)" size="small" variant="flat">
            {{ $t(`testing.executions.status.${item.last_execution_status.status}`) }}
          </v-chip>
          <span v-else class="text-grey">-</span>
        </template>

        <template v-slot:item.actions="{ item }">
          <div class="d-flex align-center" @click.stop>
            <v-tooltip location="top" :text="$t('testing.plans.trigger')">
              <template v-slot:activator="{ props }">
                <v-btn v-bind="props" icon="mdi-play-circle-outline" variant="text" color="success" size="small" @click="triggerBuild(item)" :loading="item._triggering" />
              </template>
            </v-tooltip>
            <v-tooltip location="top" :text="$t('testing.plans.copyTriggerUrl')">
              <template v-slot:activator="{ props }">
                <v-btn v-bind="props" icon="mdi-link-variant" variant="text" color="info" size="small" @click="copyTriggerUrl(item)" />
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
          <v-empty-state icon="mdi-clipboard-text-off-outline" :title="$t('common.noData')" class="py-10" />
        </template>
      </v-data-table>
    </v-card>

    <!-- Create/Edit Dialog -->
    <v-dialog v-model="dialog" max-width="800px" scrollable>
      <v-card class="rounded-xl">
        <v-card-title class="pa-4 bg-primary text-white d-flex align-center justify-space-between">
          <span class="text-subtitle-1 font-weight-bold">{{ form.id ? $t('testing.plans.edit') : $t('testing.plans.new') }}</span>
          <v-btn icon="mdi-close" variant="text" color="white" density="compact" @click="dialog = false" />
        </v-card-title>

        <v-card-text class="pa-6" style="max-height: 70vh;">
          <v-form ref="formRef" @submit.prevent="saveItem">
            <!-- Basic Info -->
            <div class="text-subtitle-2 font-weight-bold mb-2">{{ $t('testing.plans.fields.name') }}</div>
            <v-text-field v-model="form.name" variant="outlined" density="compact" class="mb-3" :rules="[v => !!v || $t('common.required')]" />
            <v-textarea v-model="form.description" :label="$t('testing.plans.fields.description')" variant="outlined" density="compact" rows="2" class="mb-3" />

            <v-row>
              <v-col cols="6">
                <v-select v-model="form.executor_machine" :items="machines" item-title="name" item-value="id" :label="$t('testing.plans.fields.executorMachine')" variant="outlined" density="compact" clearable />
              </v-col>
              <v-col cols="6">
                <v-select v-model="form.environment" :items="environments" item-title="name" item-value="id" :label="$t('testing.plans.fields.environment')" variant="outlined" density="compact" clearable />
              </v-col>
            </v-row>

            <!-- Jenkins Config -->
            <v-divider class="my-4" />
            <div class="text-subtitle-2 font-weight-bold mb-2">Jenkins</div>
            <v-text-field v-model="form.jenkins_server_url" :label="$t('testing.plans.fields.jenkinsServerUrl')" variant="outlined" density="compact" class="mb-2" placeholder="https://jenkins.example.com" />
            <v-text-field v-model="form.jenkins_job_name" :label="$t('testing.plans.fields.jenkinsJobName')" variant="outlined" density="compact" class="mb-2" />
            <v-row>
              <v-col cols="6">
                <v-text-field v-model="jenkinsUsername" :label="$t('testing.plans.fields.jenkinsUsername')" variant="outlined" density="compact" />
              </v-col>
              <v-col cols="6">
                <v-text-field v-model="jenkinsToken" :label="$t('testing.plans.fields.jenkinsToken')" variant="outlined" density="compact" type="password" />
              </v-col>
            </v-row>

            <!-- Cron -->
            <v-divider class="my-4" />
            <div class="d-flex align-center mb-2">
              <v-switch v-model="form.is_cron_enabled" :label="$t('testing.plans.fields.isCronEnabled')" color="primary" density="compact" hide-details class="mr-4" />
            </div>
            <v-text-field v-if="form.is_cron_enabled" v-model="form.cron_expression" :label="$t('testing.plans.fields.cronExpression')" variant="outlined" density="compact" placeholder="0 2 * * *" hint="minute hour day month weekday" persistent-hint class="mb-3" />

            <!-- Notification -->
            <v-divider class="my-4" />
            <div class="text-subtitle-2 font-weight-bold mb-2">{{ $t('testing.notification.title') }}</div>
            <v-row>
              <v-col cols="12">
                <v-switch v-model="notifyEmail" :label="$t('testing.notification.email')" color="primary" density="compact" hide-details />
                <v-text-field v-if="notifyEmail" v-model="emailRecipients" :label="$t('testing.notification.emailRecipients')" variant="outlined" density="compact" class="mt-2" hint="Comma-separated emails" persistent-hint />
              </v-col>
              <v-col cols="12">
                <v-switch v-model="notifyWebhook" :label="$t('testing.notification.webhook')" color="primary" density="compact" hide-details />
                <template v-if="notifyWebhook">
                  <v-text-field v-model="webhookUrl" :label="$t('testing.notification.webhookUrl')" variant="outlined" density="compact" class="mt-2" />
                  <v-select v-model="webhookType" :items="webhookTypes" :label="$t('testing.notification.webhookType')" variant="outlined" density="compact" class="mt-2" />
                </template>
              </v-col>
            </v-row>

            <!-- Build Steps -->
            <v-divider class="my-4" />
            <div class="d-flex align-center justify-space-between mb-2">
              <div class="text-subtitle-2 font-weight-bold">{{ $t('testing.steps.title') }}</div>
              <v-btn size="small" color="primary" variant="tonal" prepend-icon="mdi-plus" @click="addStep" class="text-none">{{ $t('testing.steps.add') }}</v-btn>
            </div>
            <v-card v-for="(step, idx) in form.steps" :key="idx" variant="outlined" class="pa-3 mb-3">
              <v-row dense align="center">
                <v-col cols="1" class="text-center text-grey font-weight-bold">{{ idx + 1 }}</v-col>
                <v-col cols="4">
                  <v-text-field v-model="step.name" :label="$t('testing.steps.name')" variant="outlined" density="compact" hide-details />
                </v-col>
                <v-col cols="2">
                  <v-text-field v-model.number="step.timeout" :label="$t('testing.steps.timeout')" variant="outlined" density="compact" hide-details type="number" />
                </v-col>
                <v-col cols="3">
                  <v-select v-model="step.on_failure" :items="failureOptions" :label="$t('testing.steps.onFailure')" variant="outlined" density="compact" hide-details />
                </v-col>
                <v-col cols="2" class="text-right">
                  <v-btn icon="mdi-chevron-up" size="x-small" variant="text" :disabled="idx === 0" @click="moveStep(idx, -1)" />
                  <v-btn icon="mdi-chevron-down" size="x-small" variant="text" :disabled="idx === form.steps.length - 1" @click="moveStep(idx, 1)" />
                  <v-btn icon="mdi-close" size="x-small" variant="text" color="error" @click="removeStep(idx)" />
                </v-col>
                <v-col cols="11" offset="1">
                  <v-textarea v-model="step.script" :label="$t('testing.steps.script')" variant="outlined" density="compact" rows="2" hide-details class="mt-1 code-font" />
                </v-col>
              </v-row>
            </v-card>

            <v-select v-model="form.status" :items="planStatusOptions" :label="$t('testing.plans.fields.status')" variant="outlined" density="compact" class="mt-3" />
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
import { useRouter } from 'vue-router'
import { useSnackbarStore } from '@/store/snackbar'
import { getBuildPlans, createBuildPlan, updateBuildPlan, deleteBuildPlan, triggerBuildPlan } from '@/api/testing'
import { getExecutorMachines } from '@/api/testing'
import { getEnvironments } from '@/api/execution'

const { t } = useI18n()
const router = useRouter()
const snackbar = useSnackbarStore()

const loading = ref(false)
const saving = ref(false)
const search = ref('')
const statusFilter = ref(null)
const dialog = ref(false)
const formRef = ref<any>(null)
const items = ref<any[]>([])
const machines = ref<any[]>([])
const environments = ref<any[]>([])

// Notification helpers
const notifyEmail = ref(false)
const emailRecipients = ref('')
const notifyWebhook = ref(false)
const webhookUrl = ref('')
const webhookType = ref('dingtalk')
const jenkinsUsername = ref('')
const jenkinsToken = ref('')

const form = ref<any>({ steps: [] })

const headers = computed(() => [
  { title: t('testing.plans.fields.name'), key: 'name', align: 'start' as const },
  { title: 'Jenkins Job', key: 'jenkins_job_name' },
  { title: t('testing.plans.fields.isCronEnabled'), key: 'is_cron_enabled' },
  { title: t('testing.plans.fields.stepCount'), key: 'step_count', width: 80 },
  { title: t('testing.plans.fields.lastExecution'), key: 'last_execution_status' },
  { title: t('testing.plans.fields.status'), key: 'status', width: 100 },
  { title: t('common.actions'), key: 'actions', sortable: false, align: 'end' as const, width: 200 },
])

const statusOptions = computed(() => [
  { title: t('testing.plans.status.active'), value: 'active' },
  { title: t('testing.plans.status.disabled'), value: 'disabled' },
])
const planStatusOptions = [
  { title: 'Active', value: 'active' },
  { title: 'Disabled', value: 'disabled' },
]
const failureOptions = [
  { title: 'Stop', value: 'stop' },
  { title: 'Continue', value: 'continue' },
  { title: 'Retry', value: 'retry' },
]
const webhookTypes = [
  { title: 'DingTalk', value: 'dingtalk' },
  { title: 'Feishu', value: 'feishu' },
  { title: 'WeChat Work', value: 'wechat' },
]

const filteredItems = computed(() => {
  return items.value.filter(item => {
    const matchSearch = !search.value || item.name.toLowerCase().includes(search.value.toLowerCase())
    const matchStatus = !statusFilter.value || item.status === statusFilter.value
    return matchSearch && matchStatus
  })
})

const getExecStatusColor = (s: string) => ({ pending: 'grey', running: 'info', success: 'success', failed: 'error', cancelled: 'warning' }[s] || 'grey')

const loadData = async () => {
  loading.value = true
  try {
    const [plansRes, machinesRes, envRes] = await Promise.all([
      getBuildPlans({ no_page: true }), getExecutorMachines({ no_page: true }), getEnvironments({ no_page: true }),
    ])
    items.value = (Array.isArray(plansRes) ? plansRes : []).map((i: any) => ({ ...i, _triggering: false }))
    machines.value = Array.isArray(machinesRes) ? machinesRes : []
    environments.value = Array.isArray(envRes) ? envRes : []
  } catch (e) { console.error(e) }
  loading.value = false
}

const openDialog = (item?: any) => {
  if (item) {
    form.value = { ...item, steps: item.steps ? [...item.steps] : [] }
    const nc = item.notification_config || {}
    notifyEmail.value = nc.email?.enabled || false
    emailRecipients.value = (nc.email?.recipients || []).join(', ')
    notifyWebhook.value = nc.webhook?.enabled || false
    webhookUrl.value = nc.webhook?.url || ''
    webhookType.value = nc.webhook?.type || 'dingtalk'
    const creds = item.jenkins_credentials || {}
    jenkinsUsername.value = creds.username || ''
    jenkinsToken.value = creds.token || ''
  } else {
    form.value = { name: '', description: '', executor_machine: null, environment: null, jenkins_server_url: '', jenkins_job_name: '', cron_expression: '', is_cron_enabled: false, status: 'active', steps: [] }
    notifyEmail.value = false; emailRecipients.value = ''; notifyWebhook.value = false; webhookUrl.value = ''; webhookType.value = 'dingtalk'
    jenkinsUsername.value = ''; jenkinsToken.value = ''
  }
  dialog.value = true
}

const addStep = () => {
  form.value.steps.push({ name: '', script: '', timeout: 3600, on_failure: 'stop' })
}
const removeStep = (idx: number) => { form.value.steps.splice(idx, 1) }
const moveStep = (idx: number, dir: number) => {
  const arr = form.value.steps
  const target = idx + dir
  ;[arr[idx], arr[target]] = [arr[target], arr[idx]]
}

const saveItem = async () => {
  const { valid } = await formRef.value.validate()
  if (!valid) return
  saving.value = true
  try {
    // Build notification_config and jenkins_credentials
    const data = {
      ...form.value,
      jenkins_credentials: { username: jenkinsUsername.value, token: jenkinsToken.value },
      notification_config: {
        email: { enabled: notifyEmail.value, recipients: emailRecipients.value.split(',').map((s: string) => s.trim()).filter(Boolean) },
        webhook: { enabled: notifyWebhook.value, url: webhookUrl.value, type: webhookType.value },
      },
      steps: form.value.steps.map((s: any, i: number) => ({ ...s, order: i })),
    }
    if (form.value.id) {
      await updateBuildPlan(form.value.id, data)
    } else {
      await createBuildPlan(data)
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
    await deleteBuildPlan(item.id)
    snackbar.notify(t('common.success'), 'success')
    loadData()
  } catch (e: any) { snackbar.notify(e?.message || t('common.error'), 'error') }
}

const triggerBuild = async (item: any) => {
  if (!confirm(t('testing.plans.triggerConfirm'))) return
  item._triggering = true
  try {
    await triggerBuildPlan(item.id)
    snackbar.notify(t('common.success'), 'success')
    loadData()
  } catch (e: any) { snackbar.notify(e?.message || t('common.error'), 'error') }
  item._triggering = false
}

const copyTriggerUrl = (item: any) => {
  const url = `${window.location.origin}/api/build-trigger/${item.trigger_token}/`
  navigator.clipboard.writeText(url)
  snackbar.notify(t('testing.plans.triggerUrlCopied'), 'success')
}

const goToDetail = (item: any) => {
  router.push({ name: 'BuildPlanDetail', params: { id: item.id } })
}

onMounted(loadData)
</script>

<style scoped>
.code-font :deep(textarea) {
  font-family: 'Fira Code', 'Courier New', monospace;
  font-size: 13px;
}
</style>

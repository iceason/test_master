<template>
  <v-container fluid>
    <!-- 页头 + 操作栏 -->
    <v-sheet class="pa-4 rounded-xl border-thin" elevation="0" color="surface">
      <v-row dense align="center" class="mb-3">
        <v-col>
          <div class="d-flex align-center">
            <v-avatar color="primary" variant="tonal" size="40" class="mr-3">
              <v-icon icon="mdi-clipboard-flow-outline" size="22"></v-icon>
            </v-avatar>
            <div>
              <div class="text-h6 font-weight-bold">{{ $t('testing.plans.title') }}</div>
              <div class="text-caption text-medium-emphasis">
                {{ $t('testing.plans.subtitle') }}
              </div>
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
            :placeholder="$t('testing.plans.fields.status')"
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
            class="text-none font-weight-bold w-100"
            @click="openDialog()"
          >
            {{ $t('testing.plans.new') }}
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
        @click:row="(_e: any, { item }: any) => goToDetail(item)"
      >
        <template #[`item.is_cron_enabled`]="{ item }">
          <v-chip v-if="item.is_cron_enabled" color="info" size="small" variant="flat">
            <v-icon start size="14">mdi-clock-outline</v-icon>
            {{ item.cron_expression }}
          </v-chip>
          <span v-else class="text-medium-emphasis">-</span>
        </template>

        <template #[`item.status`]="{ item }">
          <v-chip
            :color="item.status === 'active' ? 'success' : 'grey'"
            size="small"
            variant="flat"
          >
            {{ $t(`testing.plans.status.${item.status}`) }}
          </v-chip>
        </template>

        <template #[`item.last_execution_status`]="{ item }">
          <div v-if="item.last_execution_status" class="d-flex align-center ga-2">
            <v-chip
              :color="getExecStatusColor(item.last_execution_status.status)"
              size="small"
              variant="flat"
            >
              {{ $t(`testing.executions.status.${item.last_execution_status.status}`) }}
            </v-chip>
            <span class="text-caption text-medium-emphasis">{{
              formatTime(item.last_execution_status.started_at)
            }}</span>
          </div>
          <span v-else class="text-medium-emphasis">-</span>
        </template>

        <template #[`item.actions`]="{ item }">
          <div class="d-flex align-center" @click.stop>
            <v-tooltip
              location="top"
              :text="isRunning(item) ? $t('testing.plans.stopBuild') : $t('testing.plans.trigger')"
            >
              <template #activator="{ props }">
                <v-btn
                  v-bind="props"
                  :icon="isRunning(item) ? 'mdi-stop-circle-outline' : 'mdi-play-circle-outline'"
                  variant="text"
                  :color="isRunning(item) ? 'error' : 'teal'"
                  size="small"
                  :loading="item._triggering || item._stopping"
                  @click="isRunning(item) ? stopBuild(item) : triggerBuild(item)"
                />
              </template>
            </v-tooltip>
            <v-tooltip location="top" :text="$t('testing.plans.copyTriggerUrl')">
              <template #activator="{ props }">
                <v-btn
                  v-bind="props"
                  icon="mdi-link-variant"
                  variant="text"
                  color="info"
                  size="small"
                  @click="copyTriggerUrl(item)"
                />
              </template>
            </v-tooltip>
            <v-tooltip location="top" :text="$t('common.edit')">
              <template #activator="{ props }">
                <v-btn
                  v-bind="props"
                  icon="mdi-pencil-outline"
                  variant="text"
                  color="primary"
                  size="small"
                  @click="openDialog(item)"
                />
              </template>
            </v-tooltip>
            <v-tooltip location="top" :text="$t('common.delete')">
              <template #activator="{ props }">
                <v-btn
                  v-bind="props"
                  icon="mdi-delete-outline"
                  variant="text"
                  color="error"
                  size="small"
                  @click="deleteItem(item)"
                />
              </template>
            </v-tooltip>
          </div>
        </template>

        <template #no-data>
          <v-empty-state
            icon="mdi-clipboard-text-off-outline"
            :title="$t('common.noData')"
            class="py-10"
          />
        </template>
      </v-data-table>
    </v-card>

    <!-- Create/Edit Dialog (fullscreen) -->
    <v-dialog v-model="dialog" fullscreen transition="dialog-bottom-transition">
      <v-card class="d-flex flex-column" style="height: 100vh">
        <!-- Top toolbar -->
        <v-toolbar color="primary" density="comfortable" class="flex-grow-0">
          <v-btn icon="mdi-close" variant="text" @click="dialog = false" />
          <v-toolbar-title class="text-subtitle-1 font-weight-bold">
            {{ form.id ? $t('testing.plans.edit') : $t('testing.plans.new') }}
          </v-toolbar-title>
          <v-spacer />
          <v-btn variant="text" class="text-none mr-2" @click="dialog = false">{{
            $t('common.cancel')
          }}</v-btn>
          <v-btn
            variant="flat"
            color="white"
            class="text-none text-primary font-weight-bold"
            prepend-icon="mdi-content-save"
            :loading="saving"
            @click="saveItem"
            >{{ $t('common.save') }}</v-btn
          >
        </v-toolbar>

        <!-- Body: left config + right pipeline -->
        <div class="d-flex flex-grow-1" style="overflow: hidden">
          <!-- Left config panel (420px) -->
          <div
            class="left-config-panel border-e"
            style="width: 420px; min-width: 420px; overflow-y: auto"
          >
            <v-form ref="formRef" @submit.prevent="saveItem">
              <v-expansion-panels v-model="expandedPanels" multiple variant="accordion">
                <!-- Basic Info -->
                <v-expansion-panel value="basic">
                  <v-expansion-panel-title class="font-weight-medium">
                    {{ $t('testing.plans.fields.name') }}
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <v-text-field
                      v-model="form.name"
                      :label="$t('testing.plans.fields.name')"
                      variant="outlined"
                      density="compact"
                      class="mb-3"
                      :rules="[(v) => !!v || $t('common.required')]"
                    />
                    <v-textarea
                      v-model="form.description"
                      :label="$t('testing.plans.fields.description')"
                      variant="outlined"
                      density="compact"
                      rows="2"
                      class="mb-3"
                    />
                    <v-select
                      v-model="form.executor_machine"
                      :items="machines"
                      item-title="name"
                      item-value="id"
                      :label="$t('testing.plans.fields.executorMachine')"
                      variant="outlined"
                      density="compact"
                      clearable
                      class="mb-3"
                    />
                    <v-select
                      v-if="form.id"
                      v-model="form.status"
                      :items="planStatusOptions"
                      :label="$t('testing.plans.fields.status')"
                      variant="outlined"
                      density="compact"
                      class="mt-3"
                    />
                    <v-text-field
                      v-model.number="form.repeat_run_times"
                      :label="$t('testing.plans.fields.repeatRunTimes')"
                      type="number"
                      min="1"
                      max="20"
                      variant="outlined"
                      density="compact"
                      class="mt-3"
                      :hint="$t('testing.plans.fields.repeatRunTimesHint')"
                      persistent-hint
                    />
                    <v-select
                      v-model="form.repeat_failure_policy"
                      :items="repeatFailurePolicyOptions"
                      :label="$t('testing.plans.fields.repeatFailurePolicy')"
                      variant="outlined"
                      density="compact"
                      class="mt-3"
                    />
                  </v-expansion-panel-text>
                </v-expansion-panel>

                <!-- Source Code -->
                <v-expansion-panel value="source">
                  <v-expansion-panel-title class="font-weight-medium">
                    {{ $t('testing.plans.sections.sourceCode') }}
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <v-text-field
                      v-model="form.git_repo_url"
                      :label="$t('testing.plans.fields.gitRepoUrl')"
                      variant="outlined"
                      density="compact"
                      class="mb-3"
                      placeholder="https://github.com/user/repo.git"
                    />
                    <v-text-field
                      v-model="form.git_branch"
                      :label="$t('testing.plans.fields.gitBranch')"
                      variant="outlined"
                      density="compact"
                      class="mb-3"
                    />
                    <v-text-field
                      v-model="form.git_credential_id"
                      :label="$t('testing.plans.fields.gitCredentialId')"
                      variant="outlined"
                      density="compact"
                      class="mb-3"
                      :hint="$t('testing.plans.fields.gitCredentialIdHint')"
                      persistent-hint
                    />
                    <v-switch
                      v-model="form.workspace_cleanup"
                      :label="$t('testing.plans.fields.workspaceCleanup')"
                      color="primary"
                      density="compact"
                      hide-details
                    />
                  </v-expansion-panel-text>
                </v-expansion-panel>

                <!-- Environment Variables -->
                <v-expansion-panel value="envVars">
                  <v-expansion-panel-title class="font-weight-medium">
                    {{ $t('testing.plans.sections.envVars') }}
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <v-row
                      v-for="(ev, idx) in form.environment_variables"
                      :key="idx"
                      dense
                      class="mb-2"
                    >
                      <v-col cols="5">
                        <v-text-field
                          v-model="ev.key"
                          label="Key"
                          variant="outlined"
                          density="compact"
                          hide-details
                        />
                      </v-col>
                      <v-col cols="5">
                        <v-text-field
                          v-model="ev.value"
                          label="Value"
                          variant="outlined"
                          density="compact"
                          hide-details
                        />
                      </v-col>
                      <v-col cols="2" class="d-flex align-center">
                        <v-btn
                          icon="mdi-close"
                          size="x-small"
                          variant="text"
                          color="error"
                          @click="form.environment_variables.splice(idx, 1)"
                        />
                      </v-col>
                    </v-row>
                    <v-btn
                      size="small"
                      color="primary"
                      variant="tonal"
                      prepend-icon="mdi-plus"
                      class="text-none mt-2"
                      @click="form.environment_variables.push({ key: '', value: '' })"
                    >
                      {{ $t('testing.plans.addVariable') }}
                    </v-btn>
                  </v-expansion-panel-text>
                </v-expansion-panel>

                <!-- 定时任务 -->
                <v-expansion-panel value="cron">
                  <v-expansion-panel-title class="font-weight-medium">
                    {{ $t('testing.plans.cronField') }}
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <v-switch
                      v-model="form.is_cron_enabled"
                      :label="$t('testing.plans.fields.isCronEnabled')"
                      color="primary"
                      density="compact"
                      hide-details
                      class="mb-3"
                    />
                    <v-text-field
                      v-if="form.is_cron_enabled"
                      v-model="form.cron_expression"
                      :label="$t('testing.plans.fields.cronExpression')"
                      variant="outlined"
                      density="compact"
                      placeholder="0 2 * * *"
                      hint="minute hour day month weekday"
                      persistent-hint
                    />
                  </v-expansion-panel-text>
                </v-expansion-panel>

                <!-- Notification -->
                <v-expansion-panel value="notification">
                  <v-expansion-panel-title class="font-weight-medium">
                    {{ $t('testing.notification.title') }}
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <v-switch
                      v-model="notifyEmail"
                      :label="$t('testing.notification.email')"
                      color="primary"
                      density="compact"
                      hide-details
                      class="mb-3"
                    />
                    <v-combobox
                      v-if="notifyEmail"
                      v-model="emailRecipientsList"
                      :label="$t('testing.notification.emailRecipients')"
                      variant="outlined"
                      density="compact"
                      multiple
                      chips
                      closable-chips
                      :hint="$t('testing.plans.notification.emailHint')"
                      persistent-hint
                      class="mb-3"
                    />
                    <v-switch
                      v-model="notifyWebhook"
                      :label="$t('testing.notification.webhook')"
                      color="primary"
                      density="compact"
                      hide-details
                      class="mb-3"
                    />
                    <template v-if="notifyWebhook">
                      <div class="text-caption text-medium-emphasis mb-2">
                        {{ $t('testing.notification.webhookLegacyHint') }}
                      </div>
                      <v-text-field
                        v-model="webhookUrl"
                        :label="$t('testing.notification.webhookUrl')"
                        variant="outlined"
                        density="compact"
                        class="mb-2"
                      />
                      <v-select
                        v-model="webhookType"
                        :items="webhookTypes"
                        :label="$t('testing.notification.webhookType')"
                        variant="outlined"
                        density="compact"
                      />
                    </template>
                    <v-divider class="my-3" />
                    <v-switch
                      v-model="notifyDingTalk"
                      :label="$t('testing.notification.dingtalk')"
                      color="primary"
                      density="compact"
                      hide-details
                      class="mb-3"
                    />
                    <template v-if="notifyDingTalk">
                      <v-select
                        v-model="selectedDingTalkGroupIds"
                        :items="dingTalkGroups"
                        item-title="name"
                        item-value="id"
                        :label="$t('testing.notification.dingtalkGroups')"
                        variant="outlined"
                        density="compact"
                        multiple
                        chips
                        class="mb-2"
                      />
                      <v-select
                        v-model="selectedDingTalkTemplateId"
                        :items="dingTalkTemplates"
                        item-title="name"
                        item-value="id"
                        :label="$t('testing.notification.dingtalkTemplate')"
                        variant="outlined"
                        density="compact"
                        clearable
                      />
                    </template>
                  </v-expansion-panel-text>
                </v-expansion-panel>

                <!-- Report -->
                <v-expansion-panel value="report">
                  <v-expansion-panel-title class="font-weight-medium">
                    {{ $t('testing.plans.sections.reportConfig') }}
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <v-switch
                      v-model="form.report_enabled"
                      :label="$t('testing.plans.fields.reportEnabled')"
                      color="primary"
                      density="compact"
                      hide-details
                      class="mb-3"
                    />
                    <v-text-field
                      v-if="form.report_enabled"
                      v-model="form.report_results_dir"
                      :label="$t('testing.plans.fields.reportResultsDir')"
                      variant="outlined"
                      density="compact"
                      class="mb-3"
                      placeholder="allure-results"
                    />
                    <v-textarea
                      v-if="form.report_enabled"
                      v-model="form.report_command"
                      :label="$t('testing.plans.fields.reportCommand')"
                      variant="outlined"
                      density="compact"
                      rows="3"
                      class="code-font"
                    />
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>
            </v-form>
          </div>

          <!-- Right pipeline panel -->
          <div
            class="flex-grow-1 d-flex flex-column"
            style="overflow: hidden; background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%)"
          >
            <div class="pipeline-header">
              <div class="d-flex align-center">
                <span class="text-subtitle-2 font-weight-bold">{{
                  $t('testing.steps.title')
                }}</span>
                <v-chip size="x-small" color="primary" variant="tonal" class="ml-2" pill
                  >{{ form.steps.length }} {{ $t('testing.plans.stepsCount') }}</v-chip
                >
              </div>
              <v-btn-toggle
                v-model="editorMode"
                mandatory
                density="compact"
                color="primary"
                variant="outlined"
              >
                <v-btn value="visual" size="small" class="text-none">
                  <v-icon start size="16">mdi-drag-variant</v-icon
                  >{{ $t('testing.pipeline.visualEditor') }}
                </v-btn>
                <v-btn value="text" size="small" class="text-none">
                  <v-icon start size="16">mdi-code-braces</v-icon
                  >{{ $t('testing.pipeline.textEditor') }}
                </v-btn>
              </v-btn-toggle>
            </div>
            <div class="flex-grow-1 d-flex align-center" style="overflow: auto">
              <div v-if="editorMode === 'visual'" class="w-100">
                <PipelineEditor
                  v-model="form.steps"
                  :report-enabled="form.report_enabled"
                  :report-command-preview="form.report_command"
                  :machine-os-type="selectedMachineOs"
                />
              </div>
              <div v-else class="w-100 pa-4">
                <Codemirror
                  v-model="jenkinsfileText"
                  :style="{ height: 'calc(100vh - 180px)', fontSize: '13px' }"
                  :extensions="cmExtensions"
                  :tab-size="4"
                />
              </div>
            </div>
          </div>
        </div>
      </v-card>
    </v-dialog>

    <!-- Confirm Dialog -->
    <v-dialog v-model="confirmDialog" max-width="400">
      <v-card class="rounded-xl">
        <v-card-title :class="`bg-${confirmColor} pa-4 text-white d-flex align-center ga-2`">
          <v-icon color="white">{{ confirmIcon }}</v-icon>
          <span class="text-subtitle-1 font-weight-bold">{{ confirmTitle }}</span>
        </v-card-title>
        <v-card-text class="pa-4">{{ confirmMessage }}</v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="confirmDialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn
            :color="confirmColor"
            variant="flat"
            :prepend-icon="confirmIcon"
            @click="confirmAction"
            >{{ $t('common.confirm') }}</v-btn
          >
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useSnackbarStore } from '@/store/snackbar'
import {
  getBuildPlans,
  getBuildPlan,
  createBuildPlan,
  updateBuildPlan,
  deleteBuildPlan,
  triggerBuildPlan,
  stopBuildPlan,
  getExecutorMachines,
  getDingTalkGroups,
  getDingTalkTemplates,
  getBuildPlanJenkinsEnv,
} from '@/api/testing'
import { Codemirror } from 'vue-codemirror'
import { StreamLanguage } from '@codemirror/language'
import { groovy } from '@codemirror/legacy-modes/mode/groovy'
import PipelineEditor from './PipelineEditor.vue'
import {
  generateJenkinsfile,
  parseJenkinsfile,
  buildDefaultReportCommand,
  upsertJenkinsfileEnvironment,
} from './pipelineScript'

const { t } = useI18n()
const router = useRouter()
const snackbar = useSnackbarStore()

const cmExtensions = [StreamLanguage.define(groovy)]

const loading = ref(false)
const saving = ref(false)
const search = ref('')
const statusFilter = ref(null)
const dialog = ref(false)
const formRef = ref<any>(null)
const items = ref<any[]>([])
const machines = ref<any[]>([])
const dingTalkGroups = ref<any[]>([])
const dingTalkTemplates = ref<any[]>([])
const expandedPanels = ref(['basic'])
const editorMode = ref('visual')
const jenkinsfileText = ref('')

const notifyEmail = ref(false)
const emailRecipientsList = ref<string[]>([])
const notifyWebhook = ref(false)
const webhookUrl = ref('')
const webhookType = ref('dingtalk')
const notifyDingTalk = ref(false)
const selectedDingTalkGroupIds = ref<number[]>([])
const selectedDingTalkTemplateId = ref<number | null>(null)
const backendBaseUrl = ref('')

const selectedMachineOs = computed(() => {
  const m = machines.value.find((x: any) => x.id === form.value.executor_machine)
  return m?.os_type || 'linux'
})

const confirmDialog = ref(false)
const confirmTitle = ref('')
const confirmMessage = ref('')
const confirmColor = ref('teal')
const confirmIcon = ref('mdi-play-circle')
let confirmResolve: ((v: boolean) => void) | null = null

const form = ref<any>({
  steps: [],
  environment_variables: [],
  git_repo_url: '',
  git_branch: 'main',
  git_credential_id: '',
  workspace_cleanup: true,
  report_enabled: false,
  report_results_dir: 'allure-results',
  report_command: '',
  repeat_run_times: 1,
  repeat_failure_policy: 'continue_all',
  jenkinsfile_text: '',
})

const headers = computed(() => [
  { title: t('testing.plans.fields.name'), key: 'name', align: 'start' as const },
  { title: 'Jenkins Job', key: 'jenkins_job_name' },
  { title: t('testing.plans.fields.isCronEnabled'), key: 'is_cron_enabled' },
  { title: t('testing.plans.fields.stepCount'), key: 'step_count', width: 80 },
  {
    title: t('testing.plans.fields.repeatRunTimes'),
    key: 'repeat_run_times',
    width: 96,
    align: 'center' as const,
  },
  { title: t('testing.plans.fields.lastExecution'), key: 'last_execution_status' },
  { title: t('testing.plans.fields.status'), key: 'status', width: 100 },
  {
    title: t('common.actions'),
    key: 'actions',
    sortable: false,
    align: 'end' as const,
    width: 200,
  },
])

const statusOptions = computed(() => [
  { title: t('testing.plans.status.active'), value: 'active' },
  { title: t('testing.plans.status.disabled'), value: 'disabled' },
])
const planStatusOptions = computed(() => [
  { title: t('testing.plans.status.active'), value: 'active' },
  { title: t('testing.plans.status.disabled'), value: 'disabled' },
])
const repeatFailurePolicyOptions = computed(() => [
  { title: t('testing.plans.repeatFailurePolicy.continue_all'), value: 'continue_all' },
  { title: t('testing.plans.repeatFailurePolicy.stop_on_first_fail'), value: 'stop_on_first_fail' },
])
const webhookTypes = [
  { title: 'DingTalk', value: 'dingtalk' },
  { title: 'Feishu', value: 'feishu' },
  { title: 'WeChat Work', value: 'wechat' },
]

const filteredItems = computed(() => {
  return items.value.filter((item) => {
    const matchSearch =
      !search.value || item.name.toLowerCase().includes(search.value.toLowerCase())
    const matchStatus = !statusFilter.value || item.status === statusFilter.value
    return matchSearch && matchStatus
  })
})

const getExecStatusColor = (s: string) =>
  ({ pending: 'grey', running: 'info', success: 'success', failed: 'error', cancelled: 'warning' })[
    s
  ] || 'grey'

const isRunning = (item: any) => {
  const s = item.last_execution_status?.status
  return s === 'running' || s === 'pending'
}

const formatTime = (iso: string) => {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const showConfirm = (
  title: string,
  message: string,
  color = 'teal',
  icon = 'mdi-play-circle'
): Promise<boolean> => {
  return new Promise((resolve) => {
    confirmTitle.value = title
    confirmMessage.value = message
    confirmColor.value = color
    confirmIcon.value = icon
    confirmResolve = resolve
    confirmDialog.value = true
  })
}
const confirmAction = () => {
  confirmDialog.value = false
  confirmResolve?.(true)
}
watch(confirmDialog, (v) => {
  if (!v && confirmResolve) {
    confirmResolve(false)
    confirmResolve = null
  }
})

const loadData = async () => {
  loading.value = true
  try {
    const [plansRes, machinesRes, dingtalkGroupsRes, dingtalkTemplatesRes] = await Promise.all([
      getBuildPlans({ no_page: true }),
      getExecutorMachines({ no_page: true }),
      getDingTalkGroups({ no_page: true, is_active: true }),
      getDingTalkTemplates({ no_page: true, is_active: true }),
    ])
    items.value = (Array.isArray(plansRes) ? plansRes : []).map((i: any) => ({
      ...i,
      _triggering: false,
      _stopping: false,
    }))
    machines.value = Array.isArray(machinesRes) ? machinesRes : []
    dingTalkGroups.value = Array.isArray(dingtalkGroupsRes) ? dingtalkGroupsRes : []
    dingTalkTemplates.value = Array.isArray(dingtalkTemplatesRes) ? dingtalkTemplatesRes : []
  } catch (e) {
    console.error(e)
  }
  loading.value = false
}

const populateForm = (data: any) => {
  form.value = {
    ...data,
    steps: data.steps ? JSON.parse(JSON.stringify(data.steps)) : [],
    environment_variables: data.environment_variables
      ? JSON.parse(JSON.stringify(data.environment_variables))
      : [],
    git_repo_url: data.git_repo_url || '',
    git_branch: data.git_branch || 'main',
    git_credential_id: data.git_credential_id || '',
    workspace_cleanup: data.workspace_cleanup ?? true,
    report_enabled: data.report_enabled || false,
    report_results_dir: data.report_results_dir || 'allure-results',
    report_command: data.report_command || '',
    repeat_run_times: data.repeat_run_times || 1,
    repeat_failure_policy: data.repeat_failure_policy || 'continue_all',
    jenkinsfile_text: data.jenkinsfile_text || '',
  }
  const nc = data.notification_config || {}
  notifyEmail.value = nc.email?.enabled || false
  emailRecipientsList.value = nc.email?.recipients || []
  notifyWebhook.value = nc.webhook?.enabled || false
  webhookUrl.value = nc.webhook?.url || ''
  webhookType.value = nc.webhook?.type || 'dingtalk'
  notifyDingTalk.value = nc.dingtalk?.enabled || false
  selectedDingTalkGroupIds.value = Array.isArray(nc.dingtalk?.group_ids)
    ? nc.dingtalk.group_ids
    : []
  selectedDingTalkTemplateId.value = nc.dingtalk?.template_id ?? null
  jenkinsfileText.value = data.jenkinsfile_text || ''
  lastCleanText = jenkinsfileText.value
  textDirty.value = false
  visualDirty.value = false
}

const openDialog = async (item?: any) => {
  expandedPanels.value = ['basic']
  suppressDirtyWatch = true
  pendingEditorSwitch.value = true
  editorMode.value = 'visual'
  if (item) {
    populateForm(item)
    dialog.value = true
    try {
      const fullData = await getBuildPlan(item.id)
      populateForm(fullData)
    } catch (e) {
      console.error('Failed to load plan details:', e)
    }
  } else {
    form.value = {
      name: '',
      description: '',
      executor_machine: null,
      jenkins_job_name: '',
      cron_expression: '',
      is_cron_enabled: false,
      status: 'active',
      steps: [],
      environment_variables: [],
      git_repo_url: '',
      git_branch: 'main',
      git_credential_id: '',
      workspace_cleanup: true,
      report_enabled: false,
      report_command: '',
      report_results_dir: 'allure-results',
      repeat_run_times: 1,
      repeat_failure_policy: 'continue_all',
      jenkinsfile_text: '',
    }
    notifyEmail.value = false
    emailRecipientsList.value = []
    notifyWebhook.value = false
    webhookUrl.value = ''
    webhookType.value = 'dingtalk'
    notifyDingTalk.value = false
    selectedDingTalkGroupIds.value = []
    selectedDingTalkTemplateId.value = null
    jenkinsfileText.value = ''
    lastCleanText = ''
    textDirty.value = false
    visualDirty.value = false
    dialog.value = true
    try {
      const env = await getBuildPlanJenkinsEnv()
      if (env?.backend_base_url) backendBaseUrl.value = env.backend_base_url
    } catch (e) {
      console.error(e)
    }
  }
  nextTick(() => {
    suppressDirtyWatch = false
  })
}

const pendingEditorSwitch = ref(false)
const textDirty = ref(false)
const visualDirty = ref(false)
let lastCleanText = ''
let suppressDirtyWatch = false

watch(jenkinsfileText, (val) => {
  if (!suppressDirtyWatch && val !== lastCleanText) textDirty.value = true
})

watch(
  () => form.value.steps,
  () => {
    if (!suppressDirtyWatch && editorMode.value === 'visual') visualDirty.value = true
  },
  { deep: true }
)

watch(
  () => [form.value.report_enabled, form.value.executor_machine] as const,
  () => {
    if (!form.value.report_enabled) return
    if (!(form.value.report_results_dir || '').trim()) {
      form.value.report_results_dir = 'allure-results'
    }
    if ((form.value.report_command || '').trim()) return
    form.value.report_command = buildDefaultReportCommand(
      selectedMachineOs.value,
      form.value.report_results_dir || 'allure-results'
    )
  },
  { immediate: true }
)

watch(editorMode, async (newMode, oldMode) => {
  if (pendingEditorSwitch.value) {
    pendingEditorSwitch.value = false
    return
  }

  if (newMode === 'text' && oldMode === 'visual') {
    if (visualDirty.value || !jenkinsfileText.value) {
      const machine = machines.value.find((m) => m.id === form.value.executor_machine)
      const generated = generateJenkinsfile(form.value.steps, {
        osType: selectedMachineOs.value,
        agentLabel: machine?.jenkins_node_name || undefined,
        gitRepoUrl: form.value.git_repo_url,
        gitBranch: form.value.git_branch,
        gitCredentialId: form.value.git_credential_id,
        workspaceCleanup: form.value.workspace_cleanup,
        reportEnabled: form.value.report_enabled,
        reportResultsDir: form.value.report_results_dir,
        reportCommand: form.value.report_command,
        environmentVariables: form.value.environment_variables,
        backendBaseUrl: backendBaseUrl.value || undefined,
        buildPlanId: form.value.id ?? null,
        existingJenkinsfileText: jenkinsfileText.value || form.value.jenkinsfile_text || '',
      })
      jenkinsfileText.value = generated
      lastCleanText = generated
    }
    textDirty.value = false
    visualDirty.value = false
  } else if (newMode === 'visual' && oldMode === 'text') {
    if (textDirty.value) {
      const ok = await showConfirm(
        t('testing.pipeline.switchTitle'),
        t('testing.pipeline.switchUnsavedWarn'),
        'warning',
        'mdi-alert-circle-outline'
      )
      if (!ok) {
        pendingEditorSwitch.value = true
        editorMode.value = 'text'
        return
      }
    }
    if (jenkinsfileText.value) {
      suppressDirtyWatch = true
      const { steps, warnings } = parseJenkinsfile(jenkinsfileText.value)
      if (warnings.length) {
        snackbar.notify(t('testing.pipeline.parseWarning') + ' ' + warnings.join('; '), 'warning')
      }
      if (steps.length) {
        form.value.steps = steps
      }
      nextTick(() => {
        suppressDirtyWatch = false
      })
    }
    textDirty.value = false
    visualDirty.value = false
  }
})

const saveItem = async () => {
  try {
    const validateResult = await formRef.value?.validate()
    const valid = !!validateResult?.valid
    if (!valid) {
      if (!expandedPanels.value.includes('basic')) {
        expandedPanels.value = ['basic', ...expandedPanels.value]
      }
      snackbar.notify(t('testing.plans.fillRequired'), 'warning')
      return
    }
  } catch {
    snackbar.notify(t('testing.plans.formValidationError'), 'warning')
    return
  }
  saving.value = true
  try {
    let jfText = jenkinsfileText.value || ''
    if (editorMode.value === 'visual') {
      const machine = machines.value.find((m: any) => m.id === form.value.executor_machine)
      jfText = generateJenkinsfile(form.value.steps, {
        osType: selectedMachineOs.value,
        agentLabel: machine?.jenkins_node_name || undefined,
        gitRepoUrl: form.value.git_repo_url,
        gitBranch: form.value.git_branch,
        gitCredentialId: form.value.git_credential_id,
        workspaceCleanup: form.value.workspace_cleanup,
        reportEnabled: form.value.report_enabled,
        reportResultsDir: form.value.report_results_dir,
        reportCommand: form.value.report_command,
        environmentVariables: form.value.environment_variables,
        backendBaseUrl: backendBaseUrl.value || undefined,
        buildPlanId: form.value.id ?? null,
        existingJenkinsfileText: jenkinsfileText.value || form.value.jenkinsfile_text || '',
      })
      suppressDirtyWatch = true
      jenkinsfileText.value = jfText
      nextTick(() => {
        suppressDirtyWatch = false
      })
    }
    jfText = upsertJenkinsfileEnvironment(jfText, {
      environmentVariables: form.value.environment_variables,
      backendBaseUrl: backendBaseUrl.value || undefined,
      buildPlanId: form.value.id ?? null,
    })
    const repeatRunTimes = Number(form.value.repeat_run_times || 1)
    const safeRepeatRunTimes = Math.min(
      20,
      Math.max(1, Number.isFinite(repeatRunTimes) ? repeatRunTimes : 1)
    )
    if (safeRepeatRunTimes !== repeatRunTimes) {
      snackbar.notify(t('testing.plans.fields.repeatRunTimesRange'), 'warning')
    }

    const steps = (form.value.steps || []).map((s: any, i: number) => {
      const { id: _id, ...rest } = s
      return { ...rest, order: i }
    })

    const data: Record<string, any> = {
      name: form.value.name,
      description: form.value.description || '',
      executor_machine: form.value.executor_machine || null,
      jenkins_job_name: form.value.name || '',
      git_repo_url: form.value.git_repo_url || '',
      git_branch: form.value.git_branch || 'main',
      git_credential_id: form.value.git_credential_id || '',
      workspace_cleanup: form.value.workspace_cleanup ?? true,
      report_enabled: form.value.report_enabled || false,
      report_results_dir: form.value.report_results_dir || 'allure-results',
      report_command: form.value.report_command || '',
      repeat_run_times: safeRepeatRunTimes,
      repeat_failure_policy: form.value.repeat_failure_policy || 'continue_all',
      environment_variables: form.value.environment_variables || [],
      cron_expression: form.value.cron_expression || '',
      is_cron_enabled: form.value.is_cron_enabled || false,
      status: form.value.status || 'active',
      jenkinsfile_text: jfText,
      notification_config: {
        email: { enabled: notifyEmail.value, recipients: emailRecipientsList.value },
        webhook: { enabled: notifyWebhook.value, url: webhookUrl.value, type: webhookType.value },
        dingtalk: {
          enabled: notifyDingTalk.value,
          group_ids: selectedDingTalkGroupIds.value,
          template_id: selectedDingTalkTemplateId.value,
        },
      },
      steps,
    }

    if (form.value.id) {
      await updateBuildPlan(form.value.id, data)
    } else {
      await createBuildPlan(data)
    }
    lastCleanText = jfText
    textDirty.value = false
    dialog.value = false
    snackbar.notify(t('common.success'), 'success')
    loadData()
  } catch (e: any) {
    const msg =
      e?.response?.data?.error || e?.response?.data?.detail || e?.message || t('common.error')
    snackbar.notify(msg, 'error')
  }
  saving.value = false
}

const deleteItem = async (item: any) => {
  const ok = await showConfirm(
    t('common.confirmDelete'),
    t('common.confirmDelete', { name: item.name }),
    'error',
    'mdi-delete-outline'
  )
  if (!ok) return
  try {
    await deleteBuildPlan(item.id)
    snackbar.notify(t('common.success'), 'success')
    loadData()
  } catch (e: any) {
    snackbar.notify(e?.message || t('common.error'), 'error')
  }
}

let refreshTimer: ReturnType<typeof setTimeout> | null = null

const startAutoRefresh = () => {
  stopAutoRefresh()
  const poll = () => {
    loadData()
    const hasRunning = items.value.some(
      (i: any) =>
        i.last_execution_status && ['pending', 'running'].includes(i.last_execution_status.status)
    )
    if (hasRunning) {
      refreshTimer = setTimeout(poll, 5000)
    } else {
      refreshTimer = null
    }
  }
  refreshTimer = setTimeout(poll, 3000)
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearTimeout(refreshTimer)
    refreshTimer = null
  }
}

const triggerBuild = async (item: any) => {
  const ok = await showConfirm(
    t('testing.plans.trigger'),
    t('testing.plans.triggerConfirm'),
    'teal',
    'mdi-play-circle'
  )
  if (!ok) return
  item._triggering = true
  try {
    await triggerBuildPlan(item.id)
    snackbar.notify(t('common.success'), 'success')
    loadData()
    startAutoRefresh()
  } catch (e: any) {
    const msg =
      e?.response?.data?.error || e?.response?.data?.detail || e?.message || t('common.error')
    snackbar.notify(msg, 'error')
  }
  item._triggering = false
}

const stopBuild = async (item: any) => {
  const ok = await showConfirm(
    t('testing.plans.stopBuild'),
    t('testing.plans.stopBuildConfirm'),
    'error',
    'mdi-stop-circle-outline'
  )
  if (!ok) return
  item._stopping = true
  try {
    await stopBuildPlan(item.id)
    snackbar.notify(t('testing.plans.stopSent'), 'success')
    loadData()
  } catch (e: any) {
    const msg =
      e?.response?.data?.error || e?.response?.data?.detail || e?.message || t('common.error')
    snackbar.notify(msg, 'error')
  }
  item._stopping = false
}

const copyTriggerUrl = (item: any) => {
  const url = `${window.location.origin}/api/build-trigger/?plan_id=${item.id}`
  navigator.clipboard.writeText(url)
  snackbar.notify(t('testing.plans.triggerUrlCopied'), 'success')
}

const goToDetail = (item: any) => {
  router.push({ name: 'BuildPlanDetail', params: { id: item.id } })
}

onMounted(loadData)
onBeforeUnmount(stopAutoRefresh)
</script>

<style scoped>
.code-font :deep(textarea) {
  font-family: 'Fira Code', 'Courier New', monospace;
  font-size: 13px;
}
.left-config-panel {
  background: #fff;
}
.left-config-panel :deep(.v-expansion-panel-title) {
  min-height: 44px;
  padding: 8px 16px;
  font-size: 14px;
}
.left-config-panel :deep(.v-expansion-panel-text__wrapper) {
  padding: 12px 16px;
}
.pipeline-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}
</style>

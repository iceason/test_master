<template>
  <v-container fluid>
    <!-- Header -->
    <v-sheet class="pa-4 rounded-xl border-thin" elevation="0" color="surface">
      <v-row dense align="center">
        <v-col>
          <div class="d-flex align-center">
            <v-icon size="24" color="primary" class="mr-3">mdi-email-edit-outline</v-icon>
            <div>
              <div class="text-h6 font-weight-bold">{{ $t('settings.emailTemplates.title') }}</div>
              <div class="text-caption text-medium-emphasis">{{ $t('settings.emailTemplates.subtitle') }}</div>
            </div>
          </div>
        </v-col>
        <v-col cols="auto">
          <v-btn color="primary" prepend-icon="mdi-plus" class="text-none font-weight-bold" @click="openEditor()">
            {{ $t('settings.emailTemplates.new') }}
          </v-btn>
        </v-col>
      </v-row>
    </v-sheet>

    <!-- Template cards -->
    <v-row class="mt-4">
      <v-col v-for="tpl in templates" :key="tpl.id" cols="12" md="6" lg="4">
        <v-card class="rounded-xl" elevation="1" hover @click="openEditor(tpl)">
          <v-card-item>
            <template v-slot:prepend>
              <v-avatar color="primary" variant="tonal" size="40">
                <v-icon>mdi-email-outline</v-icon>
              </v-avatar>
            </template>
            <v-card-title class="text-subtitle-1 font-weight-bold">{{ tpl.name }}</v-card-title>
            <v-card-subtitle class="text-caption">
              {{ $t('common.updatedAt') }}: {{ formatDate(tpl.updated_at) }}
            </v-card-subtitle>
            <template v-slot:append>
              <v-chip v-if="tpl.is_default" color="success" size="small" variant="tonal" class="font-weight-bold">
                <v-icon start size="14">mdi-check-circle</v-icon>
                {{ $t('settings.emailTemplates.default') }}
              </v-chip>
            </template>
          </v-card-item>

          <v-card-text class="pt-0 px-4 pb-2">
            <div class="text-caption text-grey-darken-1 mb-1">{{ $t('settings.emailTemplates.subjectLabel') }}:</div>
            <div class="text-body-2 text-truncate mb-2" style="font-family: monospace;">{{ tpl.subject }}</div>
            <div class="text-caption text-grey-darken-1 mb-1">{{ $t('settings.emailTemplates.bodyPreview') }}:</div>
            <div class="text-body-2 body-preview">{{ tpl.body }}</div>
          </v-card-text>

          <v-card-actions class="px-4 pb-3" @click.stop>
            <v-btn v-if="!tpl.is_default" variant="tonal" color="success" size="small" class="text-none" prepend-icon="mdi-check-circle-outline" @click.stop="setDefault(tpl)">
              {{ $t('settings.emailTemplates.setDefault') }}
            </v-btn>
            <v-spacer />
            <v-btn variant="text" color="primary" size="small" icon="mdi-eye-outline" @click.stop="previewTemplate(tpl)" />
            <v-btn variant="text" color="primary" size="small" icon="mdi-pencil-outline" @click.stop="openEditor(tpl)" />
            <v-btn variant="text" color="error" size="small" icon="mdi-delete-outline" @click.stop="deleteTemplate(tpl)" />
          </v-card-actions>
        </v-card>
      </v-col>

      <v-col v-if="!loading && !templates.length" cols="12">
        <v-empty-state icon="mdi-email-off-outline" :title="$t('settings.emailTemplates.empty')" class="py-10">
          <template v-slot:actions>
            <v-btn color="primary" prepend-icon="mdi-plus" class="text-none" @click="openEditor()">
              {{ $t('settings.emailTemplates.createFirst') }}
            </v-btn>
          </template>
        </v-empty-state>
      </v-col>
    </v-row>

    <!-- Edit Dialog -->
    <v-dialog v-model="editorDialog" max-width="900" persistent>
      <v-card class="rounded-xl" elevation="8">
        <v-toolbar color="primary" density="compact">
          <v-btn icon="mdi-close" variant="text" @click="editorDialog = false" />
          <v-toolbar-title class="text-subtitle-1 font-weight-bold">
            {{ editingTpl?.id ? $t('settings.emailTemplates.edit') : $t('settings.emailTemplates.new') }}
          </v-toolbar-title>
          <v-spacer />
          <v-btn variant="text" class="text-none font-weight-bold" @click="save" :loading="saving">
            {{ $t('common.save') }}
          </v-btn>
        </v-toolbar>

        <v-card-text class="pa-0">
          <v-row no-gutters>
            <v-col cols="7" class="pa-6">
              <v-text-field v-model="form.name" :label="$t('settings.emailTemplates.nameLabel')" variant="outlined" density="compact" class="mb-3" />
              <v-text-field v-model="form.subject" :label="$t('settings.emailTemplates.subjectLabel')" variant="outlined" density="compact" class="mb-3" style="font-family: monospace;" />
              <v-textarea v-model="form.body" :label="$t('settings.emailTemplates.bodyLabel')" variant="outlined" density="compact" rows="10" auto-grow style="font-family: monospace;" />
              <v-switch v-model="form.is_default" :label="$t('settings.emailTemplates.setAsDefault')" color="primary" density="compact" hide-details />
            </v-col>
            <v-col cols="5" class="pa-6 bg-grey-lighten-5" style="overflow-y: auto; max-height: 80vh;">
              <div class="text-subtitle-2 font-weight-bold mb-2">
                <v-icon size="16" class="mr-1">mdi-code-braces</v-icon>
                {{ $t('settings.emailTemplates.variables') }}
              </div>
              <div class="text-caption text-grey mb-3">{{ $t('settings.emailTemplates.variableHint') }}</div>
              <v-chip v-for="v in variableList" :key="v.key" size="small" variant="outlined" color="primary" class="mr-1 mb-1" style="cursor: pointer" @click="insertVariable(v.key)">
                <span v-text="varTag(v.key)"></span>
              </v-chip>
              <v-divider class="my-4" />
              <div class="text-subtitle-2 font-weight-bold mb-2">
                <v-icon size="16" class="mr-1">mdi-eye-outline</v-icon>
                {{ $t('settings.emailTemplates.livePreview') }}
              </div>
              <v-sheet class="rounded-lg" color="white" elevation="1" style="overflow: hidden;">
                <div class="px-3 py-2 bg-teal-lighten-5" style="border-bottom: 1px solid #e0e0e0;">
                  <div class="text-caption font-weight-bold text-teal-darken-2">{{ liveSubjectPreview }}</div>
                </div>
                <pre class="email-body-text pa-3">{{ livePreview }}</pre>
              </v-sheet>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Preview Dialog -->
    <v-dialog v-model="previewDialog" max-width="680">
      <v-card class="rounded-xl" elevation="12">
        <v-toolbar color="teal-darken-1" density="compact">
          <v-btn icon="mdi-close" variant="text" @click="previewDialog = false" />
          <v-toolbar-title class="text-subtitle-1 font-weight-bold">
            <v-icon class="mr-1" size="18">mdi-email-search-outline</v-icon>
            {{ $t('settings.emailTemplates.emailPreview') }}
          </v-toolbar-title>
        </v-toolbar>
        <v-card-text class="pa-0">
          <div class="email-preview-envelope">
            <div class="email-preview-header">
              <v-row dense align="center" class="mb-2">
                <v-col cols="auto" class="text-caption text-grey-darken-1 font-weight-bold">{{ $t('settings.emailTemplates.sender') }}：</v-col>
                <v-col class="text-caption">Test Master &lt;noreply@testmaster.local&gt;</v-col>
              </v-row>
              <v-row dense align="center" class="mb-2">
                <v-col cols="auto" class="text-caption text-grey-darken-1 font-weight-bold">{{ $t('settings.emailTemplates.recipient') }}：</v-col>
                <v-col class="text-caption">team@example.com</v-col>
              </v-row>
              <v-row dense align="center">
                <v-col cols="auto" class="text-caption text-grey-darken-1 font-weight-bold">{{ $t('settings.emailTemplates.subjectLine') }}：</v-col>
                <v-col class="text-subtitle-2 font-weight-bold">{{ previewData.subject }}</v-col>
              </v-row>
            </div>
            <v-divider />
            <div class="email-preview-body">
              <pre class="email-body-text">{{ previewData.body }}</pre>
            </div>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation -->
    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card class="rounded-xl">
        <v-toolbar color="error" density="compact">
          <v-toolbar-title class="text-subtitle-1 font-weight-bold">{{ $t('common.confirmDelete') }}</v-toolbar-title>
        </v-toolbar>
        <v-card-text class="pa-4 text-body-2">{{ $t('common.confirmDelete', { name: deletingTpl?.name }) }}</v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn color="grey-darken-1" variant="text" @click="deleteDialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="error" variant="flat" class="ml-2" @click="doDelete" :loading="deleting">{{ $t('common.delete') }}</v-btn>
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
  getEmailTemplates,
  createEmailTemplate,
  updateEmailTemplate,
  deleteEmailTemplate as deleteEmailTemplateApi,
  setDefaultEmailTemplate,
  previewEmailTemplate,
} from '@/api/testing'

const { t } = useI18n()
const snackbar = useSnackbarStore()

const templates = ref<any[]>([])
const loading = ref(false)
const editorDialog = ref(false)
const previewDialog = ref(false)
const deleteDialog = ref(false)
const saving = ref(false)
const deleting = ref(false)

const editingTpl = ref<any>(null)
const deletingTpl = ref<any>(null)
const previewData = ref({ subject: '', body: '' })

const form = ref({
  name: '',
  subject: '',
  body: '',
  is_default: false,
})

const defaultBody =
`══════════════════════════════════════
  {{status_emoji}} 自动化测试执行报告
══════════════════════════════════════

【基本信息】
  构建计划：{{plan_name}}
  执行结果：{{status_upper}}
  执行时间：{{timestamp}}
  执行耗时：{{duration}}

【触发信息】
  触发方式：{{trigger_type}}
  触发人员：{{triggered_by}}

【构建详情】
  Jenkins 链接：{{jenkins_url}}
  （点击上方链接可查看完整构建日志与测试产物）

──────────────────────────────────────
  说明：
  · SUCCESS  — 所有测试步骤执行通过
  · FAILED   — 存在失败的测试步骤，请及时排查
  · CANCELLED — 构建被手动取消
──────────────────────────────────────

此邮件由 Test Master 自动发送，请勿直接回复。
如有疑问请联系测试团队。
`

const variableList = [
  { key: 'plan_name' },
  { key: 'status' },
  { key: 'status_upper' },
  { key: 'status_emoji' },
  { key: 'trigger_type' },
  { key: 'triggered_by' },
  { key: 'duration' },
  { key: 'jenkins_url' },
  { key: 'timestamp' },
]

const varTag = (key: string) => `\u007B\u007B${key}\u007D\u007D`

const sampleData: Record<string, string> = {
  plan_name: '示例构建计划',
  status: 'success',
  status_upper: 'SUCCESS',
  status_emoji: '✅',
  trigger_type: '手动',
  triggered_by: 'admin',
  duration: '1m 23s',
  jenkins_url: 'http://127.0.0.1:8080/job/demo/1/',
  timestamp: new Date().toLocaleString(),
}

const liveSubjectPreview = computed(() => {
  let text = form.value.subject
  for (const [key, value] of Object.entries(sampleData)) {
    text = text.replace(new RegExp(`\\{\\{${key}\\}\\}`, 'g'), value)
  }
  return text
})

const livePreview = computed(() => {
  let text = form.value.body
  for (const [key, value] of Object.entries(sampleData)) {
    text = text.replace(new RegExp(`\\{\\{${key}\\}\\}`, 'g'), value)
  }
  return text
})

const formatDate = (d: string) => {
  if (!d) return '-'
  return new Date(d).toLocaleString()
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getEmailTemplates()
    templates.value = Array.isArray(res) ? res : (res as any).results || []
  } catch { snackbar.notify(t('common.error'), 'error') }
  loading.value = false
}

const openEditor = (tpl?: any) => {
  if (tpl) {
    editingTpl.value = tpl
    form.value = { name: tpl.name, subject: tpl.subject, body: tpl.body, is_default: tpl.is_default }
  } else {
    editingTpl.value = null
    form.value = {
      name: '',
      subject: '{{status_emoji}} [Test Master] {{plan_name}} - {{status_upper}}',
      body: defaultBody,
      is_default: false,
    }
  }
  editorDialog.value = true
}

const insertVariable = (key: string) => {
  form.value.body += `{{${key}}}`
}

const save = async () => {
  if (!form.value.name) { snackbar.notify(t('common.required'), 'warning'); return }
  saving.value = true
  try {
    if (editingTpl.value?.id) {
      await updateEmailTemplate(editingTpl.value.id, form.value)
    } else {
      await createEmailTemplate(form.value)
    }
    editorDialog.value = false
    snackbar.notify(t('common.saveSuccess'), 'success')
    fetchData()
  } catch { snackbar.notify(t('common.error'), 'error') }
  saving.value = false
}

const setDefault = async (tpl: any) => {
  try {
    await setDefaultEmailTemplate(tpl.id)
    snackbar.notify(t('common.success'), 'success')
    fetchData()
  } catch { snackbar.notify(t('common.error'), 'error') }
}

const previewTemplate = async (tpl: any) => {
  try {
    const res = await previewEmailTemplate(tpl.id) as any
    previewData.value = { subject: res.subject, body: res.body }
    previewDialog.value = true
  } catch { snackbar.notify(t('common.error'), 'error') }
}

const deleteTemplate = (tpl: any) => {
  deletingTpl.value = tpl
  deleteDialog.value = true
}

const doDelete = async () => {
  if (!deletingTpl.value) return
  deleting.value = true
  try {
    await deleteEmailTemplateApi(deletingTpl.value.id)
    deleteDialog.value = false
    snackbar.notify(t('common.deleteSuccess'), 'success')
    fetchData()
  } catch { snackbar.notify(t('common.error'), 'error') }
  deleting.value = false
}

onMounted(fetchData)
</script>

<style scoped>
.body-preview {
  max-height: 60px;
  overflow: hidden;
  text-overflow: ellipsis;
  font-family: monospace;
  font-size: 12px;
  color: #666;
}

.email-preview-envelope {
  background: #fafafa;
}

.email-preview-header {
  padding: 20px 24px 16px;
  background: linear-gradient(135deg, #f5f5f5 0%, #fafafa 100%);
}

.email-preview-body {
  padding: 20px 24px 24px;
  background: #fff;
}

.email-body-text {
  font-family: 'Menlo', 'Consolas', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
  color: #333;
  margin: 0;
}
</style>

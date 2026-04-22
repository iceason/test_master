<template>
  <v-container fluid>
    <v-sheet class="pa-4 rounded-xl border-thin" elevation="0" color="surface">
      <v-row dense align="center">
        <v-col>
          <div class="d-flex align-center">
            <v-icon size="24" color="primary" class="mr-3">mdi-message-text-outline</v-icon>
            <div>
              <div class="text-h6 font-weight-bold">{{ $t('settings.dingtalkTemplates.title') }}</div>
              <div class="text-caption text-medium-emphasis">{{ $t('settings.dingtalkTemplates.subtitle') }}</div>
            </div>
          </div>
        </v-col>
        <v-col cols="auto">
          <v-btn color="primary" prepend-icon="mdi-plus" class="text-none font-weight-bold" @click="openEditor()">
            {{ $t('settings.dingtalkTemplates.new') }}
          </v-btn>
        </v-col>
      </v-row>
    </v-sheet>

    <v-row class="mt-4">
      <v-col v-for="tpl in templates" :key="tpl.id" cols="12" md="6" lg="4">
        <v-card class="rounded-xl" elevation="1" hover @click="openEditor(tpl)">
          <v-card-item>
            <template v-slot:prepend>
              <v-avatar color="primary" variant="tonal" size="40"><v-icon>mdi-note-text-outline</v-icon></v-avatar>
            </template>
            <v-card-title>{{ tpl.name }}</v-card-title>
            <template v-slot:append>
              <v-chip v-if="tpl.is_default" size="small" color="success" variant="tonal">{{ $t('common.default') }}</v-chip>
            </template>
          </v-card-item>
          <v-card-text class="pt-0">
            <div class="text-caption text-medium-emphasis text-truncate">{{ tpl.title_template }}</div>
          </v-card-text>
          <v-card-actions @click.stop>
            <v-spacer />
            <v-btn v-if="!tpl.is_default" icon="mdi-check-circle-outline" variant="text" color="success" @click.stop="setDefault(tpl)" />
            <v-btn icon="mdi-eye-outline" variant="text" color="teal" @click.stop="preview(tpl)" />
            <v-btn icon="mdi-pencil-outline" variant="text" color="primary" @click.stop="openEditor(tpl)" />
            <v-btn icon="mdi-delete-outline" variant="text" color="error" @click.stop="remove(tpl)" />
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <v-dialog v-model="dialog" max-width="760" persistent>
      <v-card class="rounded-xl">
        <v-toolbar color="primary" density="compact">
          <v-btn icon="mdi-close" variant="text" @click="dialog = false" />
          <v-toolbar-title>{{ editing?.id ? $t('common.edit') : $t('common.create') }}</v-toolbar-title>
          <v-spacer />
          <v-btn variant="text" class="text-none" :loading="saving" @click="save">{{ $t('common.save') }}</v-btn>
        </v-toolbar>
        <v-card-text class="pa-6">
          <v-text-field v-model="form.name" :label="$t('settings.dingtalkTemplates.name')" variant="outlined" density="compact" class="mb-3" />
          <v-text-field v-model="form.title_template" :label="$t('settings.dingtalkTemplates.titleTemplate')" variant="outlined" density="compact" class="mb-3" />
          <v-textarea v-model="form.body_template" :label="$t('settings.dingtalkTemplates.bodyTemplate')" variant="outlined" density="compact" rows="8" class="mb-3" />
          <v-textarea v-model="form.description" :label="$t('settings.dingtalkTemplates.description')" variant="outlined" density="compact" rows="2" class="mb-3" />
          <v-switch v-model="form.is_default" :label="$t('settings.dingtalkTemplates.isDefault')" color="primary" density="compact" hide-details class="mb-2" />
          <v-switch v-model="form.is_active" :label="$t('settings.dingtalkTemplates.isActive')" color="primary" density="compact" hide-details />
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="previewDialog" max-width="680">
      <v-card class="rounded-xl">
        <v-toolbar color="teal-darken-1" density="compact">
          <v-btn icon="mdi-close" variant="text" @click="previewDialog = false" />
          <v-toolbar-title>{{ $t('settings.dingtalkTemplates.preview') }}</v-toolbar-title>
        </v-toolbar>
        <v-card-text class="pa-4">
          <div class="text-subtitle-2 font-weight-bold mb-2">{{ previewData.title }}</div>
          <pre class="preview-text">{{ previewData.body }}</pre>
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useSnackbarStore } from '@/store/snackbar'
import {
  getDingTalkTemplates, createDingTalkTemplate, updateDingTalkTemplate,
  deleteDingTalkTemplate, setDefaultDingTalkTemplate, previewDingTalkTemplate,
} from '@/api/testing'

const { t } = useI18n()
const snackbar = useSnackbarStore()
const templates = ref<any[]>([])
const dialog = ref(false)
const saving = ref(false)
const editing = ref<any>(null)
const previewDialog = ref(false)
const previewData = ref({ title: '', body: '' })
const form = ref({
  name: '',
  title_template: '{{status_emoji}} [Test Master] {{plan_name}} - {{status_upper}}',
  body_template:
    '## {{status_emoji}} 自动化构建通知\\n\\n' +
    '### 基本信息\\n' +
    '- 构建计划：{{plan_name}}\\n' +
    '- 执行结果：{{status_upper}}\\n' +
    '- 执行时间：{{timestamp}}\\n' +
    '- 执行耗时：{{duration}}\\n\\n' +
    '### 触发信息\\n' +
    '- 触发方式：{{trigger_type}}\\n' +
    '- 触发人：{{triggered_by}}\\n\\n' +
    '### 构建详情\\n' +
    '- Jenkins 链接：{{jenkins_url}}\\n\\n' +
    '---\\n' +
    '说明：\\n' +
    '- SUCCESS：所有步骤执行通过\\n' +
    '- FAILED：存在失败步骤，请及时排查\\n' +
    '- CANCELLED：构建被取消\\n',
  description: '',
  is_default: false,
  is_active: true,
})

const loadData = async () => {
  try {
    const res = await getDingTalkTemplates()
    templates.value = Array.isArray(res) ? res : (res as any).results || []
  } catch {
    snackbar.notify(t('common.error'), 'error')
  }
}

const openEditor = (tpl?: any) => {
  if (tpl) {
    editing.value = tpl
    form.value = {
      name: tpl.name,
      title_template: tpl.title_template,
      body_template: tpl.body_template,
      description: tpl.description || '',
      is_default: tpl.is_default,
      is_active: tpl.is_active,
    }
  } else {
    editing.value = null
    form.value = {
      name: '',
      title_template: '{{status_emoji}} [Test Master] {{plan_name}} - {{status_upper}}',
      body_template:
        '## {{status_emoji}} 自动化构建通知\\n\\n' +
        '### 基本信息\\n' +
        '- 构建计划：{{plan_name}}\\n' +
        '- 执行结果：{{status_upper}}\\n' +
        '- 执行时间：{{timestamp}}\\n' +
        '- 执行耗时：{{duration}}\\n\\n' +
        '### 触发信息\\n' +
        '- 触发方式：{{trigger_type}}\\n' +
        '- 触发人：{{triggered_by}}\\n\\n' +
        '### 构建详情\\n' +
        '- Jenkins 链接：{{jenkins_url}}\\n\\n' +
        '---\\n' +
        '说明：\\n' +
        '- SUCCESS：所有步骤执行通过\\n' +
        '- FAILED：存在失败步骤，请及时排查\\n' +
        '- CANCELLED：构建被取消\\n',
      description: '',
      is_default: false,
      is_active: true,
    }
  }
  dialog.value = true
}

const save = async () => {
  if (!form.value.name || !form.value.title_template || !form.value.body_template) {
    snackbar.notify(t('common.required'), 'warning')
    return
  }
  saving.value = true
  try {
    if (editing.value?.id) await updateDingTalkTemplate(editing.value.id, form.value)
    else await createDingTalkTemplate(form.value)
    dialog.value = false
    snackbar.notify(t('common.saveSuccess'), 'success')
    loadData()
  } catch {
    snackbar.notify(t('common.error'), 'error')
  }
  saving.value = false
}

const setDefault = async (tpl: any) => {
  try {
    await setDefaultDingTalkTemplate(tpl.id)
    snackbar.notify(t('common.success'), 'success')
    loadData()
  } catch {
    snackbar.notify(t('common.error'), 'error')
  }
}

const preview = async (tpl: any) => {
  try {
    const res = await previewDingTalkTemplate(tpl.id) as any
    previewData.value = { title: res.title, body: res.body }
    previewDialog.value = true
  } catch {
    snackbar.notify(t('common.error'), 'error')
  }
}

const remove = async (tpl: any) => {
  try {
    await deleteDingTalkTemplate(tpl.id)
    snackbar.notify(t('common.deleteSuccess'), 'success')
    loadData()
  } catch {
    snackbar.notify(t('common.error'), 'error')
  }
}

onMounted(loadData)
</script>

<style scoped>
.preview-text {
  white-space: pre-wrap;
  word-break: break-word;
  font-family: Menlo, Consolas, monospace;
  margin: 0;
}
</style>

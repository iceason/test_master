<template>
  <v-container fluid>
    <v-sheet class="pa-4 rounded-xl border-thin" elevation="0" color="surface">
      <v-row dense align="center">
        <v-col>
          <div class="d-flex align-center">
            <v-icon size="24" color="primary" class="mr-3">mdi-chat-processing-outline</v-icon>
            <div>
              <div class="text-h6 font-weight-bold">{{ $t('settings.dingtalkGroups.title') }}</div>
              <div class="text-caption text-medium-emphasis">{{ $t('settings.dingtalkGroups.subtitle') }}</div>
            </div>
          </div>
        </v-col>
        <v-col cols="auto">
          <v-btn color="primary" prepend-icon="mdi-plus" class="text-none font-weight-bold" @click="openEditor()">
            {{ $t('settings.dingtalkGroups.new') }}
          </v-btn>
        </v-col>
      </v-row>
    </v-sheet>

    <v-row class="mt-4">
      <v-col v-for="item in groups" :key="item.id" cols="12" md="6" lg="4">
        <v-card class="rounded-xl" elevation="1" hover @click="openEditor(item)">
          <v-card-item>
            <template v-slot:prepend>
              <v-avatar :color="item.is_active ? 'primary' : 'grey'" variant="tonal" size="40">
                <v-icon>mdi-robot-outline</v-icon>
              </v-avatar>
            </template>
            <v-card-title class="text-subtitle-1 font-weight-bold">{{ item.name }}</v-card-title>
            <v-card-subtitle class="text-caption">{{ item.webhook_url }}</v-card-subtitle>
            <template v-slot:append>
              <v-chip :color="item.is_active ? 'success' : 'grey'" size="small" variant="tonal">
                {{ item.is_active ? $t('common.enabled') : $t('common.disabled') }}
              </v-chip>
            </template>
          </v-card-item>
          <v-card-text class="pt-0">
            <div class="text-caption text-medium-emphasis">{{ item.description || '-' }}</div>
          </v-card-text>
          <v-card-actions @click.stop>
            <v-spacer />
            <v-btn icon="mdi-send-check-outline" variant="text" color="teal" @click.stop="testSend(item)" />
            <v-btn icon="mdi-pencil-outline" variant="text" color="primary" @click.stop="openEditor(item)" />
            <v-btn icon="mdi-delete-outline" variant="text" color="error" @click.stop="remove(item)" />
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <v-dialog v-model="dialog" max-width="640" persistent>
      <v-card class="rounded-xl">
        <v-toolbar color="primary" density="compact">
          <v-btn icon="mdi-close" variant="text" @click="dialog = false" />
          <v-toolbar-title>{{ editing?.id ? $t('common.edit') : $t('common.create') }}</v-toolbar-title>
          <v-spacer />
          <v-btn variant="text" class="text-none" :loading="saving" @click="save">{{ $t('common.save') }}</v-btn>
        </v-toolbar>
        <v-card-text class="pa-6">
          <v-text-field v-model="form.name" :label="$t('settings.dingtalkGroups.name')" variant="outlined" density="compact" class="mb-3" />
          <v-text-field v-model="form.webhook_url" :label="$t('settings.dingtalkGroups.webhookUrl')" variant="outlined" density="compact" class="mb-3" />
          <v-text-field v-model="form.secret" :label="$t('settings.dingtalkGroups.secret')" variant="outlined" density="compact" :type="showSecret ? 'text' : 'password'" :append-inner-icon="showSecret ? 'mdi-eye-off-outline' : 'mdi-eye-outline'" @click:append-inner="showSecret = !showSecret" class="mb-3" />
          <v-textarea v-model="form.description" :label="$t('settings.dingtalkGroups.description')" variant="outlined" density="compact" rows="2" class="mb-3" />
          <v-switch v-model="form.is_active" :label="$t('settings.dingtalkGroups.isActive')" color="primary" density="compact" hide-details />
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
  getDingTalkGroups, createDingTalkGroup, updateDingTalkGroup,
  deleteDingTalkGroup, testDingTalkGroupSend,
} from '@/api/testing'

const { t } = useI18n()
const snackbar = useSnackbarStore()
const groups = ref<any[]>([])
const dialog = ref(false)
const saving = ref(false)
const showSecret = ref(false)
const editing = ref<any>(null)
const form = ref({ name: '', webhook_url: '', secret: '', description: '', is_active: true })

const loadData = async () => {
  try {
    const res = await getDingTalkGroups()
    groups.value = Array.isArray(res) ? res : (res as any).results || []
  } catch {
    snackbar.notify(t('common.error'), 'error')
  }
}

const openEditor = (item?: any) => {
  showSecret.value = false
  if (item) {
    editing.value = item
    form.value = {
      name: item.name,
      webhook_url: item.webhook_url,
      secret: '',
      description: item.description || '',
      is_active: item.is_active,
    }
  } else {
    editing.value = null
    form.value = { name: '', webhook_url: '', secret: '', description: '', is_active: true }
  }
  dialog.value = true
}

const save = async () => {
  if (!form.value.name || !form.value.webhook_url || (!editing.value && !form.value.secret)) {
    snackbar.notify(t('common.required'), 'warning')
    return
  }
  saving.value = true
  try {
    if (editing.value?.id) {
      await updateDingTalkGroup(editing.value.id, form.value)
    } else {
      await createDingTalkGroup(form.value)
    }
    dialog.value = false
    snackbar.notify(t('common.saveSuccess'), 'success')
    loadData()
  } catch (e: any) {
    snackbar.notify(e?.response?.data?.message || t('common.error'), 'error')
  }
  saving.value = false
}

const testSend = async (item: any) => {
  try {
    await testDingTalkGroupSend(item.id)
    snackbar.notify(t('common.success'), 'success')
  } catch (e: any) {
    snackbar.notify(e?.response?.data?.message || t('common.error'), 'error')
  }
}

const remove = async (item: any) => {
  try {
    await deleteDingTalkGroup(item.id)
    snackbar.notify(t('common.deleteSuccess'), 'success')
    loadData()
  } catch {
    snackbar.notify(t('common.error'), 'error')
  }
}

onMounted(loadData)
</script>

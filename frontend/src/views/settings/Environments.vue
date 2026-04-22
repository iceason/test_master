<template>
  <v-container fluid>
    <!-- Header -->
    <v-sheet class="pa-4 rounded-xl border-thin" elevation="0" color="surface">
      <v-row dense align="center">
        <v-col>
          <div class="d-flex align-center">
            <v-icon size="24" color="primary" class="mr-3">mdi-earth</v-icon>
            <div>
              <div class="text-h6 font-weight-bold">{{ $t('settings.environments.title') }}</div>
              <div class="text-caption text-medium-emphasis">{{ $t('settings.environments.subtitle') }}</div>
            </div>
          </div>
        </v-col>
        <v-col cols="auto">
          <v-btn color="primary" prepend-icon="mdi-plus" class="text-none font-weight-bold" @click="openEditor()">
            {{ $t('settings.environments.new') }}
          </v-btn>
        </v-col>
      </v-row>
    </v-sheet>

    <!-- Environment cards -->
    <v-row class="mt-4">
      <v-col v-for="env in environments" :key="env.id" cols="12" md="6" lg="4">
        <v-card class="rounded-xl" elevation="1" hover @click="openEditor(env)">
          <v-card-item>
            <template v-slot:prepend>
              <v-avatar :color="env.is_active ? 'primary' : 'grey'" variant="tonal" size="40">
                <v-icon>mdi-earth</v-icon>
              </v-avatar>
            </template>
            <v-card-title class="text-subtitle-1 font-weight-bold">{{ env.name }}</v-card-title>
            <v-card-subtitle class="text-caption">{{ env.code }}</v-card-subtitle>
            <template v-slot:append>
              <v-chip :color="env.is_active ? 'success' : 'grey'" size="small" variant="tonal" class="font-weight-bold">
                <v-icon start size="14">{{ env.is_active ? 'mdi-check-circle' : 'mdi-close-circle' }}</v-icon>
                {{ env.is_active ? $t('settings.environments.active') : $t('settings.environments.inactive') }}
              </v-chip>
            </template>
          </v-card-item>

          <v-card-text class="pt-0 px-4 pb-2">
            <div v-if="env.project_name" class="d-flex align-center mb-2">
              <v-icon size="14" color="teal" class="mr-1">mdi-folder-outline</v-icon>
              <v-chip size="small" color="teal" variant="tonal">{{ env.project_name }}</v-chip>
            </div>
            <div class="text-caption text-grey-darken-1 mb-1">{{ $t('settings.environments.baseUrlLabel') }}:</div>
            <div class="text-body-2 text-truncate mb-2" style="font-family: monospace;">{{ env.base_url }}</div>
            <div class="text-caption text-grey-darken-1 mb-1">Token:</div>
            <div class="text-body-2 text-truncate mb-2" style="font-family: monospace;">{{ env.token ? '••••••••' + env.token.slice(-6) : '-' }}</div>
            <div v-if="env.description" class="text-caption text-grey-darken-1 mb-1">{{ $t('settings.environments.descriptionLabel') }}:</div>
            <div v-if="env.description" class="text-body-2 text-truncate">{{ env.description }}</div>
          </v-card-text>

          <v-card-actions class="px-4 pb-3" @click.stop>
            <v-chip size="x-small" variant="text" class="text-caption text-medium-emphasis">
              {{ $t('common.updatedAt') }}: {{ formatDate(env.updated_at) }}
            </v-chip>
            <v-spacer />
            <v-btn variant="text" color="primary" size="small" icon="mdi-pencil-outline" @click.stop="openEditor(env)" />
            <v-btn variant="text" color="error" size="small" icon="mdi-delete-outline" @click.stop="confirmDelete(env)" />
          </v-card-actions>
        </v-card>
      </v-col>

      <v-col v-if="!loading && !environments.length" cols="12">
        <v-empty-state icon="mdi-earth" :title="$t('settings.environments.empty')" class="py-10">
          <template v-slot:actions>
            <v-btn color="primary" prepend-icon="mdi-plus" class="text-none" @click="openEditor()">
              {{ $t('settings.environments.createFirst') }}
            </v-btn>
          </template>
        </v-empty-state>
      </v-col>
    </v-row>

    <!-- Edit Dialog -->
    <v-dialog v-model="editorDialog" max-width="600" persistent>
      <v-card class="rounded-xl" elevation="8">
        <v-toolbar color="primary" density="compact">
          <v-btn icon="mdi-close" variant="text" @click="editorDialog = false" />
          <v-toolbar-title class="text-subtitle-1 font-weight-bold">
            {{ editingEnv?.id ? $t('settings.environments.edit') : $t('settings.environments.new') }}
          </v-toolbar-title>
          <v-spacer />
          <v-btn variant="text" class="text-none font-weight-bold" @click="save" :loading="saving">
            {{ $t('common.save') }}
          </v-btn>
        </v-toolbar>

        <v-card-text class="pa-6">
          <v-text-field v-model="form.name" :label="$t('settings.environments.nameLabel')" variant="outlined" density="compact" class="mb-4" :rules="[v => !!v || $t('common.required')]" />
          <v-text-field v-model="form.code" :label="$t('settings.environments.codeLabel')" :hint="$t('settings.environments.codeHint')" persistent-hint variant="outlined" density="compact" class="mb-4" :rules="[v => !!v || $t('common.required')]" />
          <v-select
            v-model="form.project"
            :items="projects"
            item-title="name"
            item-value="id"
            :label="$t('settings.environments.projectLabel')"
            :hint="$t('settings.environments.projectHint')"
            persistent-hint
            variant="outlined"
            density="compact"
            clearable
            class="mb-4"
          >
            <template v-slot:prepend-inner>
              <v-icon size="18" color="teal">mdi-folder-outline</v-icon>
            </template>
          </v-select>
          <v-text-field v-model="form.base_url" :label="$t('settings.environments.baseUrlLabel')" variant="outlined" density="compact" placeholder="https://api.example.com" class="mb-4" :rules="[v => !!v || $t('common.required')]" />
          <v-text-field v-model="form.token" label="Token" variant="outlined" density="compact" :type="showToken ? 'text' : 'password'" :append-inner-icon="showToken ? 'mdi-eye-off-outline' : 'mdi-eye-outline'" @click:append-inner="showToken = !showToken" :hint="$t('settings.environments.tokenHint')" persistent-hint class="mb-4" />
          <v-textarea v-model="form.description" :label="$t('settings.environments.descriptionLabel')" variant="outlined" density="compact" rows="2" auto-grow class="mb-4" />
          <v-switch v-model="form.is_active" :label="$t('settings.environments.isActive')" color="primary" density="compact" hide-details />
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card class="rounded-xl">
        <v-toolbar color="error" density="compact">
          <v-toolbar-title class="text-subtitle-1 font-weight-bold">{{ $t('common.confirmDelete') }}</v-toolbar-title>
        </v-toolbar>
        <v-card-text class="pa-4 text-body-2">
          {{ $t('settings.environments.deleteConfirm', { name: deletingEnv?.name }) }}
        </v-card-text>
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
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useSnackbarStore } from '@/store/snackbar'
import { getEnvironments, createEnvironment, updateEnvironment, deleteEnvironment } from '@/api/testing'
import { getDirectories } from '@/api/directory'

const { t } = useI18n()
const snackbar = useSnackbarStore()

const environments = ref<any[]>([])
const projects = ref<any[]>([])
const loading = ref(false)
const editorDialog = ref(false)
const deleteDialog = ref(false)
const saving = ref(false)
const deleting = ref(false)
const showToken = ref(false)

const editingEnv = ref<any>(null)
const deletingEnv = ref<any>(null)

const form = ref({ name: '', code: '', project: null as number | null, base_url: '', token: '', description: '', is_active: true })

const formatDate = (d: string) => d ? new Date(d).toLocaleString() : '-'

const fetchData = async () => {
  loading.value = true
  try {
    const [envRes, dirRes] = await Promise.all([
      getEnvironments(),
      getDirectories(),
    ])
    environments.value = Array.isArray(envRes) ? envRes : (envRes as any).results || []
    projects.value = Array.isArray(dirRes) ? dirRes : []
  } catch { snackbar.notify(t('common.error'), 'error') }
  loading.value = false
}

const openEditor = (env?: any) => {
  showToken.value = false
  if (env) {
    editingEnv.value = env
    form.value = { name: env.name, code: env.code, project: env.project || null, base_url: env.base_url, token: env.token || '', description: env.description || '', is_active: env.is_active }
  } else {
    editingEnv.value = null
    form.value = { name: '', code: '', project: null, base_url: '', token: '', description: '', is_active: true }
  }
  editorDialog.value = true
}

const save = async () => {
  if (!form.value.name || !form.value.code || !form.value.base_url) {
    snackbar.notify(t('settings.environments.fillRequired'), 'warning'); return
  }
  saving.value = true
  try {
    if (editingEnv.value?.id) await updateEnvironment(editingEnv.value.id, form.value)
    else await createEnvironment(form.value)
    editorDialog.value = false
    snackbar.notify(t('common.saveSuccess'), 'success')
    fetchData()
  } catch (e: any) {
    const msg = e?.response?.data ? Object.values(e.response.data).flat().join('; ') : t('common.error')
    snackbar.notify(msg, 'error')
  }
  saving.value = false
}

const confirmDelete = (env: any) => { deletingEnv.value = env; deleteDialog.value = true }

const doDelete = async () => {
  if (!deletingEnv.value) return
  deleting.value = true
  try {
    await deleteEnvironment(deletingEnv.value.id)
    deleteDialog.value = false
    snackbar.notify(t('common.deleteSuccess'), 'success')
    fetchData()
  } catch { snackbar.notify(t('common.error'), 'error') }
  deleting.value = false
}

onMounted(fetchData)
</script>

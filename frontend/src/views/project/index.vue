<template>
  <v-container fluid>
    <!-- Header -->
    <v-sheet class="pa-4 rounded-xl border-thin" elevation="0" color="surface">
      <v-row dense align="center">
        <v-col>
          <div class="d-flex align-center">
            <v-avatar color="primary" variant="tonal" size="40" class="mr-3">
              <v-icon icon="mdi-folder-multiple-outline" size="22"></v-icon>
            </v-avatar>
            <div>
              <div class="text-h6 font-weight-bold">{{ $t('project.title') }}</div>
              <div class="text-caption text-medium-emphasis">{{ $t('project.subtitle') }}</div>
            </div>
          </div>
        </v-col>
        <v-col cols="auto">
          <v-btn color="primary" prepend-icon="mdi-plus" class="text-none font-weight-bold" @click="openEditor()">
            {{ $t('project.new') }}
          </v-btn>
        </v-col>
      </v-row>
    </v-sheet>

    <!-- Project cards -->
    <v-row class="mt-4">
      <v-col v-for="proj in projects" :key="proj.id" cols="12" md="6" lg="4">
        <v-card class="rounded-xl" elevation="1" hover>
          <v-card-item>
            <template v-slot:prepend>
              <v-avatar color="primary" variant="tonal" size="40">
                <v-icon>mdi-folder-outline</v-icon>
              </v-avatar>
            </template>
            <v-card-title class="text-subtitle-1 font-weight-bold">{{ proj.name }}</v-card-title>
            <v-card-subtitle class="text-caption">
              {{ proj.created_by_name ? $t('project.createdBy', { name: proj.created_by_name }) : '' }}
            </v-card-subtitle>
          </v-card-item>

          <v-card-text class="pt-0 px-4 pb-2">
            <div v-if="proj.description" class="text-body-2 text-grey-darken-1 mb-3" style="white-space: pre-line;">{{ proj.description }}</div>
            <div class="d-flex align-center ga-3">
              <v-chip size="small" color="primary" variant="tonal" prepend-icon="mdi-account-group-outline">
                {{ $t('project.memberCount', { count: proj.member_count }) }}
              </v-chip>
              <v-chip v-if="proj.created_at" size="small" variant="text" class="text-caption text-medium-emphasis">
                {{ formatDate(proj.created_at) }}
              </v-chip>
            </div>
          </v-card-text>

          <v-card-actions class="px-4 pb-3">
            <v-btn variant="tonal" color="info" size="small" prepend-icon="mdi-account-multiple-outline" class="text-none" @click="openMemberDialog(proj)">
              {{ $t('project.members') }}
            </v-btn>
            <v-spacer />
            <v-btn variant="text" color="primary" size="small" icon="mdi-pencil-outline" @click="openEditor(proj)" />
            <v-btn variant="text" color="error" size="small" icon="mdi-delete-outline" @click="confirmDelete(proj)" />
          </v-card-actions>
        </v-card>
      </v-col>

      <v-col v-if="!loading && !projects.length" cols="12">
        <v-empty-state icon="mdi-folder-multiple-outline" :title="$t('project.empty')" class="py-10">
          <template v-slot:actions>
            <v-btn color="primary" prepend-icon="mdi-plus" class="text-none" @click="openEditor()">
              {{ $t('project.createFirst') }}
            </v-btn>
          </template>
        </v-empty-state>
      </v-col>
    </v-row>

    <!-- Edit Dialog -->
    <v-dialog v-model="editorDialog" max-width="540" persistent>
      <v-card class="rounded-xl" elevation="8">
        <v-toolbar color="primary" density="compact">
          <v-btn icon="mdi-close" variant="text" @click="editorDialog = false" />
          <v-toolbar-title class="text-subtitle-1 font-weight-bold">
            {{ editingProject?.id ? $t('project.edit') : $t('project.new') }}
          </v-toolbar-title>
          <v-spacer />
          <v-btn variant="text" class="text-none font-weight-bold" @click="save" :loading="saving">
            {{ $t('common.save') }}
          </v-btn>
        </v-toolbar>

        <v-card-text class="pa-6">
          <v-text-field v-model="form.name" :label="$t('project.nameLabel')" variant="outlined" density="compact" class="mb-4" :rules="[v => !!v || $t('common.required')]" />
          <v-textarea v-model="form.description" :label="$t('project.descriptionLabel')" variant="outlined" density="compact" rows="3" auto-grow class="mb-2" />
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
          {{ $t('project.deleteConfirm', { name: deletingProject?.name }) }}
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn color="grey-darken-1" variant="text" @click="deleteDialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="error" variant="flat" class="ml-2" @click="doDelete" :loading="deleting">{{ $t('common.delete') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Member Management Dialog -->
    <v-dialog v-model="memberDialog" max-width="680" persistent>
      <v-card class="rounded-xl" elevation="8">
        <v-toolbar color="info" density="compact">
          <v-btn icon="mdi-close" variant="text" @click="memberDialog = false" />
          <v-toolbar-title class="text-subtitle-1 font-weight-bold">
            {{ $t('project.memberManagement') }} - {{ memberProject?.name }}
          </v-toolbar-title>
        </v-toolbar>

        <v-card-text class="pa-4">
          <!-- Add member form -->
          <v-sheet class="pa-3 rounded-lg mb-4 border-thin" color="surface-variant">
            <div class="text-subtitle-2 font-weight-bold mb-2">{{ $t('project.addMember') }}</div>
            <v-row dense align="center">
              <v-col cols="12" sm="5">
                <v-autocomplete
                  v-model="newMember.user"
                  :items="userOptions"
                  :loading="searchingUsers"
                  item-title="username"
                  item-value="id"
                  return-object
                  :label="$t('project.selectUser')"
                  variant="outlined"
                  density="compact"
                  hide-details
                  clearable
                  @update:search="onUserSearch"
                >
                  <template v-slot:item="{ item, props: itemProps }">
                    <v-list-item v-bind="itemProps">
                      <template v-slot:subtitle>{{ item.raw.email }}</template>
                    </v-list-item>
                  </template>
                </v-autocomplete>
              </v-col>
              <v-col cols="12" sm="4">
                <v-select
                  v-model="newMember.role"
                  :items="roleOptions"
                  item-title="label"
                  item-value="value"
                  :label="$t('project.role')"
                  variant="outlined"
                  density="compact"
                  hide-details
                />
              </v-col>
              <v-col cols="12" sm="3">
                <v-btn color="primary" block class="text-none" :disabled="!newMember.user" :loading="addingMember" @click="doAddMember">
                  {{ $t('project.addMemberBtn') }}
                </v-btn>
              </v-col>
            </v-row>
          </v-sheet>

          <!-- Member list -->
          <v-table density="compact" hover>
            <thead>
              <tr>
                <th>{{ $t('project.username') }}</th>
                <th>{{ $t('project.email') }}</th>
                <th>{{ $t('project.role') }}</th>
                <th>{{ $t('project.joinedAt') }}</th>
                <th class="text-center">{{ $t('common.actions') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="m in members" :key="m.id">
                <td class="font-weight-medium">{{ m.username }}</td>
                <td class="text-caption text-grey-darken-1">{{ m.email || '-' }}</td>
                <td>
                  <v-select
                    :model-value="m.role"
                    :items="roleOptions"
                    item-title="label"
                    item-value="value"
                    variant="plain"
                    density="compact"
                    hide-details
                    style="max-width: 130px;"
                    @update:model-value="(val: string) => doUpdateRole(m, val)"
                  />
                </td>
                <td class="text-caption">{{ formatDate(m.joined_at) }}</td>
                <td class="text-center">
                  <v-btn icon="mdi-account-remove-outline" variant="text" color="error" size="small" @click="doRemoveMember(m)" :disabled="m.role === 'owner' && ownerCount <= 1" />
                </td>
              </tr>
              <tr v-if="!membersLoading && !members.length">
                <td colspan="5" class="text-center text-caption text-grey py-4">{{ $t('common.noData') }}</td>
              </tr>
            </tbody>
          </v-table>
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useSnackbarStore } from '@/store/snackbar'
import {
  getProjects, createProject, updateProject, deleteProject,
  getProjectMembers, addProjectMember, removeProjectMember, updateMemberRole,
  searchUsers,
  type Project, type ProjectMember as PM, type SimpleUser,
} from '@/api/project'

const { t } = useI18n()
const snackbar = useSnackbarStore()

const projects = ref<Project[]>([])
const loading = ref(false)
const editorDialog = ref(false)
const deleteDialog = ref(false)
const memberDialog = ref(false)
const saving = ref(false)
const deleting = ref(false)

const editingProject = ref<Project | null>(null)
const deletingProject = ref<Project | null>(null)
const memberProject = ref<Project | null>(null)

const form = ref({ name: '', description: '' })

const members = ref<PM[]>([])
const membersLoading = ref(false)
const addingMember = ref(false)
const searchingUsers = ref(false)
const userOptions = ref<SimpleUser[]>([])
const newMember = ref<{ user: SimpleUser | null; role: string }>({ user: null, role: 'member' })

let searchTimer: ReturnType<typeof setTimeout> | null = null

const roleOptions = computed(() => [
  { value: 'owner', label: t('project.roles.owner') },
  { value: 'admin', label: t('project.roles.admin') },
  { value: 'member', label: t('project.roles.member') },
  { value: 'viewer', label: t('project.roles.viewer') },
])

const ownerCount = computed(() => members.value.filter(m => m.role === 'owner').length)

const formatDate = (d: string) => d ? new Date(d).toLocaleDateString() : '-'

const fetchProjects = async () => {
  loading.value = true
  try {
    const res = await getProjects()
    projects.value = Array.isArray(res) ? res : []
  } catch {
    snackbar.notify(t('common.error'), 'error')
  }
  loading.value = false
}

const openEditor = (proj?: Project) => {
  if (proj) {
    editingProject.value = proj
    form.value = { name: proj.name, description: proj.description || '' }
  } else {
    editingProject.value = null
    form.value = { name: '', description: '' }
  }
  editorDialog.value = true
}

const save = async () => {
  if (!form.value.name) {
    snackbar.notify(t('common.required'), 'warning')
    return
  }
  saving.value = true
  try {
    if (editingProject.value?.id) {
      await updateProject(editingProject.value.id, form.value)
    } else {
      await createProject(form.value)
    }
    editorDialog.value = false
    snackbar.notify(t('common.saveSuccess'), 'success')
    fetchProjects()
  } catch (e: any) {
    const msg = e?.response?.data ? Object.values(e.response.data).flat().join('; ') : t('common.error')
    snackbar.notify(msg, 'error')
  }
  saving.value = false
}

const confirmDelete = (proj: Project) => {
  deletingProject.value = proj
  deleteDialog.value = true
}

const doDelete = async () => {
  if (!deletingProject.value) return
  deleting.value = true
  try {
    await deleteProject(deletingProject.value.id)
    deleteDialog.value = false
    snackbar.notify(t('common.deleteSuccess'), 'success')
    fetchProjects()
  } catch {
    snackbar.notify(t('common.error'), 'error')
  }
  deleting.value = false
}

// ----- Member management -----

const openMemberDialog = async (proj: Project) => {
  memberProject.value = proj
  newMember.value = { user: null, role: 'member' }
  userOptions.value = []
  memberDialog.value = true
  await fetchMembers()
}

const fetchMembers = async () => {
  if (!memberProject.value) return
  membersLoading.value = true
  try {
    members.value = await getProjectMembers(memberProject.value.id)
  } catch {
    snackbar.notify(t('common.error'), 'error')
  }
  membersLoading.value = false
}

const onUserSearch = (val: string) => {
  if (searchTimer) clearTimeout(searchTimer)
  if (!val || val.length < 1) return
  searchTimer = setTimeout(async () => {
    searchingUsers.value = true
    try {
      userOptions.value = await searchUsers(val)
    } catch { /* ignore */ }
    searchingUsers.value = false
  }, 300)
}

const doAddMember = async () => {
  if (!memberProject.value || !newMember.value.user) return
  addingMember.value = true
  try {
    await addProjectMember(memberProject.value.id, {
      user_id: newMember.value.user.id,
      role: newMember.value.role,
    })
    snackbar.notify(t('common.success'), 'success')
    newMember.value = { user: null, role: 'member' }
    await fetchMembers()
    fetchProjects()
  } catch (e: any) {
    const msg = e?.response?.data?.error || t('common.error')
    snackbar.notify(msg, 'error')
  }
  addingMember.value = false
}

const doRemoveMember = async (m: PM) => {
  if (!memberProject.value) return
  try {
    await removeProjectMember(memberProject.value.id, m.user_id)
    snackbar.notify(t('common.deleteSuccess'), 'success')
    await fetchMembers()
    fetchProjects()
  } catch (e: any) {
    const msg = e?.response?.data?.error || t('common.error')
    snackbar.notify(msg, 'error')
  }
}

const doUpdateRole = async (m: PM, newRole: string) => {
  if (!memberProject.value || newRole === m.role) return
  try {
    await updateMemberRole(memberProject.value.id, { user_id: m.user_id, role: newRole })
    snackbar.notify(t('common.saveSuccess'), 'success')
    await fetchMembers()
  } catch (e: any) {
    const msg = e?.response?.data?.error || t('common.error')
    snackbar.notify(msg, 'error')
  }
}

onMounted(fetchProjects)
</script>

<template>
  <div class="d-flex flex-column fill-height">
    <div class="px-4 d-flex align-center border-b" style="height: 64px; flex-shrink: 0;">
      <span class="text-h6 font-weight-bold">{{ $t('common.interfaces') }}</span>
      <v-spacer></v-spacer>
      <v-btn
        icon="mdi-folder-plus"
        variant="text"
        size="small"
        color="primary"
        @click="openDirDialog()"
        :title="$t('generation.addRootDirectory')"
      ></v-btn>
      <v-btn
        icon="mdi-refresh"
        variant="text"
        size="small"
        color="grey"
        class="ml-1"
        @click="loadData"
        :title="$t('common.refresh')"
      ></v-btn>
    </div>

    <div class="flex-grow-1 overflow-y-auto pa-2">
      <v-list density="compact" nav v-if="items.length > 0">
        <template v-for="item in items" :key="item.id">
          <dir-tree-item
            :item="item"
            :active-id="activeId"
            @select="handleSelect"
            @add-dir="openDirDialog($event)"
            @edit-dir="openEditDialog($event)"
            @delete-dir="handleDeleteDir"
          />
        </template>
      </v-list>
      <v-empty-state
        v-else
        icon="mdi-folder-outline"
        :title="$t('common.noData')"
        class="mt-10"
      ></v-empty-state>
    </div>

    <!-- 目录 Dialog -->
    <v-dialog v-model="dirDialog" max-width="500">
      <v-card class="rounded-xl">
        <v-toolbar color="primary" density="compact">
          <v-toolbar-title class="text-subtitle-1 font-weight-bold">
            {{ isEditMode ? $t('generation.editDirectory') : $t('generation.addSubDirectory') }}
          </v-toolbar-title>
        </v-toolbar>
        <v-card-text class="pa-4">
          <v-text-field
            v-model="dirForm.name"
            :label="$t('generation.directoryName')"
            variant="outlined"
            density="compact"
            autofocus
          ></v-text-field>
        </v-card-text>
        <v-card-actions class="px-6 pb-4">
          <v-spacer></v-spacer>
          <v-btn color="grey-darken-1" variant="text" class="text-none" @click="dirDialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="primary" variant="flat" class="text-none ml-3" @click="saveDirectory">{{ $t('common.save') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card class="rounded-xl">
        <v-toolbar color="error" density="compact">
          <v-toolbar-title class="text-subtitle-1 font-weight-bold">{{ $t('common.delete') }}</v-toolbar-title>
        </v-toolbar>
        <v-card-text class="pa-4 text-body-2">
          {{ deleteItemName ? $t('common.confirmDelete', { name: deleteItemName }) : '' }}
        </v-card-text>
        <v-card-actions class="px-6 pb-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" color="grey-darken-1" class="text-none" @click="deleteDialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="error" variant="flat" class="text-none ml-3" @click="confirmDelete">{{ $t('common.delete') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import DirTreeItem from './DirTreeItem.vue'
import { getDirectories, createDirectory, updateDirectory, deleteDirectory } from '@/api/directory'
import type { Directory } from '@/api/directory'

const { t } = useI18n()
const emit = defineEmits(['select'])

const items = ref<any[]>([])
const activeId = ref<number | null>(null)

const dirDialog = ref(false)
const deleteDialog = ref(false)
const isEditMode = ref(false)
const dirForm = ref({ id: 0, name: '', parent: undefined as number | undefined })
const deleteItemId = ref<number | null>(null)
const deleteItemName = ref('')

const loadData = async () => {
  try {
    const dirs = await getDirectories()
    items.value = buildDirTree(dirs)
  } catch (e) {
    console.error(e)
  }
}

const buildDirTree = (dirs: Directory[]): any[] => {
  const processDir = (dir: Directory): any => {
    const subDirs = dir.sub_directories ? dir.sub_directories.map(processDir) : []
    return { ...dir, type: 'directory', children: subDirs }
  }
  return dirs.map(processDir)
}

const handleSelect = (item: any) => {
  activeId.value = item.id
  emit('select', item.id)
}

const openDirDialog = (parent?: any) => {
  isEditMode.value = false
  dirForm.value = { id: 0, name: '', parent: parent?.id }
  dirDialog.value = true
}

const openEditDialog = (item: any) => {
  isEditMode.value = true
  dirForm.value = { id: item.id, name: item.name, parent: undefined }
  dirDialog.value = true
}

const saveDirectory = async () => {
  try {
    if (dirForm.value.id) {
      await updateDirectory(dirForm.value.id, { name: dirForm.value.name })
    } else {
      await createDirectory({ name: dirForm.value.name, parent: dirForm.value.parent })
    }
    dirDialog.value = false
    loadData()
  } catch (e) {
    console.error(e)
  }
}

const handleDeleteDir = (item: any) => {
  deleteItemId.value = item.id
  deleteItemName.value = item.name
  deleteDialog.value = true
}

const confirmDelete = async () => {
  if (!deleteItemId.value) return
  try {
    await deleteDirectory(deleteItemId.value)
    if (activeId.value === deleteItemId.value) {
      activeId.value = null
      emit('select', null)
    }
    loadData()
  } catch (e) {
    console.error(e)
  } finally {
    deleteDialog.value = false
  }
}

defineExpose({ refresh: loadData })

onMounted(() => {
  loadData()
})
</script>

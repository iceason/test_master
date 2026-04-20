<template>
  <v-container fluid class="fill-height pa-4">
    <v-row no-gutters class="fill-height">
      <!-- 左侧目录树 -->
      <v-col cols="12" md="3" class="d-flex flex-column fill-height">
        <v-card class="flex-grow-1 d-flex flex-column overflow-hidden" elevation="1" style="border-top-right-radius: 0; border-bottom-right-radius: 0;">
          <DirectoryTree ref="dirTreeRef" @select="handleDirSelect" />
        </v-card>
      </v-col>

      <!-- 右侧接口列表 -->
      <v-col cols="12" md="9" class="d-flex flex-column fill-height">
        <v-card class="flex-grow-1 d-flex flex-column overflow-hidden" elevation="1" style="border-top-left-radius: 0; border-bottom-left-radius: 0;">
          <!-- 操作栏 -->
          <div class="pa-4 border-b" style="flex-shrink: 0;">
            <v-row dense align="center">
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="search"
                  :label="$t('common.search')"
                  prepend-inner-icon="mdi-magnify"
                  density="compact"
                  variant="outlined"
                  hide-details
                  clearable
                  class="rounded-lg"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="3">
                <v-select
                  v-model="filters.method"
                  :items="['GET', 'POST', 'PUT', 'DELETE', 'PATCH']"
                  :label="$t('interface.fields.method')"
                  density="compact"
                  variant="outlined"
                  hide-details
                  clearable
                  class="rounded-lg"
                ></v-select>
              </v-col>
              <v-spacer></v-spacer>
              <v-col cols="12" md="auto" class="d-flex justify-end">
                <v-btn
                  color="secondary"
                  variant="tonal"
                  prepend-icon="mdi-file-import"
                  @click="importDialog = true"
                  class="text-none"
                  size="small"
                >
                  {{ $t('interface.importOpenAPI') }}
                </v-btn>
                <v-btn
                  color="error"
                  variant="tonal"
                  prepend-icon="mdi-delete-outline"
                  @click="handleBatchDelete()"
                  class="text-none ml-2"
                  size="small"
                >
                  {{ $t('common.batchDelete') }}
                </v-btn>
                <v-btn color="primary" prepend-icon="mdi-plus" @click="openDialog()" class="text-none ml-2" size="small">
                  {{ $t('interface.new') }}
                </v-btn>
              </v-col>
            </v-row>
          </div>

          <!-- 数据表格 -->
          <div class="flex-grow-1 overflow-hidden">
            <v-data-table-virtual
              :headers="customHeaders"
              :items="filteredItems"
              :loading="loading"
              :search="search"
              fixed-header
              height="100%"
              hover
              item-key="id"
              item-height="48"
            >
              <template v-slot:header.select>
                <v-checkbox
                  v-model="isAllSelected"
                  :indeterminate="selectedIds.length > 0 && selectedIds.length < filteredItems.length"
                  @change="toggleSelectAll"
                  hide-details
                ></v-checkbox>
              </template>

              <template v-slot:item.select="{ item }">
                <v-checkbox
                  :model-value="selectedIdsSet.has(item.id)"
                  @update:model-value="toggleItemSelection(item.id)"
                  hide-details
                ></v-checkbox>
              </template>

              <template v-slot:item.method="{ item }">
                <v-chip :color="getMethodColor(item.method)" size="small" label class="font-weight-bold">
                  {{ item.method.toUpperCase() }}
                </v-chip>
              </template>

              <template v-slot:item.path="{ item }">
                <code class="text-grey-darken-3 bg-grey-lighten-4 px-1 rounded">{{ item.path }}</code>
              </template>

              <template v-slot:item.directory="{ item }">
                {{ getDirectoryName(item.directory) }}
              </template>

              <template v-slot:item.actions="{ item }">
                <v-tooltip location="top" :text="$t('interface.generateTestCases')">
                  <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" icon="mdi-test-tube" variant="text" size="small" color="success" @click="handleGenerate(item)"></v-btn>
                  </template>
                </v-tooltip>
                <v-tooltip location="top" :text="$t('common.edit')">
                  <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" icon="mdi-pencil" variant="text" size="small" color="primary" @click="openDialog(item)"></v-btn>
                  </template>
                </v-tooltip>
                <v-tooltip location="top" :text="$t('common.delete')">
                  <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" icon="mdi-delete" variant="text" size="small" color="error" @click="handleDelete(item)"></v-btn>
                  </template>
                </v-tooltip>
              </template>

              <template v-slot:no-data>
                <v-empty-state icon="mdi-database-off" :title="$t('common.noData')" class="py-10"></v-empty-state>
              </template>
            </v-data-table-virtual>
          </div>
        </v-card>
      </v-col>
    </v-row>

    <!-- Create/Edit Dialog -->
    <v-dialog v-model="dialog" max-width="800px" persistent>
      <v-card class="rounded-xl">
        <v-toolbar color="primary" density="compact">
          <v-toolbar-title class="text-subtitle-1 font-weight-bold">{{ editedId ? $t('interface.edit') : $t('interface.new') }}</v-toolbar-title>
        </v-toolbar>
        <v-card-text class="pa-4">
          <v-form ref="form" v-model="valid">
            <v-row>
              <v-col cols="12" md="8">
                <v-text-field
                  v-model="editedItem.name"
                  :label="$t('interface.fields.name')"
                  :rules="[v => !!v || $t('common.required')]"
                  variant="outlined"
                  density="compact"
                  required
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="4">
                <v-select
                  v-model="editedItem.method"
                  :items="['GET', 'POST', 'PUT', 'DELETE', 'PATCH']"
                  :label="$t('interface.fields.method')"
                  :rules="[v => !!v || $t('common.required')]"
                  variant="outlined"
                  density="compact"
                  required
                ></v-select>
              </v-col>
              <v-col cols="12" md="8">
                <v-text-field
                  v-model="editedItem.path"
                  :label="$t('interface.fields.path')"
                  :rules="[v => !!v || $t('common.required')]"
                  variant="outlined"
                  density="compact"
                  required
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="4">
                <v-select
                  v-model="editedItem.directory"
                  :items="flatDirs"
                  item-title="name"
                  item-value="id"
                  :label="$t('interface.fields.directory')"
                  :rules="[v => !!v || $t('common.required')]"
                  variant="outlined"
                  density="compact"
                  required
                ></v-select>
              </v-col>
              <v-col cols="12">
                <v-textarea
                  v-model="editedItem.schema_yaml"
                  :label="$t('interface.fields.schema')"
                  variant="outlined"
                  rows="10"
                  class="font-monospace"
                  hint="Enter JSON or YAML format"
                  persistent-hint
                ></v-textarea>
              </v-col>
            </v-row>
          </v-form>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="px-6 pb-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" color="grey-darken-1" class="text-none" @click="dialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="primary" variant="flat" class="text-none ml-3" @click="save" :disabled="!valid">{{ $t('common.save') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="400px">
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

    <!-- Batch Delete Confirmation Dialog -->
    <v-dialog v-model="batchDeleteDialog" max-width="400px">
      <v-card class="rounded-xl">
        <v-toolbar color="error" density="compact">
          <v-toolbar-title class="text-subtitle-1 font-weight-bold">{{ $t('common.batchDelete') }}</v-toolbar-title>
        </v-toolbar>
        <v-card-text class="pa-4 text-body-2">
          {{ $t('common.confirmBatchDelete', { count: selectedIds.length }) }}
        </v-card-text>
        <v-card-actions class="px-6 pb-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" color="grey-darken-1" class="text-none" @click="batchDeleteDialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="error" variant="flat" class="text-none ml-3" @click="confirmBatchDelete">{{ $t('common.delete') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Generation Loading Dialog -->
    <v-dialog v-model="generating" hide-overlay persistent width="300">
      <v-card color="primary" dark class="pa-4 text-center rounded-xl">
        <v-card-text class="text-white">
          {{ $t('interface.generating') }}
          <v-progress-linear indeterminate color="white" class="mb-0 mt-4"></v-progress-linear>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Import OpenAPI Dialog -->
    <ImportDialog v-model="importDialog" @imported="onImported" />

    <v-snackbar v-model="snackbar" :color="snackbarColor" location="top right">
      {{ snackbarText }}
      <template v-slot:actions>
        <v-btn variant="text" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { getInterfaces, createInterface, updateInterface, deleteInterface, generateTestCases, batchDeleteInterfaces } from '@/api/interface'
import { getDirectories } from '@/api/directory'
import type { Interface } from '@/api/interface'
import type { Directory } from '@/api/directory'
import ImportDialog from './components/ImportDialog.vue'
import DirectoryTree from './components/DirectoryTree.vue'

const { t } = useI18n()

const loading = ref(false)
const generating = ref(false)
const dialog = ref(false)
const valid = ref(false)
const items = ref<Interface[]>([])
const directories = ref<Directory[]>([])
const flatDirs = ref<{ id: number; name: string }[]>([])
const editedId = ref<number | null>(null)
const deleteDialog = ref(false)
const batchDeleteDialog = ref(false)
const deleteItemId = ref<number | null>(null)
const deleteItemName = ref('')
const snackbar = ref(false)
const snackbarText = ref('')
const snackbarColor = ref('success')
const search = ref('')
const importDialog = ref(false)
const selectedDirId = ref<number | null>(null)
const dirTreeRef = ref<any>(null)
const filters = ref({ method: null as string | null })

const defaultItem: Partial<Interface> = {
  name: '',
  method: 'GET',
  path: '',
  directory: undefined,
  schema_yaml: ''
}

const editedItem = ref<Partial<Interface>>({ ...defaultItem })

const customHeaders = computed(() => [
  { title: '', key: 'select', sortable: false, width: '50px', align: 'center' as const },
  { title: t('interface.fields.id'), key: 'id', align: 'start' as const },
  { title: t('interface.fields.name'), key: 'name' },
  { title: t('interface.fields.method'), key: 'method' },
  { title: t('interface.fields.path'), key: 'path' },
  { title: t('interface.fields.directory'), key: 'directory' },
  { title: t('common.actions'), key: 'actions', sortable: false, align: 'end' as const },
])

const selectedIdsSet = ref(new Set<number>())
const selectedIds = computed(() => Array.from(selectedIdsSet.value))

const selectedItems = computed(() => {
  return filteredItems.value.filter(item => selectedIdsSet.value.has(item.id))
})

const toggleItemSelection = (id: number) => {
  if (selectedIdsSet.value.has(id)) {
    selectedIdsSet.value.delete(id)
  } else {
    selectedIdsSet.value.add(id)
  }
}

const toggleSelectAll = () => {
  if (selectedIds.value.length === filteredItems.value.length) {
    selectedIdsSet.value.clear()
  } else {
    selectedIdsSet.value = new Set(filteredItems.value.map(item => item.id))
  }
}

const isAllSelected = computed(() => {
  return filteredItems.value.length > 0 && selectedIds.value.length === filteredItems.value.length
})

const filteredItems = computed(() => {
  return items.value.filter(item => {
    if (filters.value.method && item.method !== filters.value.method) return false
    return true
  })
})

const flattenDirs = (dirs: Directory[]): { id: number; name: string }[] => {
  let result: { id: number; name: string }[] = []
  for (const dir of dirs) {
    result.push({ id: dir.id, name: dir.name })
    if (dir.sub_directories) {
      result = result.concat(flattenDirs(dir.sub_directories))
    }
  }
  return result
}

const loadInterfaces = async () => {
  loading.value = true
  try {
    const params: any = { no_page: true }
    if (selectedDirId.value) {
      params.directory = selectedDirId.value
    }
    items.value = await getInterfaces(params)
  } catch (error) {
    showMsg(t('common.error'), 'error')
  } finally {
    loading.value = false
  }
}

const loadDirectories = async () => {
  try {
    const dirsData = await getDirectories()
    directories.value = dirsData
    flatDirs.value = flattenDirs(dirsData)
  } catch (error) {
    console.error(error)
  }
}

const loadData = async () => {
  await Promise.all([loadInterfaces(), loadDirectories()])
}

const handleDirSelect = (dirId: number | null) => {
  selectedDirId.value = dirId
  selectedIdsSet.value.clear()
  loadInterfaces()
}

const getMethodColor = (method: string) => {
  const colors: Record<string, string> = { GET: 'blue', POST: 'green', PUT: 'orange', DELETE: 'red', PATCH: 'purple' }
  return colors[method.toUpperCase()] || 'grey'
}

const getDirectoryName = (id: number) => {
  const dir = flatDirs.value.find(d => d.id === id)
  return dir ? dir.name : id
}

const openDialog = (item?: Interface) => {
  if (item) {
    editedId.value = item.id
    let schemaStr = ''
    if (item.schema) {
      schemaStr = JSON.stringify(item.schema, null, 2)
    }
    editedItem.value = { ...item, schema_yaml: schemaStr }
  } else {
    editedId.value = null
    editedItem.value = { ...defaultItem }
    if (selectedDirId.value) {
      editedItem.value.directory = selectedDirId.value
    } else if (flatDirs.value.length > 0) {
      editedItem.value.directory = flatDirs.value[0].id
    }
  }
  dialog.value = true
}

const save = async () => {
  try {
    if (editedItem.value.schema_yaml) {
      try { JSON.parse(editedItem.value.schema_yaml) } catch (e) { /* YAML handled by backend */ }
    }
    if (editedId.value) {
      await updateInterface(editedId.value, editedItem.value)
    } else {
      await createInterface(editedItem.value)
    }
    showMsg(t('common.success'))
    dialog.value = false
    loadInterfaces()
    dirTreeRef.value?.refresh()
  } catch (error) {
    showMsg(t('common.error'), 'error')
  }
}

const handleDelete = (item: Interface) => {
  deleteItemId.value = item.id
  deleteItemName.value = item.name
  deleteDialog.value = true
}

const confirmDelete = async () => {
  if (deleteItemId.value) {
    try {
      await deleteInterface(deleteItemId.value)
      showMsg(t('common.success'))
      loadInterfaces()
    } catch (error) {
      showMsg(t('common.error'), 'error')
    } finally {
      deleteDialog.value = false
    }
  }
}

const handleBatchDelete = () => {
  if (selectedIds.value.length > 0) {
    batchDeleteDialog.value = true
  } else {
    showMsg(t('common.noSelectedItems'), 'warning')
  }
}

const confirmBatchDelete = async () => {
  if (selectedIds.value.length > 0) {
    try {
      await batchDeleteInterfaces(selectedIds.value)
      showMsg(t('common.success'))
      loadInterfaces()
      selectedIdsSet.value.clear()
    } catch (error) {
      showMsg(t('common.error'), 'error')
    } finally {
      batchDeleteDialog.value = false
    }
  }
}

const handleGenerate = async (item: Interface) => {
  generating.value = true
  try {
    await generateTestCases(item.id)
    showMsg(t('common.success'))
  } catch (error) {
    showMsg(t('common.error'), 'error')
  } finally {
    generating.value = false
  }
}

const onImported = () => {
  showMsg(t('interface.importSuccess'))
  loadInterfaces()
  dirTreeRef.value?.refresh()
}

const showMsg = (text: string, color = 'success') => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.font-monospace :deep(textarea) {
  font-family: monospace;
}
</style>

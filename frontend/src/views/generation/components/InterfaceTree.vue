<template>
  <div class="d-flex flex-column fill-height">
    <!-- 头部操作栏 -->
    <div class="pa-4 d-flex align-center border-b">
      <span class="text-subtitle-1 font-weight-bold">{{ $t('common.interfaces') }}</span>
      <v-spacer></v-spacer>
      <v-btn
        icon="mdi-folder-plus"
        variant="text"
        size="small"
        color="primary"
        rounded="lg"
        @click="openDirDialog()"
        :title="$t('generation.addRootDirectory')"
      ></v-btn>
      <v-btn
        icon="mdi-refresh"
        variant="text"
        size="small"
        color="grey"
        rounded="lg"
        class="ml-1"
        @click="loadData"
        :title="$t('common.refresh')"
      ></v-btn>
    </div>

    <!-- 树形内容 -->
    <div class="flex-grow-1 overflow-y-auto pa-2">
      <v-list density="compact" nav v-if="items.length > 0">
        <template v-for="item in items" :key="item.id">
          <!-- 递归组件渲染目录结构 -->
          <tree-item
            :item="item"
            :active-id="activeId"
            @select="handleSelect"
            @add-dir="openDirDialog"
            @add-interface="openInterfaceDialog"
            @edit-dir="openDirDialog"
            @delete-dir="handleDeleteDir"
            @delete-interface="handleDeleteInterface"
            @move-interface="openMoveDialog"
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
        <v-card-title class="bg-primary text-white pa-4">
          <span class="text-h6">
            {{ dirForm.id ? $t('generation.editDirectory') : 
               (dirLevel === 1 ? $t('generation.addProject') : 
                (dirLevel === 2 ? $t('generation.addModule') : $t('generation.addSubDirectory'))) }}
          </span>
        </v-card-title>
        <v-card-text class="pa-4">
          <v-text-field
            v-model="dirForm.name"
            :label="(dirLevel === 1 ? $t('generation.projectName') : 
                  (dirLevel === 2 ? $t('generation.moduleName') : 
                   $t('generation.directoryName')))"
            variant="outlined"
            density="compact"
            autofocus
          ></v-text-field>
        </v-card-text>
        <v-card-actions class="px-6 pb-4">
          <v-spacer></v-spacer>
          <v-btn color="grey-darken-1" variant="text" rounded="lg" class="text-none" @click="dirDialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="primary" variant="flat" rounded="lg" class="text-none ml-3" @click="saveDirectory">{{ $t('common.save') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 接口 Dialog -->
    <v-dialog v-model="interfaceDialog" max-width="600">
      <v-card class="rounded-xl">
        <v-card-title class="bg-primary text-white pa-4">
          <span class="text-h6">{{ $t('generation.addInterface') }}</span>
        </v-card-title>
        <v-card-text class="pa-4">
          <v-container class="pa-0">
            <v-row dense>
              <v-col cols="12">
                <v-text-field
                  v-model="interfaceForm.name"
                  :label="$t('interface.fields.name')"
                  variant="outlined"
                  density="compact"
                ></v-text-field>
              </v-col>
              <v-col cols="4">
                <v-select
                  v-model="interfaceForm.method"
                  :items="['GET', 'POST', 'PUT', 'DELETE', 'PATCH']"
                  :label="$t('interface.fields.method')"
                  variant="outlined"
                  density="compact"
                ></v-select>
              </v-col>
              <v-col cols="8">
                <v-text-field
                  v-model="interfaceForm.path"
                  :label="$t('interface.fields.path')"
                  variant="outlined"
                  density="compact"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-textarea
                  v-model="interfaceForm.schema_yaml"
                  :label="$t('interface.fields.schema')"
                  variant="outlined"
                  rows="6"
                  class="font-monospace"
                  hint="JSON or YAML"
                ></v-textarea>
              </v-col>
            </v-row>
          </v-container>
        </v-card-text>
        <v-card-actions class="px-6 pb-4">
          <v-spacer></v-spacer>
          <v-btn color="grey-darken-1" variant="text" rounded="lg" class="text-none" @click="interfaceDialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="primary" variant="flat" rounded="lg" class="text-none ml-3" @click="saveInterface">{{ $t('common.save') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 移动接口 Dialog -->
    <v-dialog v-model="moveDialog" max-width="500">
      <v-card class="rounded-xl">
        <v-card-title class="bg-primary text-white pa-4">
          <span class="text-h6">{{ $t('generation.moveInterface') }}</span>
        </v-card-title>
        <v-card-text class="pa-4">
          <v-select
            v-model="moveTargetId"
            :items="flatDirectories"
            item-title="name"
            item-value="id"
            :label="$t('generation.targetDirectory')"
            variant="outlined"
            density="compact"
          ></v-select>
        </v-card-text>
        <v-card-actions class="px-6 pb-4">
          <v-spacer></v-spacer>
          <v-btn color="grey-darken-1" variant="text" rounded="lg" class="text-none" @click="moveDialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="primary" variant="flat" rounded="lg" class="text-none ml-3" @click="saveMove">{{ $t('common.save') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="400px">
      <v-card class="rounded-xl">
        <v-card-title class="text-h6 pa-4 bg-error text-white">
          {{ $t('common.delete') }}
        </v-card-title>
        <v-card-text class="pa-4 text-body-1">
          {{ deleteItemName ? $t('common.confirmDelete', { name: deleteItemName }) : '' }}
        </v-card-text>
        <v-card-actions class="px-6 pb-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" color="grey-darken-1" rounded="lg" class="text-none" @click="deleteDialog = false">
            {{ $t('common.cancel') }}
          </v-btn>
          <v-btn color="error" variant="flat" rounded="lg" class="text-none ml-3" @click="confirmDelete">
            {{ $t('common.delete') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import TreeItem from './TreeItem.vue'
import { getDirectories, createDirectory, updateDirectory, deleteDirectory } from '@/api/directory'
import { getInterfaces, createInterface, deleteInterface, updateInterface } from '@/api/interface'
import type { Directory } from '@/api/directory'
import type { Interface } from '@/api/interface'

import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const emit = defineEmits(['select'])

// 数据状态
const items = ref<any[]>([])
const activeId = ref<string>('')
const flatDirectories = ref<any[]>([]) // 用于移动接口时的选择列表

// Dialog 状态
const dirDialog = ref(false)
const interfaceDialog = ref(false)
const moveDialog = ref(false)
const deleteDialog = ref(false)

// 表单数据
const dirForm = ref({ id: 0, name: '', parent: undefined as number | undefined })
// 目录层级 - 1: 根目录, 2: 项目, 3: 模块, 4+: 子目录
const dirLevel = ref(1)
const interfaceForm = ref({ 
  name: '', 
  method: 'GET', 
  path: '', 
  directory: 0, 
  schema_yaml: '' 
})
const moveInterfaceId = ref(0)
const moveTargetId = ref<number | null>(null)
const deleteItemType = ref<'directory' | 'interface'>('directory')
const deleteItemId = ref<number | null>(null)
const deleteItemName = ref('')

// 加载数据
const loadData = async () => {
  try {
    const [dirs, ifaces] = await Promise.all([
      getDirectories(),
      getInterfaces({ no_page: true })
    ])
    items.value = buildTree(dirs, ifaces)
    flatDirectories.value = flattenDirs(items.value)
  } catch (e) {
    console.error(e)
  }
}

// 构建树形结构
const buildTree = (dirs: Directory[], ifaces: Interface[]) => {
  const map = new Map()
  
  // 初始化目录节点
  dirs.forEach(d => {
    map.set(d.id, { 
      ...d, 
      type: 'directory', 
      children: [],
      interfaces: [] // 暂存接口
    })
  })

  // 分配接口到目录
  ifaces.forEach(i => {
    const dir = map.get(i.directory)
    if (dir) {
      dir.interfaces.push({ ...i, type: 'interface' })
    }
  })

  const tree: any[] = []
  
  // 构建目录树
    dirs.forEach(d => {
      const node = map.get(d.id)
      // 合并子目录和接口作为 children
      node.children = [
        ...(d.sub_directories?.map(sub => map.get(sub.id)).filter(Boolean) || []),
        ...node.interfaces
      ]
      
      // 如果是根目录 (根据 API 返回逻辑，这里假设 getDirectories 返回所有目录，需自行组装树)
      // 实际上 API 返回的是根目录列表，包含 sub_directories。
      // 所以我们需要递归处理
    })
    
    // 重新实现递归构建逻辑
    const processDir = (dir: Directory): any => {
      const dirIfaces = ifaces.filter(i => i.directory === dir.id).map(i => ({ ...i, type: 'interface' }))
      const subDirs = dir.sub_directories ? dir.sub_directories.map(processDir) : []
      return {
        ...dir,
        type: 'directory',
        children: [...subDirs, ...dirIfaces]
      }
    }

    return dirs.map(processDir)
}

// 扁平化目录供选择
const flattenDirs = (tree: any[]): any[] => {
  let res: any[] = []
  tree.forEach(node => {
    if (node.type === 'directory') {
      res.push({ id: node.id, name: node.name })
      if (node.children) {
        res = res.concat(flattenDirs(node.children))
      }
    }
  })
  return res
}

// 事件处理
const handleSelect = (item: any) => {
  activeId.value = item.type === 'interface' ? `i-${item.id}` : `d-${item.id}`
  emit('select', { type: item.type, data: item })
}

// 目录操作
const openDirDialog = (parent?: any, editItem?: any) => {
  if (editItem) {
    dirForm.value = { id: editItem.id, name: editItem.name, parent: undefined }
    // 编辑模式下，使用默认的目录名称
    dirLevel.value = 4 // 默认使用子目录标签
  } else {
    dirForm.value = { id: 0, name: '', parent: parent?.id }
    // 直接使用API返回的level字段来判断目录类型：
    // 1. 根目录下添加：项目（level 1）
    // 2. 项目下添加：模块（level 2）
    // 3. 模块及以下添加：子目录（level 3+）
    if (!parent) {
      // 添加到根目录，是项目
      dirLevel.value = 1
    } else {
      // 根据父目录的level来确定当前要添加的目录类型
      dirLevel.value = parent.level + 1
    }
  }
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
  deleteItemType.value = 'directory'
  deleteItemId.value = item.id
  deleteItemName.value = item.name
  deleteDialog.value = true
}

const handleDeleteInterface = (item: any) => {
  deleteItemType.value = 'interface'
  deleteItemId.value = item.id
  deleteItemName.value = item.name
  deleteDialog.value = true
}

const confirmDelete = async () => {
  if (!deleteItemId.value) return
  
  try {
    if (deleteItemType.value === 'directory') {
      await deleteDirectory(deleteItemId.value)
    } else {
      await deleteInterface(deleteItemId.value)
    }
    loadData()
  } catch (e) {
    console.error(e)
  } finally {
    deleteDialog.value = false
  }
}

// 接口操作
const openInterfaceDialog = (parent: any) => {
  interfaceForm.value = { name: '', method: 'GET', path: '', directory: parent.id, schema_yaml: '' }
  interfaceDialog.value = true
}

const saveInterface = async () => {
  try {
    await createInterface(interfaceForm.value)
    interfaceDialog.value = false
    loadData()
  } catch (e) {
    console.error(e)
  }
}

// 移动接口
const openMoveDialog = (item: any) => {
  moveInterfaceId.value = item.id
  moveTargetId.value = null
  moveDialog.value = true
}

const saveMove = async () => {
  if (!moveTargetId.value) return
  try {
    await updateInterface(moveInterfaceId.value, { directory: moveTargetId.value })
    moveDialog.value = false
    loadData()
  } catch (e) {
    console.error(e)
  }
}

// 暴露刷新方法
defineExpose({ refresh: loadData })

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.font-monospace :deep(textarea) {
  font-family: monospace;
}
</style>

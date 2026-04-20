<template>
  <div class="d-flex flex-column fill-height">
    <!-- 头部 -->
    <div class="px-4 d-flex align-center border-b" style="height: 64px; flex-shrink: 0;">
      <span class="text-h6 font-weight-bold">{{ $t('common.generation') }}</span>
      <v-spacer></v-spacer>
      <v-btn
        icon="mdi-refresh"
        variant="text"
        size="small"
        color="grey"
        @click="loadData"
        :title="$t('common.refresh')"
      ></v-btn>
    </div>

    <!-- 目录筛选 -->
    <div class="px-3 pt-3 pb-1" style="flex-shrink: 0;">
      <v-select
        v-model="selectedDirId"
        :items="dirOptions"
        item-title="name"
        item-value="id"
        :label="$t('interface.fields.directory')"
        density="compact"
        variant="outlined"
        hide-details
        clearable
        class="rounded-lg"
      ></v-select>
    </div>

    <!-- 接口列表 -->
    <div class="flex-grow-1 overflow-y-auto pa-2">
      <v-list density="compact" nav v-if="interfaces.length > 0">
        <v-list-item
          v-for="item in interfaces"
          :key="item.id"
          :active="activeId === item.id"
          color="primary"
          rounded="lg"
          class="mb-1"
          @click="handleSelect(item)"
        >
          <template v-slot:prepend>
            <v-chip
              :color="getMethodColor(item.method)"
              size="x-small"
              label
              class="font-weight-bold mr-2"
              style="min-width: 42px; justify-content: center;"
            >
              {{ item.method }}
            </v-chip>
          </template>
          <v-list-item-title class="text-body-2">{{ item.name }}</v-list-item-title>
          <v-list-item-subtitle class="text-caption text-truncate">{{ item.path }}</v-list-item-subtitle>
        </v-list-item>
      </v-list>
      <v-empty-state
        v-else
        icon="mdi-api"
        :title="$t('common.noData')"
        class="mt-10"
      ></v-empty-state>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { getDirectories } from '@/api/directory'
import { getInterfaces } from '@/api/interface'
import type { Directory } from '@/api/directory'
import type { Interface } from '@/api/interface'

const { t } = useI18n()
const emit = defineEmits(['select'])

const interfaces = ref<Interface[]>([])
const dirOptions = ref<{ id: number; name: string }[]>([])
const selectedDirId = ref<number | null>(null)
const activeId = ref<number | null>(null)

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

const loadDirectories = async () => {
  try {
    const dirs = await getDirectories()
    dirOptions.value = flattenDirs(dirs)
  } catch (e) {
    console.error(e)
  }
}

const loadInterfaces = async () => {
  try {
    const params: any = { no_page: true }
    if (selectedDirId.value) {
      params.directory = selectedDirId.value
    }
    interfaces.value = await getInterfaces(params)
  } catch (e) {
    console.error(e)
  }
}

const loadData = async () => {
  await Promise.all([loadDirectories(), loadInterfaces()])
}

watch(selectedDirId, () => {
  loadInterfaces()
})

const handleSelect = (item: Interface) => {
  activeId.value = item.id
  emit('select', { type: 'interface', data: item })
}

const getMethodColor = (method: string) => {
  const colors: Record<string, string> = { GET: 'blue', POST: 'green', PUT: 'orange', DELETE: 'red', PATCH: 'purple' }
  return colors[method.toUpperCase()] || 'grey'
}

defineExpose({ refresh: loadData })

onMounted(() => {
  loadData()
})
</script>

<template>
  <v-dialog v-model="dialogModel" max-width="640px" persistent>
    <v-card class="rounded-xl">
      <v-card-title class="bg-primary text-white pa-4 d-flex align-center">
        <v-icon icon="mdi-file-import" class="mr-2"></v-icon>
        <span class="text-subtitle-1 font-weight-bold">{{ $t('interface.importDialog.title') }}</span>
      </v-card-title>

      <v-card-text class="pa-6">
        <!-- 目录选择 -->
        <v-select
          v-model="selectedDirectory"
          :items="flatDirectories"
          item-title="name"
          item-value="id"
          :label="$t('interface.importDialog.selectDirectory')"
          variant="outlined"
          density="comfortable"
          class="mb-4"
          prepend-inner-icon="mdi-folder-outline"
          :rules="[v => !!v || $t('interface.importDialog.selectDirectoryRequired')]"
        ></v-select>

        <!-- 文件上传区域 -->
        <v-file-input
          v-model="files"
          accept=".json,.yaml,.yml"
          :label="$t('interface.importDialog.selectFile')"
          prepend-icon="mdi-file-document-outline"
          variant="outlined"
          density="comfortable"
          show-size
          :loading="previewing"
          @update:model-value="handleFileChange"
        >
          <template v-slot:selection="{ fileNames }">
            <v-chip label color="primary" size="small">
              <v-icon icon="mdi-file-code" size="small" class="mr-1"></v-icon>
              {{ fileNames[0] }}
            </v-chip>
          </template>
        </v-file-input>

        <!-- 说明文字 -->
        <v-alert type="info" variant="tonal" density="compact" class="mt-2 mb-0">
          <template v-slot:text>
            {{ $t('interface.importDialog.formatHint') }}
            <br />
            {{ $t('interface.importDialog.updateHint') }}
          </template>
        </v-alert>

        <!-- 预览信息 -->
        <v-expand-transition>
          <div v-if="previewInfo" class="mt-4">
            <v-divider class="mb-3"></v-divider>
            <div class="text-subtitle-2 font-weight-bold mb-2">
              {{ previewInfo.title }}
              <span v-if="previewInfo.version" class="text-caption text-grey ml-1">v{{ previewInfo.version }}</span>
            </div>
            <p v-if="previewInfo.description" class="text-body-2 text-grey-darken-1 mb-3">
              {{ previewInfo.description }}
            </p>
            <div class="d-flex flex-wrap" style="gap: 8px;">
              <v-chip label size="small" color="primary" variant="tonal">
                <v-icon icon="mdi-api" size="small" class="mr-1"></v-icon>
                {{ $t('interface.importDialog.apiCount', { count: previewInfo.totalApis }) }}
              </v-chip>
              <v-chip label size="small" color="secondary" variant="tonal">
                <v-icon icon="mdi-tag-outline" size="small" class="mr-1"></v-icon>
                {{ $t('interface.importDialog.tagCount', { count: previewInfo.tags.length }) }}
              </v-chip>
            </div>
            <div v-if="previewInfo.tags.length > 0" class="mt-2 d-flex flex-wrap" style="gap: 4px;">
              <v-chip
                v-for="tag in previewInfo.tags"
                :key="tag"
                size="x-small"
                variant="outlined"
                color="grey"
              >
                {{ tag }}
              </v-chip>
            </div>
          </div>
        </v-expand-transition>

        <!-- 预览错误 -->
        <v-alert v-if="previewError" type="error" variant="tonal" density="compact" class="mt-4" closable @click:close="previewError = ''">
          {{ previewError }}
        </v-alert>

        <!-- 导入结果 -->
        <v-expand-transition>
          <div v-if="importResult" class="mt-4">
            <v-divider class="mb-3"></v-divider>
            <div class="text-subtitle-2 font-weight-bold mb-2">{{ $t('interface.importDialog.importResult') }}</div>
            <div class="d-flex flex-wrap" style="gap: 8px;">
              <v-chip label size="small" color="success" variant="tonal">
                <v-icon icon="mdi-plus-circle" size="small" class="mr-1"></v-icon>
                {{ $t('interface.importDialog.createdCount', { count: importResult.created }) }}
              </v-chip>
              <v-chip label size="small" color="info" variant="tonal">
                <v-icon icon="mdi-update" size="small" class="mr-1"></v-icon>
                {{ $t('interface.importDialog.updatedCount', { count: importResult.updated }) }}
              </v-chip>
              <v-chip v-if="importResult.failed > 0" label size="small" color="error" variant="tonal">
                <v-icon icon="mdi-alert-circle" size="small" class="mr-1"></v-icon>
                {{ $t('interface.importDialog.failedCount', { count: importResult.failed }) }}
              </v-chip>
            </div>

            <!-- 失败详情 -->
            <v-list v-if="importResult.errors && importResult.errors.length > 0" density="compact" class="mt-2 rounded-lg">
              <v-list-subheader>{{ $t('interface.importDialog.failureDetails') }}</v-list-subheader>
              <v-list-item
                v-for="(err, idx) in importResult.errors"
                :key="idx"
                density="compact"
              >
                <template v-slot:prepend>
                  <v-icon icon="mdi-close-circle" color="error" size="small"></v-icon>
                </template>
                <v-list-item-title class="text-body-2">
                  <code>{{ err.method }} {{ err.path }}</code>
                </v-list-item-title>
                <v-list-item-subtitle class="text-caption">{{ err.error }}</v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </div>
        </v-expand-transition>
      </v-card-text>

      <v-divider></v-divider>
      <v-card-actions class="px-6 pb-4 pt-3">
        <v-spacer></v-spacer>
        <v-btn variant="text" class="text-none" @click="close">
          {{ importResult ? $t('common.close') : $t('common.cancel') }}
        </v-btn>
        <v-btn
          v-if="!importResult"
          color="primary"
          variant="flat"
          class="text-none ml-3"
          :loading="importing"
          :disabled="!canImport"
          prepend-icon="mdi-file-import"
          @click="doImport"
        >
          {{ $t('common.import') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { importOpenAPI, previewOpenAPI } from '@/api/interface'
import { getDirectories } from '@/api/directory'
import type { ImportResult, PreviewInfo } from '@/api/interface'
import type { Directory } from '@/api/directory'

const { t } = useI18n()

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'imported'): void
}>()

const dialogModel = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 状态
const files = ref<File[]>([])
const selectedDirectory = ref<number | null>(null)
const directories = ref<Directory[]>([])
const previewing = ref(false)
const importing = ref(false)
const previewInfo = ref<PreviewInfo | null>(null)
const previewError = ref('')
const importResult = ref<ImportResult | null>(null)

// 将树形目录展开为扁平列表
const flatDirectories = computed(() => {
  const result: Array<{ id: number; name: string }> = []
  const flatten = (dirs: Directory[], prefix = '') => {
    for (const dir of dirs) {
      result.push({
        id: dir.id,
        name: prefix ? `${prefix} / ${dir.name}` : dir.name,
      })
      if (dir.sub_directories && dir.sub_directories.length > 0) {
        flatten(dir.sub_directories, prefix ? `${prefix} / ${dir.name}` : dir.name)
      }
    }
  }
  flatten(directories.value)
  return result
})

const canImport = computed(() => {
  return files.value && files.value.length > 0 && selectedDirectory.value && !importing.value
})

// 加载目录列表
const loadDirectories = async () => {
  try {
    directories.value = await getDirectories()
  } catch (e) {
    console.error('Failed to load directories:', e)
  }
}

// 文件变更时预览
const handleFileChange = async (newFiles: File[] | null) => {
  previewInfo.value = null
  previewError.value = ''
  importResult.value = null

  if (!newFiles || newFiles.length === 0) return

  const file = newFiles[0]
  if (!file) return

  previewing.value = true
  try {
    const info = await previewOpenAPI(file)
    previewInfo.value = info
  } catch (e: any) {
    const msg = e?.response?.data?.error || e?.message || t('interface.importDialog.parseError')
    previewError.value = msg
  } finally {
    previewing.value = false
  }
}

// 执行导入
const doImport = async () => {
  if (!files.value || files.value.length === 0 || !selectedDirectory.value) return

  const file = files.value[0]
  if (!file) return

  importing.value = true
  importResult.value = null
  try {
    const result = await importOpenAPI(file, selectedDirectory.value)
    importResult.value = result
    emit('imported')
  } catch (e: any) {
    const msg = e?.response?.data?.error || e?.message || t('interface.importDialog.importError')
    previewError.value = msg
  } finally {
    importing.value = false
  }
}

// 关闭对话框
const close = () => {
  dialogModel.value = false
}

// 重置状态
const resetState = () => {
  files.value = []
  selectedDirectory.value = null
  previewInfo.value = null
  previewError.value = ''
  importResult.value = null
  previewing.value = false
  importing.value = false
}

// 打开时加载目录并重置状态
watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal) {
      resetState()
      loadDirectories()
    }
  }
)
</script>

<template>
  <div class="pipeline-editor">
    <div class="pipeline-track">
      <!-- Start Trigger -->
      <div class="pl-trigger">
        <div class="pl-trigger__circle">
          <v-icon size="24" color="white">mdi-play</v-icon>
        </div>
        <span class="pl-trigger__label">Start Trigger</span>
      </div>
      <div class="pl-edge"><div class="pl-edge__line" /><div class="pl-edge__arrow" /></div>

      <!-- Draggable Steps -->
      <VueDraggable
        v-model="localSteps"
        class="pl-steps"
        handle=".pl-step__head"
        :animation="250"
        ghost-class="pl-step--ghost"
        @update:modelValue="emitUpdate"
      >
        <div v-for="(step, idx) in localSteps" :key="idx" class="pl-step-group">
          <div
            class="pl-step"
            :class="{ 'pl-step--active': hoveredIdx === idx }"
            @mouseenter="hoveredIdx = idx"
            @mouseleave="hoveredIdx = -1"
            @click="editStep(idx)"
          >
            <div class="pl-step__head">
              <span class="pl-step__num">{{ idx + 1 }}</span>
              <span class="pl-step__name">{{ step.name || t('testing.pipeline.unnamed') }}</span>
              <v-icon size="14" class="pl-step__drag" color="rgba(255,255,255,.5)">mdi-drag-horizontal-variant</v-icon>
            </div>
            <div class="pl-step__body">
              <div class="pl-step__script"><v-icon size="12" class="mr-1" color="grey-lighten-1">mdi-console</v-icon>{{ step.script || '—' }}</div>
              <div class="pl-step__tags">
                <span class="pl-tag pl-tag--time"><v-icon size="10">mdi-timer-outline</v-icon>{{ step.timeout || 120 }}s</span>
                <span class="pl-tag" :class="'pl-tag--' + (step.on_failure || 'stop')"><v-icon size="10">{{ failureIcon(step.on_failure) }}</v-icon>{{ failureLabel(step.on_failure) }}</span>
                <span class="pl-step__del" @click.stop="removeStep(idx)"><v-icon size="14" color="error">mdi-trash-can-outline</v-icon></span>
              </div>
            </div>
          </div>
          <div class="pl-edge"><div class="pl-edge__line" /><div class="pl-edge__arrow" /></div>
        </div>
      </VueDraggable>

      <!-- Add -->
      <div class="pl-node-add-wrap" @click="addStep">
        <div class="pl-node--add">
          <v-icon size="24" color="white">mdi-plus</v-icon>
        </div>
        <span class="pl-node-add__label">{{ t('testing.pipeline.addStep') }}</span>
      </div>

    </div>


    <!-- Edit Dialog -->
    <v-dialog v-model="editDialog" max-width="580" persistent>
      <v-card class="rounded-xl" elevation="16">
        <v-toolbar color="primary" density="compact">
          <v-toolbar-title class="text-subtitle-1 font-weight-bold">{{ isNewStep ? t('testing.pipeline.newStep') : t('testing.steps.edit') }}</v-toolbar-title>
          <v-spacer />
          <v-btn icon="mdi-close" variant="text" @click="cancelEdit" />
        </v-toolbar>
        <v-card-text class="pa-6">
          <v-text-field v-model="editForm.name" :label="t('testing.steps.name')" variant="outlined" density="compact" class="mb-4" :placeholder="t('testing.pipeline.namePlaceholder')" />
          <div class="mb-4">
            <label class="text-caption text-medium-emphasis d-block mb-1">{{ t('testing.steps.script') }}</label>
            <div class="script-editor-wrap">
              <Codemirror
                v-model="editForm.script"
                :style="{ minHeight: '160px', fontSize: '13px' }"
                :extensions="cmShellExtensions"
                :tab-size="4"
                placeholder="echo 'Hello World'"
              />
            </div>
          </div>
          <v-row>
            <v-col cols="6">
              <v-text-field v-model.number="editForm.timeout" :label="t('testing.steps.timeout')" variant="outlined" density="compact" type="number" suffix="s" />
            </v-col>
            <v-col cols="6">
              <v-select v-model="editForm.on_failure" :items="failureOptions" :label="t('testing.steps.onFailure')" variant="outlined" density="compact" />
            </v-col>
          </v-row>
        </v-card-text>
        <v-divider />
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" class="text-none" @click="cancelEdit">{{ t('common.cancel') }}</v-btn>
          <v-btn color="primary" variant="flat" class="text-none px-6" prepend-icon="mdi-check" @click="saveStep">{{ t('testing.pipeline.confirmBtn') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { VueDraggable } from 'vue-draggable-plus'
import { Codemirror } from 'vue-codemirror'
import { StreamLanguage } from '@codemirror/language'
import { shell } from '@codemirror/legacy-modes/mode/shell'

const { t } = useI18n()

const cmShellExtensions = [StreamLanguage.define(shell)]

const props = defineProps<{ modelValue: any[] }>()
const emit = defineEmits<{ (e: 'update:modelValue', v: any[]): void }>()

const localSteps = ref<any[]>([...props.modelValue])
const hoveredIdx = ref(-1)
const editDialog = ref(false)
const editingIdx = ref(-1)
const editForm = ref({ name: '', script: '', timeout: 120, on_failure: 'stop' })
const isNewStep = ref(false)

const failureOptions = computed(() => [
  { title: t('testing.steps.failureOptions.stop'), value: 'stop' },
  { title: t('testing.steps.failureOptions.continue_'), value: 'continue' },
  { title: t('testing.steps.failureOptions.retry'), value: 'retry' },
])

const failureIcon = (v: string) => ({ stop: 'mdi-close-circle-outline', continue: 'mdi-arrow-right-circle-outline', retry: 'mdi-refresh' }[v] || 'mdi-close-circle-outline')
const failureLabel = (v: string) => ({ stop: 'Stop', continue: 'Continue', retry: 'Retry' }[v] || 'Stop')

watch(() => props.modelValue, (v) => { localSteps.value = [...v] }, { deep: true })

const emitUpdate = () => { emit('update:modelValue', [...localSteps.value]) }

const addStep = () => { isNewStep.value = true; editingIdx.value = localSteps.value.length; editForm.value = { name: '', script: '', timeout: 120, on_failure: 'stop' }; editDialog.value = true }
const removeStep = (idx: number) => { localSteps.value.splice(idx, 1); emitUpdate() }
const editStep = (idx: number) => { isNewStep.value = false; editingIdx.value = idx; editForm.value = { ...localSteps.value[idx] }; editDialog.value = true }

const saveStep = () => {
  if (isNewStep.value) { localSteps.value.push({ ...editForm.value }) }
  else if (editingIdx.value >= 0 && editingIdx.value < localSteps.value.length) { localSteps.value[editingIdx.value] = { ...editForm.value } }
  emitUpdate(); editDialog.value = false
}
const cancelEdit = () => { editDialog.value = false }
</script>

<style scoped>
/* ===== Layout ===== */
.pipeline-editor { width: 100%; min-height: 200px; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.pipeline-track { display: flex; align-items: center; padding: 40px 28px; overflow-x: auto; width: 100%; justify-content: center; }

/* ===== Start Trigger ===== */
.pl-trigger {
  position: relative;
  width: 52px; height: 52px; flex-shrink: 0;
}
.pl-trigger__circle {
  width: 52px; height: 52px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: rgb(25, 118, 210);
  box-shadow: 0 3px 10px rgba(25, 118, 210, .3);
}
.pl-trigger__label {
  position: absolute; top: 100%; left: 50%; transform: translateX(-50%);
  margin-top: 6px;
  font-size: 11px; font-weight: 600; color: rgba(0, 0, 0, .5);
  white-space: nowrap;
}

/* ===== Add node ===== */
.pl-node-add-wrap {
  position: relative;
  width: 52px; height: 52px; flex-shrink: 0;
  cursor: pointer;
}
.pl-node--add {
  width: 52px; height: 52px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: rgb(25, 118, 210);
  box-shadow: 0 3px 10px rgba(25, 118, 210, .3);
  transition: all .2s;
}
.pl-node-add-wrap:hover .pl-node--add {
  box-shadow: 0 5px 16px rgba(25, 118, 210, .4);
  transform: scale(1.08);
}
.pl-node-add__label {
  position: absolute; top: 100%; left: 50%; transform: translateX(-50%);
  margin-top: 6px;
  font-size: 11px; font-weight: 600; color: rgba(0, 0, 0, .5);
  white-space: nowrap;
  transition: color .2s;
}
.pl-node-add-wrap:hover .pl-node-add__label {
  color: #1976d2;
}

/* ===== Connector edge ===== */
.pl-edge {
  width: 44px; display: flex; align-items: center; flex-shrink: 0; position: relative;
}
.pl-edge__line {
  position: absolute; left: 0; right: 10px; top: 50%; height: 2px;
  background: linear-gradient(90deg, #bdbdbd, #e0e0e0);
  transform: translateY(-50%);
}
.pl-edge__arrow {
  position: absolute; right: 2px; top: 50%; transform: translateY(-50%);
  width: 0; height: 0;
  border-top: 5px solid transparent; border-bottom: 5px solid transparent; border-left: 7px solid #bdbdbd;
}

/* ===== Steps area ===== */
.pl-steps { display: flex; align-items: center; gap: 0; }
.pl-step-group { display: flex; align-items: center; }

/* ===== Step card ===== */
.pl-step {
  width: 210px; height: 120px;
  background: #fff; border-radius: 14px; overflow: hidden;
  border: 1.5px solid rgba(0,0,0,.06);
  box-shadow: 0 1px 6px rgba(0,0,0,.05);
  cursor: pointer; flex-shrink: 0;
  display: flex; flex-direction: column;
  transition: all .22s cubic-bezier(.4,0,.2,1);
}
.pl-step--active {
  border-color: rgba(25,118,210,.35);
  box-shadow: 0 6px 24px rgba(25,118,210,.12);
  transform: translateY(-3px);
}
.pl-step--ghost { opacity: .35; }

.pl-step__head {
  display: flex; align-items: center; gap: 6px;
  padding: 10px 12px;
  background: linear-gradient(135deg, #1565c0, #42a5f5);
  cursor: grab; min-height: 38px;
}
.pl-step__head:active { cursor: grabbing; }
.pl-step__num {
  width: 22px; height: 22px; border-radius: 6px;
  background: rgba(255,255,255,.22); color: #fff;
  font-size: 11px; font-weight: 800;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.pl-step__name {
  font-size: 13px; font-weight: 600; color: #fff;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;
}
.pl-step__drag { opacity: 0; transition: opacity .2s; }
.pl-step--active .pl-step__drag { opacity: 1; }

.pl-step__body { padding: 10px 12px; flex: 1; display: flex; flex-direction: column; justify-content: space-between; }
.pl-step__script {
  display: flex; align-items: center;
  font-family: 'Fira Code','SF Mono','Courier New',monospace;
  font-size: 11px; color: #78909c;
  background: #f5f7fa; border-radius: 6px; padding: 5px 8px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  margin-bottom: 8px;
}
.pl-step__tags { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.pl-tag {
  display: inline-flex; align-items: center; gap: 3px;
  padding: 2px 7px; border-radius: 4px;
  font-size: 10px; font-weight: 600;
}
.pl-tag--time   { background: rgba(25,118,210,.07); color: #1565c0; }
.pl-tag--stop   { background: rgba(229,57,53,.07);  color: #c62828; }
.pl-tag--continue { background: rgba(30,136,229,.07); color: #1565c0; }
.pl-tag--retry  { background: rgba(245,124,0,.07);  color: #e65100; }
.pl-step__del {
  margin-left: auto; opacity: 0; cursor: pointer; transition: opacity .2s;
  display: flex; align-items: center; padding: 2px;
}
.pl-step--active .pl-step__del { opacity: 1; }

/* ===== Script editor ===== */
.script-editor-wrap {
  border: 1px solid rgba(0, 0, 0, 0.24);
  border-radius: 8px;
  overflow: hidden;
  transition: border-color 0.2s;
}
.script-editor-wrap:focus-within {
  border-color: rgb(var(--v-theme-primary));
  box-shadow: 0 0 0 1px rgb(var(--v-theme-primary));
}
.script-editor-wrap :deep(.cm-editor) {
  font-family: 'Fira Code', 'SF Mono', 'Consolas', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
}
.script-editor-wrap :deep(.cm-editor .cm-scroller) {
  min-height: 160px;
  max-height: 360px;
  overflow: auto;
}
.script-editor-wrap :deep(.cm-editor.cm-focused) {
  outline: none;
}
.script-editor-wrap :deep(.cm-gutters) {
  background: #f8f9fa;
  border-right: 1px solid #e8e8e8;
}

/* ===== Misc ===== */
.pl-empty { padding-bottom: 20px; opacity: .5; }
</style>

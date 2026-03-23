<template>
  <v-container fluid class="fill-height pa-0">
    <v-row no-gutters class="fill-height">
      <!-- 左侧目录树 -->
      <v-col cols="12" md="3" class="d-flex flex-column fill-height">
        <v-card class="flex-grow-1 d-flex flex-column" elevation="0" border="thin" tile>
          <div class="flex-grow-1 overflow-y-auto pa-2">
            <InterfaceTree 
              @select="handleSelect" 
              ref="treeRef"
            />
          </div>
        </v-card>
      </v-col>
      
      <!-- 右侧工作台 -->
      <v-col cols="12" md="9" class="d-flex flex-column fill-height">
        <v-card class="flex-grow-1 d-flex flex-column overflow-hidden" elevation="0" border="thin" tile>
          <InterfaceWorkbench 
            v-if="selectedInterface" 
            :interface-id="selectedInterface.id"
            @refresh-tree="refreshTree"
          />
          <div v-else class="fill-height d-flex flex-column align-center justify-center text-medium-emphasis">
            <v-icon icon="mdi-code-braces" size="64" class="mb-4 opacity-20"></v-icon>
            <div class="text-subtitle-1 font-weight-bold opacity-50">{{ $t('generation.selectInterface') }}</div>
            <div class="text-caption opacity-40 mt-2">{{ $t('generation.selectInterfaceDesc') }}</div>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import InterfaceTree from './components/InterfaceTree.vue'
import InterfaceWorkbench from './components/InterfaceWorkbench.vue'
import type { Interface } from '@/api/interface'

const selectedInterface = ref<Interface | null>(null)
const treeRef = ref<any>(null)

const handleSelect = (item: any) => {
  if (item.type === 'interface') {
    selectedInterface.value = item.data
  } else {
    selectedInterface.value = null
  }
}

const refreshTree = () => {
  treeRef.value?.refresh()
}
</script>

<style scoped>
/* Scoped styles if needed, mostly handled by Vuetify classes now */
</style>

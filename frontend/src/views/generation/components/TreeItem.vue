<template>
  <v-list-group v-if="item.type === 'directory'" :value="`d-${item.id}`">
    <template v-slot:activator="{ props, isOpen }">
      <v-list-item
        v-bind="props"
        :title="item.name"
        :prepend-icon="isOpen ? 'mdi-folder-open' : 'mdi-folder'"
        density="compact"
        @click.stop="$emit('select', item)"
        :active="activeId === `d-${item.id}`"
      >
        <template v-slot:append>
          <v-menu>
            <template v-slot:activator="{ props }">
              <v-btn icon="mdi-dots-vertical" variant="text" size="small" density="comfortable" v-bind="props"></v-btn>
            </template>
            <v-list density="compact">
              <v-list-item @click="$emit('add-dir', item)">
                <v-list-item-title class="text-body-2">{{ $t('generation.addDirectory') }}</v-list-item-title>
              </v-list-item>
              <v-list-item @click="$emit('add-interface', item)">
                <v-list-item-title class="text-body-2">{{ $t('generation.addInterface') }}</v-list-item-title>
              </v-list-item>
              <v-list-item @click="$emit('edit-dir', null, item)">
                <v-list-item-title class="text-body-2">{{ $t('common.edit') }}</v-list-item-title>
              </v-list-item>
              <v-list-item @click="$emit('delete-dir', item)">
                <v-list-item-title class="text-body-2 text-error">{{ $t('common.delete') }}</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
        </template>
      </v-list-item>
    </template>

    <template v-for="child in item.children" :key="child.id">
      <tree-item
        :item="child"
        :active-id="activeId"
        @select="$emit('select', $event)"
        @add-dir="$emit('add-dir', $event)"
        @add-interface="$emit('add-interface', $event)"
        @edit-dir="$emit('edit-dir', $event)"
        @delete-dir="$emit('delete-dir', $event)"
        @delete-interface="$emit('delete-interface', $event)"
        @move-interface="$emit('move-interface', $event)"
      />
    </template>
  </v-list-group>

  <v-list-item
    v-else
    :title="item.name"
    :prepend-icon="getMethodIcon(item.method)"
    density="compact"
    @click="$emit('select', item)"
    :active="activeId === `i-${item.id}`"
    color="primary"
  >
    <template v-slot:append>
      <v-menu>
        <template v-slot:activator="{ props }">
          <v-btn icon="mdi-dots-vertical" variant="text" size="small" density="comfortable" v-bind="props"></v-btn>
        </template>
        <v-list density="compact">
          <v-list-item @click="$emit('move-interface', item)">
            <v-list-item-title class="text-body-2">{{ $t('generation.moveInterface') }}</v-list-item-title>
          </v-list-item>
          <v-list-item @click="$emit('delete-interface', item)">
            <v-list-item-title class="text-body-2 text-error">{{ $t('common.delete') }}</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </template>
  </v-list-item>
</template>

<script setup lang="ts">
defineProps<{
  item: any
  activeId: string
}>()

defineEmits([
  'select', 
  'add-dir', 'add-interface', 'edit-dir', 'delete-dir', 
  'delete-interface', 'move-interface'
])

const getMethodIcon = (method: string) => {
  // 简单映射，实际可用不同颜色的图标
  return 'mdi-api' 
}
</script>

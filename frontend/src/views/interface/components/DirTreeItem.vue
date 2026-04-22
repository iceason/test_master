<template>
  <v-list-group :value="`d-${item.id}`">
    <template v-slot:activator="{ props, isOpen }">
      <v-list-item
        v-bind="props"
        :title="item.name"
        :prepend-icon="isOpen ? 'mdi-folder-open' : 'mdi-folder'"
        density="compact"
        @click.stop="$emit('select', item)"
        :active="activeId === item.id"
        color="primary"
      >
        <template v-slot:append>
          <v-menu>
            <template v-slot:activator="{ props: menuProps }">
              <v-btn icon="mdi-dots-vertical" variant="text" size="small" density="comfortable" v-bind="menuProps" @click.stop></v-btn>
            </template>
            <v-list density="compact">
              <v-list-item @click="$emit('add-dir', item)">
                <v-list-item-title class="text-body-2">{{ $t('generation.addSubDirectory') }}</v-list-item-title>
              </v-list-item>
              <v-list-item @click="$emit('edit-dir', item)">
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

    <template v-for="child in dirChildren" :key="child.id">
      <dir-tree-item
        :item="child"
        :active-id="activeId"
        @select="$emit('select', $event)"
        @add-dir="$emit('add-dir', $event)"
        @edit-dir="$emit('edit-dir', $event)"
        @delete-dir="$emit('delete-dir', $event)"
      />
    </template>
  </v-list-group>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  item: any
  activeId: number | null
}>()

defineEmits(['select', 'add-dir', 'edit-dir', 'delete-dir'])

const dirChildren = computed(() => {
  return (props.item.children || []).filter((c: any) => c.type === 'directory')
})
</script>

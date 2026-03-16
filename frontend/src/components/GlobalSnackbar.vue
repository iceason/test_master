<template>
  <v-snackbar
    v-model="snackbarStore.show"
    :color="snackbarStore.color"
    timeout="3000"
    location="top"
    variant="elevated"
    class="mt-4"
  >
    {{ snackbarStore.message }}
    <template v-slot:actions>
      <v-btn
        color="white"
        variant="text"
        @click="snackbarStore.show = false"
        icon="mdi-close"
        size="small"
      ></v-btn>
    </template>
  </v-snackbar>
</template>

<script setup lang="ts">
import { useSnackbarStore } from '@/store/snackbar'
const snackbarStore = useSnackbarStore()
</script>

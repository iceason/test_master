<template>
  <v-container class="fill-height d-flex align-center justify-center text-center">
    <div>
      <v-icon icon="mdi-emoticon-sad-outline" size="96" class="mb-4" color="primary"></v-icon>
      <h1 class="text-h4 font-weight-bold mb-2">404</h1>
      <p class="text-body-1 text-medium-emphasis mb-6">{{ $t('common.notFound') || 'Page not found' }}</p>
      <v-btn color="primary" variant="flat" to="/" class="text-none" rounded="lg">
        {{ $t('common.backHome') || 'Back Home' }}
      </v-btn>
    </div>
  </v-container>
</template>

<script setup lang="ts">
</script>


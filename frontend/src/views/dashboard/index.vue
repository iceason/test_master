<template>
  <v-container class="fill-height align-start py-8 px-6" style="max-width: 1400px;">
    <!-- 欢迎头 -->
    <v-row class="mb-8">
      <v-col cols="12">
        <div class="d-flex flex-column">
          <h1 class="text-h4 font-weight-bold text-on-surface mb-2">Welcome back, {{ userStore.username || 'Admin' }}</h1>
          <p class="text-body-1 text-medium-emphasis" style="max-width: 800px;">
            {{ $t('intro.subtitle') }}
          </p>
        </div>
      </v-col>
    </v-row>

    <!-- 核心功能卡片 -->
    <v-row class="mb-10">
      <v-col cols="12" md="4">
        <v-card 
          link 
          to="/generation" 
          variant="elevated"
          elevation="1"
          class="fill-height rounded-xl overflow-hidden transition-swing"
          hover
        >
          <div class="pa-6 d-flex flex-column fill-height">
            <div class="d-flex align-start justify-space-between mb-4">
              <v-avatar color="primary-container" size="56" rounded="lg">
                <v-icon icon="mdi-creation" size="32" color="on-primary-container"></v-icon>
              </v-avatar>
              <v-icon icon="mdi-arrow-top-right" color="medium-emphasis"></v-icon>
            </div>
            
            <h3 class="text-h6 font-weight-bold mb-2 text-on-surface">{{ $t('intro.features.aiGeneration.title') }}</h3>
            <p class="text-body-2 text-medium-emphasis mb-6 flex-grow-1">
              {{ $t('intro.features.aiGeneration.desc') }}
            </p>
            
            <v-btn color="primary" variant="flat" elevation="2" block class="text-none" rounded="lg">
              Start Generating
            </v-btn>
          </div>
        </v-card>
      </v-col>

      <v-col cols="12" md="4">
        <v-card 
          link 
          to="/interface" 
          variant="elevated"
          elevation="1"
          class="fill-height rounded-xl overflow-hidden transition-swing"
          hover
        >
          <div class="pa-6 d-flex flex-column fill-height">
            <div class="d-flex align-start justify-space-between mb-4">
              <v-avatar color="secondary-container" size="56" rounded="lg">
                <v-icon icon="mdi-api" size="32" color="on-secondary-container"></v-icon>
              </v-avatar>
              <v-icon icon="mdi-arrow-top-right" color="medium-emphasis"></v-icon>
            </div>
            
            <h3 class="text-h6 font-weight-bold mb-2 text-on-surface">{{ $t('intro.features.apiManagement.title') }}</h3>
            <p class="text-body-2 text-medium-emphasis mb-6 flex-grow-1">
              {{ $t('intro.features.apiManagement.desc') }}
            </p>
            
            <v-btn variant="outlined" color="primary" block class="text-none" rounded="lg">
              Manage APIs
            </v-btn>
          </div>
        </v-card>
      </v-col>

      <v-col cols="12" md="4">
        <v-card 
          link 
          to="/testcase" 
          variant="elevated"
          elevation="1"
          class="fill-height rounded-xl overflow-hidden transition-swing"
          hover
        >
          <div class="pa-6 d-flex flex-column fill-height">
            <div class="d-flex align-start justify-space-between mb-4">
              <v-avatar color="tertiary-container" size="56" rounded="lg">
                <v-icon icon="mdi-export" size="32" color="on-tertiary-container"></v-icon>
              </v-avatar>
              <v-icon icon="mdi-arrow-top-right" color="medium-emphasis"></v-icon>
            </div>
            
            <h3 class="text-h6 font-weight-bold mb-2 text-on-surface">{{ $t('intro.features.export.title') }}</h3>
            <p class="text-body-2 text-medium-emphasis mb-6 flex-grow-1">
              {{ $t('intro.features.export.desc') }}
            </p>
            
            <v-btn variant="outlined" color="primary" block class="text-none" rounded="lg">
              View & Export
            </v-btn>
          </div>
        </v-card>
      </v-col>
    </v-row>

    <!-- 快速入门指南 -->
    <v-row>
      <v-col cols="12">
        <div class="d-flex align-center mb-6">
          <v-icon icon="mdi-school-outline" class="mr-2" color="primary"></v-icon>
          <h2 class="text-h5 font-weight-bold text-on-surface">{{ $t('intro.guide.title') }}</h2>
        </div>
        
        <v-card variant="outlined" class="rounded-xl bg-surface border-opacity-12">
          <v-row no-gutters>
            <v-col cols="12" md="3" class="pa-6 border-e d-flex flex-column position-relative guide-step">
              <div class="text-overline font-weight-bold text-primary mb-2">Step 01</div>
              <div class="text-subtitle-1 font-weight-bold mb-2">{{ $t('intro.guide.step1') }}</div>
              <p class="text-body-2 text-medium-emphasis">{{ $t('intro.guide.step1Desc') }}</p>
            </v-col>
            
            <v-col cols="12" md="3" class="pa-6 border-e d-flex flex-column position-relative guide-step">
              <div class="text-overline font-weight-bold text-primary mb-2">Step 02</div>
              <div class="text-subtitle-1 font-weight-bold mb-2">{{ $t('intro.guide.step2') }}</div>
              <p class="text-body-2 text-medium-emphasis">{{ $t('intro.guide.step2Desc') }}</p>
            </v-col>
            
            <v-col cols="12" md="3" class="pa-6 border-e d-flex flex-column position-relative guide-step">
              <div class="text-overline font-weight-bold text-primary mb-2">Step 03</div>
              <div class="text-subtitle-1 font-weight-bold mb-2">{{ $t('intro.guide.step3') }}</div>
              <p class="text-body-2 text-medium-emphasis">{{ $t('intro.guide.step3Desc') }}</p>
            </v-col>
            
            <v-col cols="12" md="3" class="pa-6 d-flex flex-column guide-step">
              <div class="text-overline font-weight-bold text-success mb-2">Step 04</div>
              <div class="text-subtitle-1 font-weight-bold mb-2">{{ $t('intro.guide.step4') }}</div>
              <p class="text-body-2 text-medium-emphasis">{{ $t('intro.guide.step4Desc') }}</p>
            </v-col>
          </v-row>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { useUserStore } from '@/store/user'

const userStore = useUserStore()
</script>

<style scoped>
.bg-primary-container { background-color: rgba(var(--v-theme-primary), 0.12) !important; }
.text-on-primary-container { color: rgb(var(--v-theme-primary)) !important; }

.bg-secondary-container { background-color: rgba(var(--v-theme-secondary), 0.12) !important; }
.text-on-secondary-container { color: rgb(var(--v-theme-secondary)) !important; }

.bg-tertiary-container { background-color: rgba(var(--v-theme-tertiary, 0, 0, 0), 0.12) !important; }
.text-on-tertiary-container { color: rgb(var(--v-theme-tertiary, 0, 0, 0)) !important; }

.border-e { border-right: 1px solid rgba(0, 0, 0, 0.08) !important; }
.border-opacity-12 { border-color: rgba(0, 0, 0, 0.12) !important; }

.guide-step:hover {
  background-color: rgba(0, 0, 0, 0.02);
  transition: background-color 0.2s ease;
}
</style>

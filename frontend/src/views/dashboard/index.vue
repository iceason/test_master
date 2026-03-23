<template>
  <v-container class="fill-height align-start py-8 px-6" style="max-width: 1400px;">
    <!-- Welcome header -->
    <v-row class="mb-8">
      <v-col cols="12">
        <div class="d-flex flex-column">
          <h1 class="text-h5 font-weight-bold text-on-surface mb-2">
            {{ $t('intro.welcome', { name: userStore.username || 'Admin' }) }}
          </h1>
          <p class="text-body-1 text-medium-emphasis" style="max-width: 900px;">
            {{ $t('intro.subtitle') }}
          </p>
        </div>
      </v-col>
    </v-row>

    <!-- Feature cards -->
    <v-row class="mb-10">
      <v-col v-for="(feat, idx) in features" :key="idx" cols="12" sm="6" lg="4">
        <v-card
          link
          :to="feat.to"
          variant="elevated"
          elevation="1"
          class="fill-height rounded-xl overflow-hidden transition-swing"
          hover
        >
          <div class="pa-5 d-flex flex-column fill-height">
            <div class="d-flex align-start justify-space-between mb-4">
              <v-avatar :color="feat.avatarColor" size="52">
                <v-icon :icon="feat.icon" size="28" :color="feat.iconColor"></v-icon>
              </v-avatar>
              <v-icon icon="mdi-arrow-top-right" color="medium-emphasis" size="18"></v-icon>
            </div>
            <h3 class="text-subtitle-1 font-weight-bold mb-2 text-on-surface">{{ $t(feat.title) }}</h3>
            <p class="text-body-2 text-medium-emphasis flex-grow-1">{{ $t(feat.desc) }}</p>
          </div>
        </v-card>
      </v-col>
    </v-row>

    <!-- Quick start guide -->
    <v-row>
      <v-col cols="12">
        <div class="d-flex align-center mb-5">
          <v-icon icon="mdi-school-outline" class="mr-2" color="primary"></v-icon>
          <h2 class="text-h5 font-weight-bold text-on-surface">{{ $t('intro.guide.title') }}</h2>
        </div>

        <v-card variant="outlined" class="rounded-xl bg-surface border-opacity-12">
          <v-row no-gutters>
            <v-col
              v-for="(step, i) in steps"
              :key="i"
              cols="12"
              :md="stepColSize"
              class="pa-5 d-flex flex-column position-relative guide-step"
              :class="{ 'border-e': i < steps.length - 1 }"
            >
              <div class="text-overline font-weight-bold mb-2" :class="i === steps.length - 1 ? 'text-success' : 'text-primary'">
                Step {{ String(i + 1).padStart(2, '0') }}
              </div>
              <div class="text-subtitle-1 font-weight-bold mb-2">{{ $t(step.title) }}</div>
              <p class="text-body-2 text-medium-emphasis">{{ $t(step.desc) }}</p>
            </v-col>
          </v-row>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()

const features = [
  {
    icon: 'mdi-briefcase-outline',
    avatarColor: 'primary-container',
    iconColor: 'on-primary-container',
    title: 'intro.features.projectManagement.title',
    desc: 'intro.features.projectManagement.desc',
    to: '/projects',
  },
  {
    icon: 'mdi-api',
    avatarColor: 'secondary-container',
    iconColor: 'on-secondary-container',
    title: 'intro.features.apiManagement.title',
    desc: 'intro.features.apiManagement.desc',
    to: '/interface',
  },
  {
    icon: 'mdi-creation',
    avatarColor: 'tertiary-container',
    iconColor: 'on-tertiary-container',
    title: 'intro.features.aiGeneration.title',
    desc: 'intro.features.aiGeneration.desc',
    to: '/generation',
  },
  {
    icon: 'mdi-flask-outline',
    avatarColor: 'primary-container',
    iconColor: 'on-primary-container',
    title: 'intro.features.interfaceTesting.title',
    desc: 'intro.features.interfaceTesting.desc',
    to: '/testcase',
  },
  {
    icon: 'mdi-play-circle-outline',
    avatarColor: 'secondary-container',
    iconColor: 'on-secondary-container',
    title: 'intro.features.continuousBuild.title',
    desc: 'intro.features.continuousBuild.desc',
    to: '/testing/plans',
  },
  {
    icon: 'mdi-export',
    avatarColor: 'tertiary-container',
    iconColor: 'on-tertiary-container',
    title: 'intro.features.export.title',
    desc: 'intro.features.export.desc',
    to: '/testcase',
  },
]

const steps = [
  { title: 'intro.guide.step1', desc: 'intro.guide.step1Desc' },
  { title: 'intro.guide.step2', desc: 'intro.guide.step2Desc' },
  { title: 'intro.guide.step3', desc: 'intro.guide.step3Desc' },
  { title: 'intro.guide.step4', desc: 'intro.guide.step4Desc' },
  { title: 'intro.guide.step5', desc: 'intro.guide.step5Desc' },
]

const stepColSize = computed(() => {
  const len = steps.length
  if (len <= 4) return 12 / len
  return undefined
})
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

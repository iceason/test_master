<template>
  <v-app>
    <!-- MD3 标准导航抽屉 -->
    <v-navigation-drawer
      v-model="drawer"
      app
      width="280"
      color="surface"
      class="border-e"
      floating
    >
      <div class="px-6 py-5 d-flex align-center">
        <v-icon icon="mdi-rocket-launch" color="primary" size="28" class="mr-3"></v-icon>
        <span class="text-subtitle-1 font-weight-bold text-on-surface">Test Master</span>
      </div>

      <div class="px-3">
        <v-list :opened="openedGroups" @update:opened="onOpenedUpdate" density="compact" nav>
          <v-list-subheader class="text-uppercase text-caption font-weight-bold mb-2">Workspace</v-list-subheader>
          
          <v-list-item
            v-for="item in menuItems"
            :key="item.value"
            :value="item.value"
            :to="item.to"
            rounded="xl"
            color="primary"
            class="mb-1"
            :active-class="'bg-primary-container text-on-primary-container'"
          >
            <template v-slot:prepend>
              <v-icon :icon="item.icon" class="mr-2"></v-icon>
            </template>
            <v-list-item-title class="font-weight-medium">{{ $t(item.title) }}</v-list-item-title>
          </v-list-item>

          <!-- Project management group -->
          <v-list-group value="projects">
            <template v-slot:activator="{ props }">
              <v-list-item v-bind="props" rounded="xl" class="mb-1">
                <template v-slot:prepend>
                  <v-icon icon="mdi-briefcase-outline" class="mr-2"></v-icon>
                </template>
                <v-list-item-title class="font-weight-medium">{{ $t('common.projects') }}</v-list-item-title>
              </v-list-item>
            </template>
            <v-list-item
              v-for="sub in projectSubItems"
              :key="sub.value"
              :value="sub.value"
              :to="sub.to"
              rounded="xl"
              color="primary"
              class="mb-1"
              :active-class="'bg-primary-container text-on-primary-container'"
            >
              <template v-slot:prepend>
                <v-icon :icon="sub.icon" class="mr-2"></v-icon>
              </template>
              <v-list-item-title class="font-weight-medium">{{ $t(sub.title) }}</v-list-item-title>
            </v-list-item>
          </v-list-group>

          <!-- Test case management group -->
          <v-list-group value="testcases">
            <template v-slot:activator="{ props }">
              <v-list-item v-bind="props" rounded="xl" class="mb-1">
                <template v-slot:prepend>
                  <v-icon icon="mdi-clipboard-list-outline" class="mr-2"></v-icon>
                </template>
                <v-list-item-title class="font-weight-medium">{{ $t('common.testcases') }}</v-list-item-title>
              </v-list-item>
            </template>
            <v-list-item
              v-for="sub in testcaseSubItems"
              :key="sub.value"
              :value="sub.value"
              :to="sub.to"
              rounded="xl"
              color="primary"
              class="mb-1"
              :active-class="'bg-primary-container text-on-primary-container'"
            >
              <template v-slot:prepend>
                <v-icon :icon="sub.icon" class="mr-2"></v-icon>
              </template>
              <v-list-item-title class="font-weight-medium">{{ $t(sub.title) }}</v-list-item-title>
            </v-list-item>
          </v-list-group>

          <!-- Continuous build group -->
          <v-list-group value="testing">
            <template v-slot:activator="{ props }">
              <v-list-item v-bind="props" rounded="xl" class="mb-1">
                <template v-slot:prepend>
                  <v-icon icon="mdi-play-circle-outline" class="mr-2"></v-icon>
                </template>
                <v-list-item-title class="font-weight-medium">{{ $t('common.continuousBuild') }}</v-list-item-title>
              </v-list-item>
            </template>
            <v-list-item
              v-for="sub in testingSubItems"
              :key="sub.value"
              :value="sub.value"
              :to="sub.to"
              rounded="xl"
              color="primary"
              class="mb-1"
              :active-class="'bg-primary-container text-on-primary-container'"
            >
              <template v-slot:prepend>
                <v-icon :icon="sub.icon" class="mr-2"></v-icon>
              </template>
              <v-list-item-title class="font-weight-medium">{{ $t(sub.title) }}</v-list-item-title>
            </v-list-item>
          </v-list-group>

          <!-- Settings group -->
          <v-list-group value="settings">
            <template v-slot:activator="{ props }">
              <v-list-item v-bind="props" rounded="xl" class="mb-1">
                <template v-slot:prepend>
                  <v-icon icon="mdi-cog-outline" class="mr-2"></v-icon>
                </template>
                <v-list-item-title class="font-weight-medium">{{ $t('common.systemSettings') }}</v-list-item-title>
              </v-list-item>
            </template>
            <v-list-item
              v-for="sub in settingsSubItems"
              :key="sub.value"
              :value="sub.value"
              :to="sub.to"
              rounded="xl"
              color="primary"
              class="mb-1"
              :active-class="'bg-primary-container text-on-primary-container'"
            >
              <template v-slot:prepend>
                <v-icon :icon="sub.icon" class="mr-2"></v-icon>
              </template>
              <v-list-item-title class="font-weight-medium">{{ $t(sub.title) }}</v-list-item-title>
            </v-list-item>
          </v-list-group>
        </v-list>
      </div>

      <template v-slot:append>
        <!-- User profile moved to top bar -->
      </template>
    </v-navigation-drawer>

    <!-- 顶部栏 -->
    <v-app-bar app color="surface" elevation="0" class="border-b">
      <v-app-bar-nav-icon @click="drawer = !drawer" color="on-surface-variant"></v-app-bar-nav-icon>
      
      <v-toolbar-title class="text-subtitle-1 font-weight-bold text-on-surface">
        {{ currentRouteName }}
      </v-toolbar-title>

      <v-spacer></v-spacer>

      <!-- 主题切换按钮 -->
      <v-btn
        icon
        variant="text"
        color="on-surface-variant"
        @click="toggleTheme"
        rounded="lg"
        class="mr-1"
      >
        <v-icon :icon="isDark ? 'mdi-weather-night' : 'mdi-weather-sunny'"></v-icon>
        <v-tooltip activator="parent" location="bottom">
          {{ isDark ? $t('common.theme.switchToLight') : $t('common.theme.switchToDark') }}
        </v-tooltip>
      </v-btn>

      <!-- 语言切换 -->
      <v-btn
        variant="text"
        prepend-icon="mdi-translate"
        color="on-surface-variant"
        class="text-none mr-2"
        rounded="pill"
      >
        {{ $t('common.language.' + locale) }}
        <v-menu activator="parent">
          <v-list density="compact" rounded="xl" elevation="2">
            <v-list-item @click="changeLocale('zh')" :active="locale === 'zh'" color="primary" rounded="xl" class="mx-2 my-1">
              <v-list-item-title>中文</v-list-item-title>
            </v-list-item>
            <v-list-item @click="changeLocale('en')" :active="locale === 'en'" color="primary" rounded="xl" class="mx-2 my-1">
              <v-list-item-title>English</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
      </v-btn>

      <v-menu location="bottom end">
        <template v-slot:activator="{ props }">
          <v-btn
            variant="text"
            class="text-none"
            rounded="pill"
            v-bind="props"
          >
            <v-avatar color="primary" size="32" class="mr-2">
              <img v-if="userAvatar" :src="userAvatar" :alt="userStore.username" @error="handleAvatarError" class="object-cover rounded-full">
              <span v-else class="text-caption font-weight-bold text-on-primary">{{ (userStore.username || 'A').charAt(0).toUpperCase() }}</span>
            </v-avatar>
            <span class="text-subtitle-2 font-weight-medium mr-1">{{ userStore.username || 'Admin' }}</span>
            <v-icon icon="mdi-chevron-down" size="small"></v-icon>
          </v-btn>
        </template>
        <v-list density="compact" rounded="xl" elevation="2" width="200">
          <v-list-item prepend-icon="mdi-account-outline" value="profile" rounded="xl" class="mx-2 my-1" :to="'/profile'">
            <v-list-item-title class="text-body-2">{{ $t('common.profile') }}</v-list-item-title>
          </v-list-item>
          <v-divider class="my-1"></v-divider>
          <v-list-item prepend-icon="mdi-logout" value="logout" rounded="xl" class="mx-2 my-1 text-error" @click="handleLogout">
            <v-list-item-title class="text-body-2">{{ $t('common.logout') }}</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </v-app-bar>

    <!-- Logout Confirmation Dialog -->
    <v-dialog v-model="logoutDialog" max-width="400">
      <v-card class="rounded-xl">
        <v-card-title class="bg-primary text-white pa-4">
          <span class="text-subtitle-1 font-weight-bold">{{ $t('common.logout') }}</span>
        </v-card-title>
        <v-card-text class="pa-4 text-body-2">
          {{ $t('login.logoutConfirm') || 'Are you sure you want to logout?' }}
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn color="grey-darken-1" variant="text" @click="logoutDialog = false">
            {{ $t('common.cancel') }}
          </v-btn>
          <v-btn color="error" variant="flat" class="ml-2" @click="confirmLogout">
            {{ $t('common.logout') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 主内容 -->
    <v-main class="bg-background">
      <v-container fluid class="fill-height pa-4 align-start">
        <router-view v-slot="{ Component }">
          <v-fade-transition mode="out-in">
            <component :is="Component" />
          </v-fade-transition>
        </router-view>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@/store/user'
import { useI18n } from 'vue-i18n'
import { useTheme } from '@/composables/useTheme'

const drawer = ref(true)
const logoutDialog = ref(false)
const userAvatar = ref<string>('')
const userStore = useUserStore()
const { t, locale } = useI18n()
const route = useRoute()
const { isDark, toggleTheme } = useTheme()

const pathGroupRules: [string, string][] = [
  ['/projects', 'projects'],
  ['/settings/environments', 'projects'],
  ['/generation', 'testcases'],
  ['/testcase', 'testcases'],
  ['/testing/executions', 'testcases'],
  ['/testing/agents', 'testing'],
  ['/testing/plans', 'testing'],
  ['/settings/email-templates', 'settings'],
]

function getActiveGroup(path: string): string | undefined {
  return pathGroupRules.find(([prefix]) => path.startsWith(prefix))?.[1]
}

const openedGroups = ref<string[]>([])

watch(() => route.path, (path) => {
  const group = getActiveGroup(path)
  if (group && !openedGroups.value.includes(group)) {
    openedGroups.value = [...openedGroups.value, group]
  }
}, { immediate: true })

function onOpenedUpdate(val: string[]) {
  const activeGroup = getActiveGroup(route.path)
  if (activeGroup && !val.includes(activeGroup)) {
    openedGroups.value = [...val, activeGroup]
    return
  }
  openedGroups.value = val
}

const menuItems = [
  { title: 'common.introduction', icon: 'mdi-view-dashboard-outline', value: 'dashboard', to: '/dashboard' },
  { title: 'common.interfaces', icon: 'mdi-api', value: 'interfaces', to: '/interface' },
]

const projectSubItems = [
  { title: 'common.projectAndPermission', icon: 'mdi-shield-account-outline', value: 'sub-projects', to: '/projects' },
  { title: 'common.environments', icon: 'mdi-earth', value: 'sub-environments', to: '/settings/environments' },
]

const testcaseSubItems = [
  { title: 'common.generation', icon: 'mdi-creation', value: 'sub-generation', to: '/generation' },
  { title: 'common.interfaceTesting', icon: 'mdi-clipboard-list-outline', value: 'sub-testcases', to: '/testcase' },
  { title: 'common.executionRecords', icon: 'mdi-history', value: 'sub-executions', to: '/testing/executions' },
]

const testingSubItems = [
  { title: 'common.executorAgents', icon: 'mdi-server-network', value: 'sub-agents', to: '/testing/agents' },
  { title: 'common.buildPlans', icon: 'mdi-clipboard-flow-outline', value: 'sub-buildPlans', to: '/testing/plans' },
]

const settingsSubItems = [
  { title: 'common.emailTemplates', icon: 'mdi-email-newsletter', value: 'sub-emailTemplates', to: '/settings/email-templates' },
]

const routeNameToI18nKey: Record<string, string> = {
  Dashboard: 'common.dashboard',
  Projects: 'common.projectAndPermission',
  Interfaces: 'common.interfaces',
  Generation: 'common.generation',
  TestCases: 'common.interfaceTesting',
  ExecutorAgents: 'common.executorAgents',
  BuildPlans: 'common.buildPlans',
  BuildPlanDetail: 'common.buildPlans',
  ExecutionRecords: 'common.executionRecords',
  Execution: 'execution.title',
  Profile: 'common.profile',
  EmailTemplates: 'common.emailTemplates',
  Environments: 'common.environments',
}

const currentRouteName = computed(() => {
  const name = route.name?.toString() || 'Dashboard'
  const key = routeNameToI18nKey[name]
  return key ? t(key) : name
})

const handleLogout = () => {
  logoutDialog.value = true
}

const confirmLogout = () => {
  logoutDialog.value = false
  userStore.logout()
}

const changeLocale = (lang: string) => {
  locale.value = lang
  localStorage.setItem('locale', lang)
}

// 加载用户头像
const loadUserAvatar = () => {
  const savedAvatar = localStorage.getItem('userAvatar')
  if (savedAvatar) {
    userAvatar.value = savedAvatar
  }
}

// 处理头像加载错误
const handleAvatarError = (event: Event) => {
  const target = event.target as HTMLImageElement
  target.src = ''
  userAvatar.value = ''
}

// 处理头像更新事件
const handleAvatarUpdated = (event: Event) => {
  const customEvent = event as CustomEvent<{ avatarUrl: string }>
  if (customEvent.detail && customEvent.detail.avatarUrl) {
    userAvatar.value = customEvent.detail.avatarUrl
  }
}

// 组件挂载时
onMounted(() => {
  loadUserAvatar()
  window.addEventListener('avatarUpdated', handleAvatarUpdated as EventListener)
})

// 组件卸载时
onUnmounted(() => {
  window.removeEventListener('avatarUpdated', handleAvatarUpdated as EventListener)
})
</script>

<style scoped>
.bg-primary-container {
  background-color: rgba(var(--v-theme-primary), 0.12) !important;
}
.text-on-primary-container {
  color: rgb(var(--v-theme-primary)) !important;
}
</style>

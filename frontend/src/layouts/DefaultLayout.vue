<template>
  <v-app>
    <v-navigation-drawer
      v-model="drawer"
      app
      width="220"
      color="surface"
      class="border-e"
      floating
    >
      <div class="px-5 py-5 d-flex align-center">
        <v-icon icon="mdi-rocket-launch" color="primary" size="28" class="mr-3"></v-icon>
        <span class="text-subtitle-1 font-weight-bold text-on-surface">Test Master</span>
      </div>

      <div class="px-3">
        <v-list density="compact" nav>
          <v-list-subheader class="text-uppercase text-caption font-weight-bold mb-2">Workspace</v-list-subheader>

          <v-list-item
            v-for="item in menuItems"
            :key="item.to"
            :active="isItemActive(item)"
            rounded="xl"
            color="primary"
            class="mb-1 nav-item"
            :class="{ 'bg-primary-container text-on-primary-container': isItemActive(item) }"
            @click="navigateTo(item)"
          >
            <template v-slot:prepend>
              <v-icon :icon="item.icon" class="mr-2" size="20"></v-icon>
            </template>
            <v-list-item-title class="text-body-2 font-weight-medium">{{ $t(item.title) }}</v-list-item-title>
          </v-list-item>
        </v-list>
      </div>

      <template v-slot:append>
        <!-- User profile moved to top bar -->
      </template>
    </v-navigation-drawer>

    <v-app-bar app color="surface" elevation="0" class="border-b">
      <v-app-bar-nav-icon @click="drawer = !drawer" color="on-surface-variant"></v-app-bar-nav-icon>

      <v-toolbar-title v-if="!currentSubTabs.length" class="text-subtitle-1 font-weight-bold text-on-surface">
        {{ currentRouteName }}
      </v-toolbar-title>

      <v-tabs
        v-if="currentSubTabs.length"
        :model-value="activeTabRoute"
        density="compact"
        color="primary"
        class="sub-tabs ml-1"
      >
        <v-tab
          v-for="tab in currentSubTabs"
          :key="tab.to"
          :value="tab.to"
          :to="tab.to"
          class="text-none"
          size="small"
        >
          {{ $t(tab.title) }}
        </v-tab>
      </v-tabs>

      <v-spacer></v-spacer>

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
            <span class="text-subtitle-2 font-weight-medium mr-1">{{ userStore.username || 'admin' }}</span>
            <v-icon icon="mdi-chevron-down" size="small"></v-icon>
          </v-btn>
        </template>
        <v-list density="compact" rounded="xl" elevation="2" width="220">
          <v-list-item
            v-if="canInviteRegister"
            value="invite-register"
            rounded="xl"
            class="mx-2 my-1"
            @click="openInviteRegister"
          >
            <template v-slot:prepend>
              <v-icon icon="mdi-account-outline" size="18" color="primary"></v-icon>
            </template>
            <v-list-item-title class="text-body-2">{{ $t('register.inviteMenu') }}</v-list-item-title>
          </v-list-item>
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

    <v-dialog v-model="inviteDialog" max-width="560" persistent>
      <v-card class="rounded-xl">
        <v-toolbar color="primary" density="compact">
          <v-toolbar-title class="text-subtitle-1 font-weight-bold text-white">{{ $t('register.inviteDialogTitle') }}</v-toolbar-title>
          <v-spacer />
          <v-btn icon="mdi-close" variant="text" color="white" size="small" @click="inviteDialog = false" />
        </v-toolbar>
        <v-card-text class="pa-4">
          <p class="text-body-2 text-medium-emphasis mb-3">{{ $t('register.inviteDialogHint') }}</p>
          <v-text-field
            v-model="inviteUrl"
            variant="outlined"
            density="compact"
            readonly
            hide-details
            class="rounded-lg"
            :label="$t('register.inviteLink')"
          ></v-text-field>
          <p v-if="inviteExpiresText" class="text-caption text-medium-emphasis mt-2">{{ inviteExpiresText }}</p>
        </v-card-text>
        <v-card-actions class="px-4 pb-4">
          <v-spacer />
          <v-btn variant="text" class="text-none" @click="inviteDialog = false">{{ $t('common.close') }}</v-btn>
          <v-btn color="primary" variant="flat" class="text-none ml-2" prepend-icon="mdi-content-copy" @click="copyInviteUrl">
            {{ $t('register.copyLink') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { useSnackbarStore } from '@/store/snackbar'
import { useI18n } from 'vue-i18n'
import { useTheme } from '@/composables/useTheme'
import { getToken } from '@/utils/axios'
import { createRegistrationInvite } from '@/api/registration'

interface SubTab {
  title: string
  to: string
}

interface MenuItem {
  title: string
  icon: string
  to: string
  paths?: string[]
  children?: SubTab[]
}

const drawer = ref(true)
const logoutDialog = ref(false)
const inviteDialog = ref(false)
const inviteUrl = ref('')
const inviteExpiresAt = ref('')
const inviteExpiresText = computed(() => {
  if (!inviteExpiresAt.value) return ''
  try {
    const d = new Date(inviteExpiresAt.value)
    return t('register.inviteExpiresAt', { time: d.toLocaleString(locale.value === 'zh' ? 'zh-CN' : 'en-US') })
  } catch {
    return ''
  }
})
const userAvatar = ref<string>('')
const userStore = useUserStore()
const snackbar = useSnackbarStore()
const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()
const { isDark, toggleTheme } = useTheme()
const canInviteRegister = computed(() => {
  const normalizedUsername = (userStore.username || '').trim().toLowerCase()
  return userStore.isSuperuser || userStore.roles.includes('admin') || normalizedUsername === 'admin'
})

const menuItems: MenuItem[] = [
  { title: 'common.introduction', icon: 'mdi-view-dashboard-outline', to: '/dashboard' },
  {
    title: 'common.projects', icon: 'mdi-briefcase-outline', to: '/projects',
    paths: ['/projects', '/settings/environments'],
    children: [
      { title: 'common.projectAndPermission', to: '/projects' },
      { title: 'common.environments', to: '/settings/environments' },
    ]
  },
  {
    title: 'common.interfaceTesting', icon: 'mdi-clipboard-list-outline', to: '/interface',
    paths: ['/interface', '/generation', '/testcase', '/testing/executions'],
    children: [
      { title: 'common.interfaces', to: '/interface' },
      { title: 'common.generation', to: '/generation' },
      { title: 'common.testing', to: '/testcase' },
      { title: 'common.executionRecords', to: '/testing/executions' },
    ]
  },
  {
    title: 'common.continuousBuild', icon: 'mdi-play-circle-outline', to: '/testing/plans',
    paths: ['/testing/agents', '/testing/plans'],
    children: [
      { title: 'common.buildPlans', to: '/testing/plans' },
      { title: 'common.executorAgents', to: '/testing/agents' },
    ]
  },
  {
    title: 'common.systemSettings', icon: 'mdi-cog-outline', to: '/settings/email-templates',
    paths: ['/settings/email-templates', '/settings/dingtalk-groups', '/settings/dingtalk-templates'],
    children: [
      { title: 'common.emailTemplates', to: '/settings/email-templates' },
      { title: 'common.dingtalkGroups', to: '/settings/dingtalk-groups' },
      { title: 'common.dingtalkTemplates', to: '/settings/dingtalk-templates' },
    ]
  },
]

function isItemActive(item: MenuItem): boolean {
  const path = route.path
  if (item.paths) {
    return item.paths.some(p => path.startsWith(p))
  }
  return path.startsWith(item.to)
}

function navigateTo(item: MenuItem) {
  router.push(item.to)
}

const currentSection = computed(() => {
  return menuItems.find(item => isItemActive(item))
})

const currentSubTabs = computed<SubTab[]>(() => {
  return currentSection.value?.children || []
})

const currentSectionTitle = computed(() => {
  const section = currentSection.value
  return section ? t(section.title) : ''
})

const activeTabRoute = computed(() => {
  const path = route.path
  const tabs = currentSubTabs.value
  const match = tabs.find(tab => path.startsWith(tab.to))
  return match?.to || ''
})

const routeNameToI18nKey: Record<string, string> = {
  Dashboard: 'common.dashboard',
  Projects: 'common.projectAndPermission',
  Interfaces: 'common.interfaces',
  Generation: 'common.generation',
  TestCases: 'common.testing',
  ExecutorAgents: 'common.executorAgents',
  BuildPlans: 'common.buildPlans',
  BuildPlanDetail: 'common.buildPlans',
  ExecutionRecords: 'common.executionRecords',
  Execution: 'execution.title',
  Profile: 'common.profile',
  EmailTemplates: 'common.emailTemplates',
  Environments: 'common.environments',
  DingTalkGroups: 'common.dingtalkGroups',
  DingTalkTemplates: 'common.dingtalkTemplates',
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

const loadUserAvatar = () => {
  const savedAvatar = localStorage.getItem('userAvatar')
  if (savedAvatar) {
    userAvatar.value = savedAvatar
  }
}

const handleAvatarError = (event: Event) => {
  const target = event.target as HTMLImageElement
  target.src = ''
  userAvatar.value = ''
}

const handleAvatarUpdated = (event: Event) => {
  const customEvent = event as CustomEvent<{ avatarUrl: string }>
  if (customEvent.detail && customEvent.detail.avatarUrl) {
    userAvatar.value = customEvent.detail.avatarUrl
  }
}

const openInviteRegister = async () => {
  inviteDialog.value = true
  inviteUrl.value = ''
  inviteExpiresAt.value = ''
  try {
    const data = await createRegistrationInvite()
    inviteUrl.value = data.invite_url
    inviteExpiresAt.value = data.expires_at
  } catch (e: any) {
    const message = e?.response?.data?.message || e?.response?.data?.detail || e?.message || t('common.error')
    snackbar.notify(message, 'error')
    inviteDialog.value = false
  }
}

const copyInviteUrl = async () => {
  if (!inviteUrl.value) return
  try {
    await navigator.clipboard.writeText(inviteUrl.value)
    snackbar.notify(t('register.linkCopied'), 'success')
  } catch {
    snackbar.notify(t('register.copyFailed'), 'warning')
  }
}

onMounted(async () => {
  loadUserAvatar()
  window.addEventListener('avatarUpdated', handleAvatarUpdated as EventListener)
  if (getToken()) {
    try {
      await userStore.getInfo()
    } catch {
      /* ignore */
    }
  }
})

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
.nav-item {
  min-height: 40px;
}
.sub-tabs :deep(.v-tab) {
  min-width: auto;
  padding: 0 12px;
  letter-spacing: normal;
}
</style>

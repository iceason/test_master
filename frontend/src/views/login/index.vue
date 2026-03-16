<template>
  <v-container fluid class="fill-height justify-center align-center bg-grey-lighten-4 pa-0 position-relative">
    <!-- 背景装饰 -->
    <div class="bg-pattern position-absolute top-0 left-0 w-100 h-100"></div>

    <!-- 语言切换 (右上角) -->
    <div class="position-absolute top-0 right-0 ma-6 z-10">
      <v-menu location="bottom end">
        <template v-slot:activator="{ props }">
          <v-btn
            v-bind="props"
            variant="text"
            color="grey-darken-2"
            prepend-icon="mdi-translate"
            rounded="pill"
          >
            {{ $t('common.language.' + locale) }}
          </v-btn>
        </template>
        <v-list density="compact" rounded="xl" elevation="2">
          <v-list-item @click="changeLocale('zh')" :active="locale === 'zh'" color="primary" rounded="xl" class="mx-2 my-1">
            <v-list-item-title>中文</v-list-item-title>
          </v-list-item>
          <v-list-item @click="changeLocale('en')" :active="locale === 'en'" color="primary" rounded="xl" class="mx-2 my-1">
            <v-list-item-title>English</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </div>

    <!-- 登录卡片 -->
    <v-card width="100%" max-width="450" elevation="4" class="rounded-xl pa-8 z-10">
      <div class="text-center mb-8">
        <v-avatar color="primary" size="64" class="mb-4 elevation-2">
          <v-icon icon="mdi-rocket-launch" size="32" color="white"></v-icon>
        </v-avatar>
        <h1 class="text-h4 font-weight-bold text-grey-darken-3 mb-2">Test Master</h1>
        <p class="text-body-1 text-grey text-medium-emphasis">
          {{ $t('intro.subtitle') }}
        </p>
      </div>

      <v-form @submit.prevent="handleLogin" ref="formRef">
        <div class="mb-4">
          <div class="text-caption font-weight-bold text-grey-darken-2 mb-1 ml-1">{{ $t('login.username') }}</div>
          <v-text-field
            v-model="username"
            variant="outlined"
            density="compact"
            prepend-inner-icon="mdi-account-outline"
            :placeholder="$t('login.usernamePlaceholder')"
            color="primary"
            bg-color="surface"
            :rules="[v => !!v || $t('login.usernameRequired')]"
          ></v-text-field>
        </div>

        <div class="mb-6">
          <div class="text-caption font-weight-bold text-grey-darken-2 mb-1 ml-1">{{ $t('login.password') }}</div>
          <v-text-field
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            variant="outlined"
            density="compact"
            prepend-inner-icon="mdi-lock-outline"
            :append-inner-icon="showPassword ? 'mdi-eye-off-outline' : 'mdi-eye-outline'"
            @click:append-inner="showPassword = !showPassword"
            :placeholder="$t('login.passwordPlaceholder')"
            color="primary"
            bg-color="surface"
            :rules="[v => !!v || $t('login.passwordRequired')]"
          ></v-text-field>
        </div>

        <v-btn
          block
          color="primary"
          size="large"
          type="submit"
          :loading="loading"
          class="text-none font-weight-bold mb-6"
          rounded="lg"
          elevation="2"
        >
          {{ $t('login.loginButton') }}
        </v-btn>
        
        <div class="d-flex justify-center gap-6 mb-6 opacity-60">
           <v-tooltip location="bottom" text="AI Generation">
             <template v-slot:activator="{ props }">
               <v-icon v-bind="props" icon="mdi-creation" color="grey-darken-1"></v-icon>
             </template>
           </v-tooltip>
           <v-tooltip location="bottom" text="API Management">
             <template v-slot:activator="{ props }">
               <v-icon v-bind="props" icon="mdi-api" color="grey-darken-1"></v-icon>
             </template>
           </v-tooltip>
           <v-tooltip location="bottom" text="Secure Testing">
             <template v-slot:activator="{ props }">
               <v-icon v-bind="props" icon="mdi-shield-check" color="grey-darken-1"></v-icon>
             </template>
           </v-tooltip>
        </div>

        <div class="text-center">
          <span class="text-body-2 text-grey">{{ $t('login.noAccount') }} </span>
          <a href="#" class="text-body-2 font-weight-bold text-primary text-decoration-none">{{ $t('login.contactAdmin') }}</a>
        </div>
      </v-form>
    </v-card>

    <div class="position-absolute bottom-0 w-100 text-center py-4 text-caption text-grey-darken-1">
      {{ $t('login.copyright') }}
    </div>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { useSnackbarStore } from '@/store/snackbar'
import { useI18n } from 'vue-i18n'

const router = useRouter()
const userStore = useUserStore()
const snackbar = useSnackbarStore()
const { t, locale } = useI18n()

const username = ref('')
const password = ref('')
const loading = ref(false)
const showPassword = ref(false)
const formRef = ref<any>(null)

const handleLogin = async () => {
  const { valid } = await formRef.value.validate()
  if (!valid) return

  loading.value = true
  try {
    await userStore.login({
      username: username.value,
      password: password.value
    })
    snackbar.notify(t('login.loginSuccess'), 'success')
    router.push('/')
  } catch (error) {
    console.error(error)
    snackbar.notify(t('login.loginFailed'), 'error')
  } finally {
    loading.value = false
  }
}

const changeLocale = (lang: string) => {
  locale.value = lang
  localStorage.setItem('locale', lang)
}
</script>

<style scoped>
.bg-pattern {
  background-color: #f5f5f5;
  background-image: radial-gradient(#e0e0e0 1px, transparent 1px);
  background-size: 20px 20px;
}

.z-10 {
  z-index: 10;
}

.gap-6 {
  gap: 24px;
}
</style>

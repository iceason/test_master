<template>
  <v-container fluid class="fill-height justify-center align-center bg-grey-lighten-4 pa-0 position-relative">
    <div class="bg-pattern position-absolute top-0 left-0 w-100 h-100"></div>

    <div v-if="checking" class="d-flex justify-center align-center z-10" style="min-height: 200px;">
      <v-progress-circular indeterminate color="primary" size="48"></v-progress-circular>
    </div>

    <v-card v-else width="100%" max-width="450" elevation="4" class="rounded-xl pa-8 z-10">
      <div class="text-center mb-6">
        <v-avatar color="primary" size="64" class="mb-4 elevation-2">
          <v-icon icon="mdi-account-plus-outline" size="32" color="white"></v-icon>
        </v-avatar>
        <h1 class="text-h5 font-weight-bold text-grey-darken-3">{{ $t('register.title') }}</h1>
      </div>

      <v-alert v-if="invalidReason" type="error" variant="tonal" density="compact" class="mb-4 rounded-lg">
        {{ reasonMessage }}
      </v-alert>

      <v-form v-else @submit.prevent="handleSubmit" ref="formRef">
        <div class="mb-3">
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
            autocomplete="username"
          ></v-text-field>
        </div>

        <div class="mb-3">
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
            autocomplete="new-password"
          ></v-text-field>
        </div>

        <div class="mb-6">
          <div class="text-caption font-weight-bold text-grey-darken-2 mb-1 ml-1">{{ $t('register.confirmPassword') }}</div>
          <v-text-field
            v-model="confirmPassword"
            :type="showPassword2 ? 'text' : 'password'"
            variant="outlined"
            density="compact"
            prepend-inner-icon="mdi-lock-check-outline"
            :append-inner-icon="showPassword2 ? 'mdi-eye-off-outline' : 'mdi-eye-outline'"
            @click:append-inner="showPassword2 = !showPassword2"
            color="primary"
            bg-color="surface"
            :rules="[v => v === password || $t('register.passwordMismatch')]"
            autocomplete="new-password"
          ></v-text-field>
        </div>

        <v-btn block color="primary" size="large" type="submit" :loading="loading" class="text-none font-weight-bold">
          {{ $t('register.submit') }}
        </v-btn>
      </v-form>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { validateRegistrationInvite, registerWithInvite } from '@/api/registration'
import { setRefreshToken } from '@/utils/axios'
import { useUserStore } from '@/store/user'
import { useSnackbarStore } from '@/store/snackbar'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const userStore = useUserStore()
const snackbar = useSnackbarStore()

const token = ref('')
const checking = ref(true)
const invalidReason = ref<string | null>(null)
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const showPassword2 = ref(false)
const loading = ref(false)
const formRef = ref<any>(null)

const reasonMessage = computed(() => {
  const r = invalidReason.value
  if (!r) return ''
  const map: Record<string, string> = {
    missing_token: t('register.reasonMissingToken'),
    not_found: t('register.reasonNotFound'),
    used: t('register.reasonUsed'),
    expired: t('register.reasonExpired'),
  }
  return map[r] || t('register.reasonInvalid')
})

onMounted(async () => {
  token.value = (route.query.token as string) || ''
  if (!token.value) {
    invalidReason.value = 'missing_token'
    checking.value = false
    return
  }
  try {
    const res = await validateRegistrationInvite(token.value)
    if (!res.valid) {
      invalidReason.value = res.reason || 'not_found'
    }
  } catch {
    invalidReason.value = 'not_found'
  } finally {
    checking.value = false
  }
})

const handleSubmit = async () => {
  const { valid } = await formRef.value.validate()
  if (!valid) return
  if (password.value !== confirmPassword.value) {
    snackbar.notify(t('register.passwordMismatch'), 'error')
    return
  }
  loading.value = true
  try {
    const data = await registerWithInvite({
      token: token.value,
      username: username.value,
      password: password.value,
      confirm_password: confirmPassword.value,
    })
    userStore.setToken(data.access)
    if (data.refresh) {
      setRefreshToken(data.refresh)
    }
    await userStore.getInfo()
    snackbar.notify(t('register.success'), 'success')
    router.replace('/dashboard')
  } catch (e: any) {
    const msg = e?.response?.data?.message || e?.response?.data?.detail || e?.message || t('common.error')
    snackbar.notify(msg, 'error')
  } finally {
    loading.value = false
  }
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
</style>

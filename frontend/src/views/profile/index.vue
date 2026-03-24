<template>
  <v-container class="py-8" style="max-width: 720px;">
    <!-- 个人信息卡片 -->
    <v-card elevation="1" class="mb-6">
      <div class="profile-banner"></div>
      <div class="d-flex flex-column align-center" style="margin-top: -48px; position: relative; z-index: 1;">
        <div class="position-relative">
          <v-avatar size="96" class="profile-avatar">
            <img v-if="avatarUrl" :src="avatarUrl" :alt="user.name" @error="handleImageError" style="object-fit: cover; width: 100%; height: 100%;">
            <v-icon v-else icon="mdi-account" size="48" color="primary"></v-icon>
          </v-avatar>
          <input type="file" accept="image/*" class="d-none" ref="fileInput" @change="handleAvatarUpload">
          <v-btn
            icon="mdi-camera"
            size="x-small"
            color="primary"
            class="profile-camera-btn"
            @click="($refs.fileInput as HTMLInputElement).click()"
            :loading="uploadingAvatar"
          ></v-btn>
        </div>
        <h2 class="text-h6 font-weight-bold mt-3">{{ user.name }}</h2>
        <p class="text-body-2 text-medium-emphasis mb-1">{{ user.email }}</p>
        <p class="text-caption text-medium-emphasis mb-4">{{ $t('profile.avatarTip') }}</p>
      </div>
    </v-card>

    <!-- 修改密码卡片 -->
    <v-card elevation="1">
      <v-card-item>
        <template v-slot:prepend>
          <v-avatar color="primary" variant="tonal" size="36" rounded="lg">
            <v-icon icon="mdi-lock-outline" size="20"></v-icon>
          </v-avatar>
        </template>
        <v-card-title class="text-subtitle-1 font-weight-bold">{{ $t('profile.changePassword') }}</v-card-title>
      </v-card-item>

      <v-divider />

      <v-card-text class="pa-6">
        <v-form ref="passwordFormRef" v-model="passwordValid">
          <v-text-field
            v-model="passwordForm.oldPassword"
            :label="$t('profile.fields.oldPassword')"
            type="password"
            :rules="[v => !!v || $t('common.required')]"
            variant="outlined"
            density="compact"
            class="mb-4"
            required
          ></v-text-field>
          <v-text-field
            v-model="passwordForm.newPassword"
            :label="$t('profile.fields.newPassword')"
            type="password"
            :rules="[v => !!v || $t('common.required'), v => v.length >= 6 || $t('profile.passwordTooShort')]"
            variant="outlined"
            density="compact"
            class="mb-4"
            required
          ></v-text-field>
          <v-text-field
            v-model="passwordForm.confirmPassword"
            :label="$t('profile.fields.confirmPassword')"
            type="password"
            :rules="[v => !!v || $t('common.required'), v => v === passwordForm.newPassword || $t('profile.passwordsNotMatch')]"
            variant="outlined"
            density="compact"
            class="mb-2"
            required
          ></v-text-field>
        </v-form>
      </v-card-text>

      <v-divider />

      <v-card-actions class="pa-4">
        <v-spacer />
        <v-btn
          color="primary"
          variant="flat"
          class="text-none px-6"
          @click="changePassword"
          :disabled="!passwordValid || changingPassword"
          :loading="changingPassword"
        >
          {{ $t('profile.updatePassword') }}
        </v-btn>
      </v-card-actions>
    </v-card>

    <!-- 安全提示 -->
    <v-alert variant="tonal" color="info" density="compact" class="mt-6 text-caption">
      <div class="d-flex align-center ga-1">
        <v-icon size="14">mdi-shield-check-outline</v-icon>
        <span>{{ $t('profile.securityTip1') }}</span>
      </div>
    </v-alert>

    <v-snackbar v-model="snackbar" :color="snackbarColor" location="top right">
      {{ snackbarText }}
      <template v-slot:actions>
        <v-btn variant="text" @click="snackbar = false">{{ $t('common.close') }}</v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { getUserProfile } from '@/api/user'
import type { User } from '@/api/user'

const { t } = useI18n()

const user = ref<User>({
  id: 0,
  name: '',
  email: ''
})

const fileInput = ref<HTMLInputElement | null>(null)
const avatarUrl = ref<string>('')
const uploadingAvatar = ref(false)

const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const passwordFormRef = ref()
const passwordValid = ref(false)

const loading = ref(false)
const changingPassword = ref(false)

const snackbar = ref(false)
const snackbarText = ref('')
const snackbarColor = ref('success')

const loadUserProfile = async () => {
  loading.value = true
  try {
    const data = await getUserProfile()
    user.value = data
    const savedAvatar = localStorage.getItem('userAvatar')
    if (savedAvatar) {
      avatarUrl.value = savedAvatar
    }
  } catch (error) {
    showMsg(t('common.error'), 'error')
  } finally {
    loading.value = false
  }
}

const handleAvatarUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    const file = target.files[0]
    uploadingAvatar.value = true
    try {
      const reader = new FileReader()
      reader.onload = (e) => {
        const avatarDataUrl = e.target?.result as string
        avatarUrl.value = avatarDataUrl
        localStorage.setItem('userAvatar', avatarDataUrl)
        window.dispatchEvent(new CustomEvent('avatarUpdated', { detail: { avatarUrl: avatarDataUrl } }))
        showMsg(t('profile.avatarUpdated'), 'success')
        if (fileInput.value) {
          fileInput.value.value = ''
        }
      }
      reader.readAsDataURL(file)
    } catch (error) {
      showMsg(t('common.error'), 'error')
      if (fileInput.value) {
        fileInput.value.value = ''
      }
    } finally {
      uploadingAvatar.value = false
    }
  }
}

const changePassword = async () => {
  changingPassword.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    showMsg(t('profile.passwordUpdated'), 'success')
    passwordForm.value = {
      oldPassword: '',
      newPassword: '',
      confirmPassword: ''
    }
    if (passwordFormRef.value) {
      passwordFormRef.value.reset()
    }
  } catch (error) {
    showMsg(t('profile.passwordError'), 'error')
  } finally {
    changingPassword.value = false
  }
}

const handleImageError = (event: Event) => {
  const target = event.target as HTMLImageElement
  target.src = ''
}

const showMsg = (text: string, color = 'success') => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

onMounted(() => {
  loadUserProfile()
})
</script>

<style scoped>
.profile-banner {
  height: 120px;
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgba(var(--v-theme-primary), 0.7) 100%);
}
.profile-avatar {
  border: 4px solid rgb(var(--v-theme-surface));
  background: rgb(var(--v-theme-surface));
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}
.profile-camera-btn {
  position: absolute;
  bottom: 0;
  right: 0;
}
</style>

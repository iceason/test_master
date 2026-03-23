<template>
  <v-container class="fill-height align-center py-8 px-6" style="max-width: 1400px;">
    <!-- 主要内容区域 -->
    <v-row class="mb-10 justify-center" align="stretch">
      <!-- 左侧个人信息 -->
      <v-col cols="12" md="4" class="d-flex">
        <v-card variant="elevated" elevation="1" class="rounded-xl overflow-hidden transition-swing flex-grow-1">
          <div class="pa-6">
            <!-- 头像 -->
            <div class="d-flex flex-column items-center justify-center mb-6">
              <div class="relative mb-4">
                <v-avatar size="160" rounded="full" class="bg-primary-container">
                  <img v-if="avatarUrl" :src="avatarUrl" :alt="user.name" @error="handleImageError" class="object-cover rounded-full">
                  <v-icon v-else icon="mdi-account" size="80" color="on-primary-container"></v-icon>
                </v-avatar>
                <!-- 上传按钮 -->
                <input type="file" accept="image/*" class="d-none" ref="fileInput" @change="handleAvatarUpload">
                <v-btn
                  class="absolute bottom-0 right-0 rounded-full"
                  color="primary"
                  size="small"
                  @click="$refs.fileInput.click()"
                  :loading="uploadingAvatar"
                >
                  <v-icon icon="mdi-camera"></v-icon>
                </v-btn>
              </div>
              
              <!-- 用户信息 -->
              <h4 class="text-subtitle-1 font-weight-medium mb-1">{{ user.name }}</h4>
              <p class="text-body-1 text-medium-emphasis mb-4">{{ user.email }}</p>
              
              <!-- 头像提示 -->
              <p class="text-caption text-medium-emphasis text-center">{{ $t('profile.avatarTip') }}</p>
            </div>
          </div>
        </v-card>
      </v-col>
      
      <!-- 右侧设置区域 -->
      <v-col cols="12" md="6" class="pl-0 pl-md-6 d-flex">
        <!-- 密码修改表单 -->
        <v-card variant="elevated" elevation="1" class="rounded-xl overflow-hidden transition-swing flex-grow-1">
          <div class="pa-6">
            <h3 class="text-h6 font-weight-bold mb-6 text-on-surface">{{ $t('profile.changePassword') }}</h3>
            
            <v-form ref="passwordFormRef" v-model="passwordValid">
              <v-row dense>
                <v-col cols="12">
                  <v-text-field v-model="passwordForm.oldPassword" :label="$t('profile.fields.oldPassword')" type="password" :rules="[v => !!v || $t('common.required')]" variant="outlined" density="compact" required class="mb-4"></v-text-field>
                </v-col>
                <v-col cols="12">
                  <v-text-field v-model="passwordForm.newPassword" :label="$t('profile.fields.newPassword')" type="password" :rules="[v => !!v || $t('common.required'), v => v.length >= 6 || $t('profile.passwordTooShort')]" variant="outlined" density="compact" required class="mb-4"></v-text-field>
                </v-col>
                <v-col cols="12">
                  <v-text-field v-model="passwordForm.confirmPassword" :label="$t('profile.fields.confirmPassword')" type="password" :rules="[v => !!v || $t('common.required'), v => v === passwordForm.newPassword || $t('profile.passwordsNotMatch')]" variant="outlined" density="compact" required class="mb-4"></v-text-field>
                </v-col>
              </v-row>
              
              <!-- 操作按钮 -->
              <div class="d-flex justify-end mt-6">
                <v-btn color="primary" variant="flat" class="text-none" @click="changePassword" :disabled="!passwordValid || changingPassword">{{ changingPassword ? $t('common.loading') : $t('profile.updatePassword') }}</v-btn>
              </div>
            </v-form>
          </div>
        </v-card>
      </v-col>
    </v-row>
    
    <!-- 成功提示 -->
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

// 用户信息
const user = ref<User>({
  id: 0,
  name: '',
  email: ''
})

// 头像相关
const fileInput = ref<HTMLInputElement | null>(null)
const avatarUrl = ref<string>('')
const uploadingAvatar = ref(false)

// 密码表单
const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 表单验证
const passwordFormRef = ref()
const passwordValid = ref(false)

// 加载状态
const loading = ref(false)
const changingPassword = ref(false)

// 提示信息
const snackbar = ref(false)
const snackbarText = ref('')
const snackbarColor = ref('success')

// 加载用户信息
const loadUserProfile = async () => {
  loading.value = true
  try {
    const data = await getUserProfile()
    user.value = data
    // 从localStorage加载保存的头像
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

// 上传头像
const handleAvatarUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    const file = target.files[0]
    uploadingAvatar.value = true
    try {
      // 生成预览URL
      const reader = new FileReader()
      reader.onload = (e) => {
        const avatarDataUrl = e.target?.result as string
        avatarUrl.value = avatarDataUrl
        // 保存到localStorage实现持久化
        localStorage.setItem('userAvatar', avatarDataUrl)
        // 通知首页更新头像
        window.dispatchEvent(new CustomEvent('avatarUpdated', { detail: { avatarUrl: avatarDataUrl } }))
        showMsg(t('profile.avatarUpdated'), 'success')
        // 重置文件输入
        if (fileInput.value) {
          fileInput.value.value = ''
        }
      }
      reader.readAsDataURL(file)
    } catch (error) {
      showMsg(t('common.error'), 'error')
      // 重置文件输入
      if (fileInput.value) {
        fileInput.value.value = ''
      }
    } finally {
      uploadingAvatar.value = false
    }
  }
}

// 修改密码
const changePassword = async () => {
  changingPassword.value = true
  try {
    // 模拟密码修改
    await new Promise(resolve => setTimeout(resolve, 1000))
    showMsg(t('profile.passwordUpdated'), 'success')
    // 重置密码表单
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

// 处理图片加载错误
const handleImageError = (event: Event) => {
  const target = event.target as HTMLImageElement
  target.src = ''
}

// 显示提示信息
const showMsg = (text: string, color = 'success') => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

// 组件挂载时加载用户信息
onMounted(() => {
  loadUserProfile()
})
</script>

<style scoped>
.border-e {
  border-right: 1px solid rgba(0, 0, 0, 0.08) !important;
}

.border-opacity-12 {
  border-color: rgba(0, 0, 0, 0.12) !important;
}

.bg-primary-container { background-color: rgba(var(--v-theme-primary), 0.12) !important; }
.text-on-primary-container { color: rgb(var(--v-theme-primary)) !important; }

.object-cover {
  object-fit: cover;
  width: 100%;
  height: 100%;
}

.list-disc {
  list-style-type: disc !important;
}

.pl-5 {
  padding-left: 1.25rem !important;
}

.space-y-2 > * + * {
  margin-top: 0.5rem !important;
}
</style>
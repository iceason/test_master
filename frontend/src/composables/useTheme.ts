import { ref, watch, onMounted } from 'vue'
import { useTheme as useVuetifyTheme } from 'vuetify'

const THEME_KEY = 'app-theme'

export function useTheme() {
  const vuetifyTheme = useVuetifyTheme()
  const isDark = ref(false)

  // 初始化主题
  const initTheme = () => {
    // 从 localStorage 读取保存的主题
    const savedTheme = localStorage.getItem(THEME_KEY)
    
    if (savedTheme) {
      isDark.value = savedTheme === 'dark'
    } else {
      // 如果没有保存的主题，检查系统偏好
      isDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches
    }
    
    // 应用主题
    vuetifyTheme.global.name.value = isDark.value ? 'dark' : 'light'
  }

  // 切换主题
  const toggleTheme = () => {
    isDark.value = !isDark.value
  }

  // 设置特定主题
  const setTheme = (dark: boolean) => {
    isDark.value = dark
  }

  // 监听主题变化，保存到 localStorage 并应用
  watch(isDark, (newValue) => {
    vuetifyTheme.global.name.value = newValue ? 'dark' : 'light'
    localStorage.setItem(THEME_KEY, newValue ? 'dark' : 'light')
    
    // 更新 HTML 根元素的 data-theme 属性（可选，用于 CSS 变量）
    document.documentElement.setAttribute('data-theme', newValue ? 'dark' : 'light')
  })

  // 监听系统主题变化（可选）
  const watchSystemTheme = () => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    mediaQuery.addEventListener('change', (e) => {
      // 只在用户没有手动设置主题时才跟随系统
      if (!localStorage.getItem(THEME_KEY)) {
        isDark.value = e.matches
      }
    })
  }

  onMounted(() => {
    initTheme()
    watchSystemTheme()
  })

  return {
    isDark,
    toggleTheme,
    setTheme,
    initTheme,
  }
}

import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { mdiSvgSet, svgAliases } from './icons'
import { zhHans, en } from 'vuetify/locale'

// 浅色主题 - 优化配色（更舒适的配色）
const lightTheme = {
  dark: false,
  colors: {
    background: '#F8F9FA',      // 更清新的浅灰蓝背景（护眼）
    surface: '#FFFFFF',         // 纯白卡片
    primary: '#2196F3',         // 稍亮的 Material Blue
    'primary-darken-1': '#1976D2',
    secondary: '#26A69A',       // Teal - 更现代
    'secondary-darken-1': '#00897B',
    tertiary: '#FF7043',        // Deep Orange - 温暖的强调色
    error: '#EF5350',           // 柔和的红色
    info: '#29B6F6',            // 明亮的蓝色
    success: '#66BB6A',         // 柔和的绿色
    warning: '#FFA726',         // 橙色警告
    'on-background': '#2C3E50', // 更柔和的深蓝灰文字
    'on-surface': '#2C3E50',    // 更柔和的深蓝灰文字
    'on-primary': '#FFFFFF',
    'on-secondary': '#FFFFFF',
    'surface-variant': '#ECF0F1', // 更柔和的浅灰背景
    'on-surface-variant': '#5D6D7E',
  }
}

// 深色主题 - 优化配色（降低白色亮度，更护眼）
const darkTheme = {
  dark: true,
  colors: {
    background: '#0D1117',      // GitHub 风格的深色背景（稍微带点蓝）
    surface: '#161B22',         // 稍浅的卡片背景
    primary: '#58A6FF',         // GitHub 风格的蓝色（不刺眼）
    'primary-darken-1': '#1F6FEB',
    secondary: '#3FB950',       // GitHub 风格的绿色
    'secondary-darken-1': '#2EA043',
    tertiary: '#F78166',        // 柔和的橙色
    error: '#F85149',           // 柔和的红色
    info: '#79C0FF',            // 柔和的蓝色
    success: '#56D364',         // 柔和的绿色
    warning: '#E3B341',         // 柔和的黄色
    'on-background': '#C9D1D9', // 降低亮度的灰白色（不刺眼）
    'on-surface': '#C9D1D9',    // 降低亮度的灰白色（不刺眼）
    'on-primary': '#0D1117',    // 深色文字在主色上
    'on-secondary': '#0D1117',  // 深色文字在次色上
    'surface-variant': '#21262D', // 更深的灰色变体
    'on-surface-variant': '#8B949E', // 更柔和的次要文字
  }
}

const savedLocale = localStorage.getItem('locale') || 'zh'

export default createVuetify({
  components,
  directives,
  locale: {
    locale: savedLocale === 'zh' ? 'zhHans' : 'en',
    fallback: 'en',
    messages: { zhHans, en },
  },
  icons: {
    defaultSet: 'mdi',
    aliases: svgAliases,
    sets: {
      mdi: mdiSvgSet,
    },
  },
  theme: {
    defaultTheme: 'light',
    themes: {
      light: lightTheme,
      dark: darkTheme,
    },
  },
  defaults: {
    global: {
      ripple: true,
    },
    VCard: {
      elevation: 1,
      rounded: 'xl',
      variant: 'elevated',
    },
    VBtn: {
      rounded: 'lg',
      fontWeight: '500',
      letterSpacing: '0',
      variant: 'flat',
      size: 'default',
    },
    VTextField: {
      variant: 'outlined',
      density: 'compact',
      color: 'primary',
      hideDetails: 'auto',
    },
    VSelect: {
      variant: 'outlined',
      density: 'compact',
      color: 'primary',
      hideDetails: 'auto',
    },
    VAutocomplete: {
      variant: 'outlined',
      density: 'compact',
      color: 'primary',
      hideDetails: 'auto',
    },
    VTextarea: {
      variant: 'outlined',
      density: 'compact',
      color: 'primary',
      hideDetails: 'auto',
    },
    VSwitch: {
      color: 'primary',
      density: 'compact',
      hideDetails: 'auto',
    },
    VCheckbox: {
      color: 'primary',
      density: 'compact',
      hideDetails: 'auto',
    },
    VRadio: {
      color: 'primary',
      density: 'compact',
    },
    VRadioGroup: {
      density: 'compact',
      hideDetails: 'auto',
    },
    VFileInput: {
      variant: 'outlined',
      density: 'compact',
      color: 'primary',
      hideDetails: 'auto',
    },
    VList: {
      density: 'compact',
      nav: true,
    },
    VListItem: {
      density: 'compact',
      minHeight: '36px',
    },
    VChip: {
      density: 'compact',
      size: 'small',
      label: true,
    },
    VDataTable: {
      density: 'compact',
      hover: true,
      fixedHeader: true,
    },
    VTable: {
      density: 'compact',
    },
    VDialog: {
      transition: 'dialog-bottom-transition',
    },
    VNavigationDrawer: {
      elevation: 1,
      color: 'surface',
    },
    VAppBar: {
      elevation: 0,
      color: 'surface',
      density: 'compact',
    },
    VToolbar: {
      density: 'compact',
      color: 'surface',
    },
    VTab: {
      density: 'compact',
    },
    VTabs: {
      density: 'compact',
      color: 'primary',
    },
    VAlert: {
      density: 'compact',
      variant: 'tonal',
      rounded: 'lg',
    },
    VBadge: {
      color: 'primary',
    },
    VTooltip: {
      location: 'top',
    },
    VSnackbar: {
      location: 'top right',
      rounded: 'lg',
    },
    VDivider: {
      class: 'border-opacity-12',
    },
    VProgressLinear: {
      color: 'primary',
      rounded: true,
      height: 4,
    },
    VProgressCircular: {
      color: 'primary',
    },
    VPagination: {
      density: 'compact',
      activeColor: 'primary',
      rounded: 'lg',
    },
  },
})

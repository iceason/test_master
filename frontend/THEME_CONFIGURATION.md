# 主题配置文档

## 概述

项目支持白天/黑夜两种主题模式，配色方案经过优化，确保在两种模式下都具有良好的可读性和美观性。

---

## 主题切换

### 使用方法

**界面切换**：
- 点击顶部工具栏的 ☀️/🌙 图标即可切换主题
- 主题偏好会自动保存到浏览器 localStorage

**代码中使用**：
```typescript
import { useTheme } from '@/composables/useTheme'

const { isDark, toggleTheme, setTheme } = useTheme()

// 切换主题
toggleTheme()

// 设置特定主题
setTheme(true)  // 深色
setTheme(false) // 浅色
```

---

## 配色方案

### 浅色主题 (Light)

优化为更柔和、现代的配色：

| 颜色 | 值 | 用途 |
|------|-----|------|
| **background** | `#F5F5F5` | 页面背景（柔和灰） |
| **surface** | `#FFFFFF` | 卡片、对话框背景 |
| **primary** | `#1976D2` | 主要操作按钮（Material Blue） |
| **secondary** | `#26A69A` | 次要操作（Teal） |
| **tertiary** | `#FF7043` | 强调色（Deep Orange） |
| **error** | `#EF5350` | 错误提示 |
| **success** | `#66BB6A` | 成功提示 |
| **warning** | `#FFA726` | 警告提示 |
| **info** | `#29B6F6` | 信息提示 |

**设计理念**：
- ✅ 使用柔和的灰色背景，减少眼睛疲劳
- ✅ 高对比度的文字和背景
- ✅ 温暖的强调色，现代化风格

---

### 深色主题 (Dark)

遵循 Material Design 3 深色主题规范：

| 颜色 | 值 | 用途 |
|------|-----|------|
| **background** | `#121212` | 页面背景（Material 标准深色） |
| **surface** | `#1E1E1E` | 卡片、对话框背景 |
| **primary** | `#42A5F5` | 主要操作按钮（更亮的蓝色） |
| **secondary** | `#26A69A` | 次要操作（Teal，深浅通用） |
| **tertiary** | `#FF8A65` | 强调色（柔和橙色） |
| **error** | `#EF5350` | 错误提示 |
| **success** | `#81C784` | 成功提示 |
| **warning** | `#FFB74D` | 警告提示 |
| **info** | `#4FC3F7` | 信息提示 |

**设计理念**：
- ✅ 真正的深色背景 (#121212)，符合 Material Design 规范
- ✅ 调整颜色亮度，在深色背景下保持可读性
- ✅ 减少蓝光，适合夜间使用

---

## 视觉对比

### 页面背景

```
浅色模式:
┌─────────────────────────────────┐
│ #F5F5F5 (柔和灰背景)             │
│   ┌───────────────────────┐     │
│   │ #FFFFFF (白色卡片)     │     │
│   │                       │     │
│   └───────────────────────┘     │
└─────────────────────────────────┘

深色模式:
┌─────────────────────────────────┐
│ #121212 (深色背景)               │
│   ┌───────────────────────┐     │
│   │ #1E1E1E (深灰卡片)     │     │
│   │                       │     │
│   └───────────────────────┘     │
└─────────────────────────────────┘
```

### 按钮颜色

```
浅色模式:
[Primary #1976D2] [Secondary #26A69A] [Error #EF5350]

深色模式:
[Primary #42A5F5] [Secondary #26A69A] [Error #EF5350]
```

---

## 自动功能

### 1. 系统主题检测

首次访问时，如果用户没有设置偏好，会自动检测系统主题：

```typescript
// 检测系统是否使用深色模式
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
```

### 2. 主题持久化

用户选择的主题会自动保存到 `localStorage`：

```typescript
// 保存位置
localStorage.setItem('app-theme', 'dark' | 'light')
```

### 3. 平滑过渡

主题切换时有 0.3s 的平滑过渡动画：

```css
* {
  transition: background-color 0.3s ease, 
              color 0.3s ease, 
              border-color 0.3s ease;
}
```

---

## 组件适配

### 自动适配的组件

所有 Vuetify 组件会自动适配主题颜色：

- ✅ VCard - 卡片背景和边框
- ✅ VBtn - 按钮颜色
- ✅ VTextField - 输入框样式
- ✅ VAppBar - 顶栏背景
- ✅ VNavigationDrawer - 侧边栏
- ✅ VList - 列表项
- ✅ VDataTable - 数据表格

### 需要手动适配的元素

如果使用自定义 CSS，注意使用主题变量：

```vue
<!-- ❌ 错误：硬编码颜色 -->
<div style="background: #FFFFFF; color: #000000">

<!-- ✅ 正确：使用主题类 -->
<div class="bg-surface text-on-surface">

<!-- ✅ 正确：使用 CSS 变量 -->
<div :style="{ 
  background: `rgb(var(--v-theme-surface))`,
  color: `rgb(var(--v-theme-on-surface))`
}">
```

---

## 最佳实践

### 1. 使用语义化颜色

```vue
<!-- ✅ 推荐 -->
<v-btn color="primary">主要操作</v-btn>
<v-btn color="error">删除</v-btn>
<v-btn color="secondary">次要操作</v-btn>

<!-- ❌ 避免 -->
<v-btn color="#1976D2">操作</v-btn>
```

### 2. 使用主题类

```vue
<!-- 背景色 -->
<div class="bg-background">页面背景</div>
<div class="bg-surface">卡片背景</div>
<div class="bg-primary">主色背景</div>

<!-- 文字颜色 -->
<span class="text-on-background">正文</span>
<span class="text-on-surface">卡片内文字</span>
<span class="text-primary">主色文字</span>
```

### 3. 边框和分隔线

```vue
<!-- 使用主题适配的边框类 -->
<div class="border-b">底部边框</div>
<div class="border-e">右侧边框</div>

<!-- 分隔线 -->
<v-divider></v-divider>
```

### 4. 避免硬编码透明度

```css
/* ❌ 避免 */
.my-class {
  background: rgba(0, 0, 0, 0.1);
}

/* ✅ 推荐 */
.my-class {
  background: rgba(var(--v-theme-on-surface), 0.1);
}
```

---

## 滚动条样式

滚动条会根据主题自动调整：

### 浅色模式
- 滑块：`rgba(0, 0, 0, 0.2)`
- Hover：`rgba(0, 0, 0, 0.3)`

### 深色模式
- 滑块：`rgba(255, 255, 255, 0.2)`
- Hover：`rgba(255, 255, 255, 0.3)`

---

## 调试技巧

### 1. 查看当前主题

```javascript
// 在浏览器控制台
localStorage.getItem('app-theme')  // 'light' 或 'dark'
```

### 2. 强制切换主题

```javascript
// 强制浅色模式
localStorage.setItem('app-theme', 'light')
location.reload()

// 强制深色模式
localStorage.setItem('app-theme', 'dark')
location.reload()
```

### 3. 检查颜色变量

```javascript
// 在浏览器控制台
getComputedStyle(document.documentElement)
  .getPropertyValue('--v-theme-primary')
```

---

## 无障碍性

### 对比度

所有颜色组合都符合 WCAG 2.1 AA 级标准：

| 组合 | 对比度 | 评级 |
|------|--------|------|
| primary / on-primary | 4.5:1+ | ✅ AA |
| surface / on-surface | 12:1+ | ✅ AAA |
| background / on-background | 10:1+ | ✅ AAA |

### 用户偏好

尊重用户的系统设置：
- ✅ 首次访问检测系统主题
- ✅ 保存用户手动选择
- ✅ 提供明显的切换按钮

---

## 性能优化

### 1. 按需加载

主题配置在应用启动时一次性加载，不会重复加载。

### 2. CSS 变量

使用 CSS 变量而不是重新渲染组件：

```css
/* Vuetify 自动生成 */
:root {
  --v-theme-primary: 25, 118, 210;
  --v-theme-surface: 255, 255, 255;
}
```

### 3. 过渡动画

仅在必要的属性上添加过渡，避免影响性能：

```css
/* 只过渡颜色相关属性 */
transition: background-color 0.3s ease, 
            color 0.3s ease, 
            border-color 0.3s ease;
```

---

## 常见问题

### Q: 为什么切换主题后某些颜色没有变化？

A: 可能使用了硬编码的颜色值。请使用主题类或 CSS 变量。

### Q: 如何在组件中获取当前主题？

```typescript
import { useTheme } from '@/composables/useTheme'

const { isDark } = useTheme()
// isDark.value === true 表示深色模式
```

### Q: 如何自定义主题颜色？

修改 `frontend/src/plugins/vuetify.ts` 中的配色：

```typescript
const lightTheme = {
  colors: {
    primary: '#你的颜色',
    // ...
  }
}
```

### Q: 深色模式下文字看不清怎么办？

检查是否使用了正确的文字颜色类：
- `text-on-background` - 用于背景色上的文字
- `text-on-surface` - 用于卡片上的文字
- `text-on-primary` - 用于主色背景上的文字

---

## 扩展功能

### 自动切换（可选）

可以根据时间自动切换主题：

```typescript
// 示例：18:00-6:00 自动使用深色模式
const hour = new Date().getHours()
const shouldBeDark = hour >= 18 || hour < 6

if (shouldBeDark !== isDark.value) {
  toggleTheme()
}
```

### 自定义主题（高级）

创建更多主题变体：

```typescript
// vuetify.ts
const themes = {
  light: lightTheme,
  dark: darkTheme,
  oceanBlue: { /* 自定义 */ },
  forestGreen: { /* 自定义 */ },
}
```

---

## 资源链接

- [Material Design 3 - Dark Theme](https://m3.material.io/styles/color/dark-theme/overview)
- [Vuetify Themes](https://vuetifyjs.com/en/features/theme/)
- [WCAG Color Contrast](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)

---

## 更新日志

| 日期 | 版本 | 更新内容 |
|------|------|---------|
| 2026-02-06 | 1.0 | 实现白天/黑夜模式切换，优化配色方案 |

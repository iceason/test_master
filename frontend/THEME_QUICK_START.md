# 主题快速开始

## 🚀 立即使用

### 切换主题

**方法 1：使用界面按钮**

在顶部工具栏找到主题切换按钮：

```
┌──────────────────────────────────┐
│ Test Master    ☀️/🌙 中文 👤   │  ← 点击这里
└──────────────────────────────────┘
```

- ☀️ = 当前浅色模式，点击切换到深色
- 🌙 = 当前深色模式，点击切换到浅色

**方法 2：使用键盘快捷键（可选实现）**

```
Ctrl + Shift + D  // 切换主题
```

---

## 📋 功能说明

### ✅ 已实现的功能

1. **双主题支持**
   - ☀️ 浅色模式（白天）
   - 🌙 深色模式（夜间）

2. **自动保存**
   - 你的主题选择会自动保存
   - 下次访问时自动应用

3. **系统检测**
   - 首次访问时检测系统主题偏好
   - 跟随系统设置（如果没有手动设置）

4. **平滑过渡**
   - 0.3秒的优雅过渡动画
   - 不会造成视觉突变

5. **全局应用**
   - 所有页面统一主题
   - 所有组件自动适配

---

## 🎨 配色预览

### 浅色模式 ☀️

```
背景: 柔和灰 #F5F5F5
卡片: 纯白色 #FFFFFF
主色: 蓝色   #1976D2
次色: 青绿   #26A69A
```

**适合**：
- 白天办公
- 光线充足环境
- 打印文档

---

### 深色模式 🌙

```
背景: 深灰色 #121212
卡片: 中灰色 #1E1E1E
主色: 亮蓝色 #42A5F5
次色: 青绿   #26A69A
```

**适合**：
- 夜间工作
- 低光环境
- 减少眼睛疲劳

---

## 🔧 开发者使用

### 在组件中使用

```vue
<template>
  <div>
    <!-- 显示当前主题 -->
    <p>当前主题: {{ isDark ? '深色' : '浅色' }}</p>
    
    <!-- 切换按钮 -->
    <v-btn @click="toggleTheme">
      切换主题
    </v-btn>
  </div>
</template>

<script setup lang="ts">
import { useTheme } from '@/composables/useTheme'

const { isDark, toggleTheme } = useTheme()
</script>
```

### 使用主题颜色

```vue
<!-- 方法 1: 使用 Vuetify 颜色类 -->
<v-btn color="primary">主要按钮</v-btn>
<div class="bg-surface">卡片背景</div>
<span class="text-on-surface">文字</span>

<!-- 方法 2: 使用 CSS 变量 -->
<div :style="{ 
  background: `rgb(var(--v-theme-surface))`,
  color: `rgb(var(--v-theme-on-surface))`
}">
  自定义内容
</div>
```

---

## 💡 提示和技巧

### 1. 重置主题设置

如果主题显示异常，可以清除保存的设置：

```javascript
// 在浏览器控制台执行
localStorage.removeItem('app-theme')
location.reload()
```

### 2. 强制使用特定主题

```javascript
// 强制浅色
localStorage.setItem('app-theme', 'light')

// 强制深色
localStorage.setItem('app-theme', 'dark')

location.reload()
```

### 3. 检查当前主题

```javascript
// 在浏览器控制台
localStorage.getItem('app-theme')
// 返回: 'light' 或 'dark'
```

---

## ❓ 常见问题

### Q: 主题不会自动保存？

**A**: 检查浏览器是否允许使用 localStorage。某些隐私模式会禁用它。

### Q: 某些颜色没有变化？

**A**: 可能使用了硬编码颜色。请使用 Vuetify 的颜色类或主题变量。

### Q: 切换主题时闪烁？

**A**: 正常现象，通常只在开发模式下出现。生产环境会更流畅。

### Q: 如何设置默认主题？

**A**: 修改 `frontend/src/plugins/vuetify.ts`：

```typescript
theme: {
  defaultTheme: 'dark',  // 改为 'dark' 默认深色
  themes: {
    light: lightTheme,
    dark: darkTheme,
  },
}
```

---

## 🎯 最佳实践

### ✅ 推荐做法

```vue
<!-- 使用语义化颜色 -->
<v-btn color="primary">确认</v-btn>
<v-btn color="error">删除</v-btn>

<!-- 使用主题类 -->
<div class="bg-surface text-on-surface">
  内容
</div>
```

### ❌ 避免做法

```vue
<!-- 不要硬编码颜色 -->
<v-btn color="#1976D2">按钮</v-btn>

<!-- 不要使用固定颜色 -->
<div style="background: white; color: black;">
  内容
</div>
```

---

## 📚 相关文档

- `THEME_CONFIGURATION.md` - 详细配置文档
- `THEME_VISUAL_GUIDE.md` - 视觉效果指南
- Vuetify 主题文档: https://vuetifyjs.com/en/features/theme/

---

## 🆘 获取帮助

如果遇到问题：

1. 查看浏览器控制台是否有错误
2. 尝试清除 localStorage 和缓存
3. 检查是否使用了最新版本的代码
4. 参考详细配置文档

---

## 🎉 开始使用

1. 刷新浏览器页面
2. 找到顶部工具栏的 ☀️/🌙 图标
3. 点击切换主题
4. 享受更舒适的视觉体验！

**提示**：系统会自动记住你的选择，下次访问时直接应用。

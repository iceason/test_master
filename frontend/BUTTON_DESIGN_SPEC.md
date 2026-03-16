# 按钮设计规范

## 统一标准

### 1. 主操作按钮（Primary Actions）
用于页面主要操作：新建、保存、删除等

```vue
<v-btn 
  color="primary|error|secondary"
  prepend-icon="mdi-xxx"
  elevation="2"
  rounded="lg"
  class="text-none"
>
  Button Text
</v-btn>
```

**属性说明**：
- `elevation="2"` - 轻微阴影，强调重要性
- `rounded="lg"` - 大圆角，现代美观
- `class="text-none"` - 禁用大写转换，保持原文本

**容器间距**：
```vue
<div class="d-flex gap-2">
  <!-- 多个按钮 -->
</div>
```

---

### 2. 图标按钮（Icon Buttons）
用于列表项、卡片等内嵌操作

```vue
<v-btn 
  icon="mdi-xxx"
  variant="text"
  size="small"
  density="comfortable"
>
</v-btn>
```

**属性说明**：
- `size="small"` - 小尺寸但不至于太小（不用 x-small）
- `variant="text"` - 无背景，简洁
- `density="comfortable"` - 舒适的点击区域

---

### 3. 对话框按钮（Dialog Actions）
用于确认对话框底部

```vue
<v-card-actions class="px-6 pb-4">
  <v-spacer></v-spacer>
  <v-btn 
    variant="text" 
    color="grey-darken-1"
    rounded="lg"
    class="text-none"
    @click="cancel"
  >
    Cancel
  </v-btn>
  <v-btn 
    color="primary|error" 
    variant="flat"
    rounded="lg"
    class="text-none ml-3"
    @click="confirm"
  >
    Confirm
  </v-btn>
</v-card-actions>
```

**间距规范**：
- 容器：`class="px-6 pb-4"` (左右24px，下16px)
- 按钮间距：`class="ml-3"` (12px间距)
- 使用 `<v-spacer>` 推到右侧

---

### 4. 工具栏按钮（Toolbar Buttons）
用于工具栏、菜单触发器

```vue
<v-btn 
  icon="mdi-xxx"
  variant="text"
  size="default"
  rounded="lg"
>
</v-btn>

<!-- 或带文本 -->
<v-btn 
  prepend-icon="mdi-xxx"
  variant="tonal"
  rounded="lg"
  class="text-none"
>
  Export
</v-btn>
```

---

### 5. 表格操作按钮（Table Actions）
用于数据表格的操作列

```vue
<v-btn
  icon="mdi-xxx"
  variant="text"
  size="small"
  density="comfortable"
>
</v-btn>
```

---

## 颜色使用规范

### 主要颜色
- **primary** - 主要操作（新建、保存、确认）
- **error** - 危险操作（删除、取消订阅）
- **secondary** - 次要操作（导出、刷新）
- **success** - 成功操作（完成、发布）
- **grey-darken-1** - 取消操作

### Variant 类型
- **flat** - 实心背景（确认按钮）
- **tonal** - 半透明背景（次要操作）
- **text** - 无背景（取消、图标按钮）
- **outlined** - 边框样式（中性操作）

---

## 间距规范

### 水平间距（Horizontal Spacing）
```vue
<!-- 多个按钮容器 -->
<div class="d-flex gap-2">  <!-- 8px -->
<div class="d-flex gap-3">  <!-- 12px -->
<div class="d-flex gap-4">  <!-- 16px -->

<!-- 单个按钮间距 -->
<v-btn class="ml-2">  <!-- margin-left: 8px -->
<v-btn class="ml-3">  <!-- margin-left: 12px -->
<v-btn class="mr-2">  <!-- margin-right: 8px -->
```

### 推荐间距
- **按钮组**: `gap-2` (8px) 或 `gap-3` (12px)
- **对话框按钮**: `ml-3` (12px)
- **工具栏按钮**: `gap-2` (8px)

---

## 尺寸规范

### Size 属性
- **x-small** - ❌ 不推荐使用（太小）
- **small** - ✅ 图标按钮、表格操作
- **default** - ✅ 工具栏按钮（默认值）
- **large** - ⚠️ 特殊场景（登录按钮、CTA）

### Elevation
- **0** - 平面按钮、对话框按钮
- **1** - 卡片、列表
- **2** - ✅ 主操作按钮（推荐）
- **3+** - 特殊强调

---

## 示例对比

### ❌ 不规范
```vue
<!-- 问题：缺少圆角、间距不统一 -->
<v-btn color="primary" @click="save">Save</v-btn>
<v-btn color="error" class="ml-2">Delete</v-btn>

<!-- 问题：图标按钮太小 -->
<v-btn icon="mdi-dots" size="x-small"></v-btn>
```

### ✅ 规范
```vue
<!-- 正确：统一样式、合适间距 -->
<div class="d-flex gap-2">
  <v-btn 
    color="primary" 
    elevation="2"
    rounded="lg"
    class="text-none"
    @click="save"
  >
    Save
  </v-btn>
  <v-btn 
    color="error" 
    elevation="2"
    rounded="lg"
    class="text-none"
    @click="delete"
  >
    Delete
  </v-btn>
</div>

<!-- 正确：合适大小的图标按钮 -->
<v-btn 
  icon="mdi-dots-vertical" 
  variant="text"
  size="small"
  density="comfortable"
>
</v-btn>
```

---

## 快速检查清单

- [ ] 主操作按钮有 `elevation="2"` 和 `rounded="lg"`
- [ ] 所有按钮有 `class="text-none"` （除非需要大写）
- [ ] 图标按钮使用 `size="small"`（不用 x-small）
- [ ] 对话框按钮都有 `rounded="lg"`
- [ ] 按钮容器使用 `gap-2` 或 `gap-3`
- [ ] 对话框按钮间距 `ml-3`
- [ ] 颜色使用符合语义（primary/error/secondary）

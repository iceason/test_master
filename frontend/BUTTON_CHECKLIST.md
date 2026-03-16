# 按钮优化验证清单

## 快速检查清单

使用此清单验证新添加的按钮是否符合设计规范。

---

## 主操作按钮检查 ✓

适用于：新建、保存、删除、提交等主要操作

```vue
<v-btn 
  color="primary|error|secondary"
  prepend-icon="mdi-xxx"              <!-- 如需要 -->
  elevation="2"                        <!-- ✓ 必须 -->
  rounded="lg"                         <!-- ✓ 必须 -->
  class="text-none"                    <!-- ✓ 必须 -->
  @click="action"
>
  {{ $t('xxx') }}
</v-btn>
```

### 检查项
- [ ] 有 `elevation="2"` 属性
- [ ] 有 `rounded="lg"` 属性
- [ ] 有 `class="text-none"` 类
- [ ] 颜色符合语义（primary/error/secondary）
- [ ] 如有图标，使用 `prepend-icon` 或 `append-icon`

---

## 图标按钮检查 ✓

适用于：菜单触发、工具栏操作

```vue
<v-btn 
  icon="mdi-xxx"
  variant="text"                       <!-- ✓ 必须 -->
  size="small"                         <!-- ✓ 必须（不用 x-small） -->
  density="comfortable"                <!-- ✓ 推荐 -->
  rounded="lg"                         <!-- ✓ 推荐 -->
>
</v-btn>
```

### 检查项
- [ ] 使用 `size="small"`（不是 x-small）
- [ ] 有 `variant="text"` 属性
- [ ] 有 `density="comfortable"` 属性（列表/树形场景）
- [ ] 有 `rounded="lg"` 属性（工具栏场景）

---

## 对话框按钮检查 ✓

适用于：确认对话框、表单对话框

```vue
<v-card-actions class="px-6 pb-4">   <!-- ✓ 容器必须 -->
  <v-spacer></v-spacer>               <!-- ✓ 必须 -->
  
  <!-- 取消按钮 -->
  <v-btn 
    variant="text"                     <!-- ✓ 必须 -->
    color="grey-darken-1"              <!-- ✓ 推荐 -->
    rounded="lg"                       <!-- ✓ 必须 -->
    class="text-none"                  <!-- ✓ 必须 -->
    @click="close"
  >
    {{ $t('common.cancel') }}
  </v-btn>
  
  <!-- 确认按钮 -->
  <v-btn 
    color="primary|error"              <!-- ✓ 必须 -->
    variant="flat"                     <!-- ✓ 必须 -->
    rounded="lg"                       <!-- ✓ 必须 -->
    class="text-none ml-3"             <!-- ✓ 必须（注意 ml-3） -->
    @click="confirm"
  >
    {{ $t('common.save') }}
  </v-btn>
</v-card-actions>
```

### 检查项
- [ ] 容器有 `class="px-6 pb-4"`
- [ ] 容器内有 `<v-spacer>`
- [ ] 取消按钮：`variant="text"`, `rounded="lg"`, `text-none`
- [ ] 确认按钮：`variant="flat"`, `rounded="lg"`, `text-none ml-3`
- [ ] 按钮间距是 `ml-3`（不是 ml-2）

---

## 按钮容器检查 ✓

适用于：多个按钮并排显示

```vue
<!-- 主操作区 -->
<div class="d-flex gap-2">            <!-- ✓ 或 gap-3 -->
  <v-btn>...</v-btn>
  <v-btn>...</v-btn>
</div>

<!-- 工具栏 -->
<div class="d-flex gap-1">            <!-- ✓ 紧凑场景 -->
  <v-btn icon>...</v-btn>
  <v-btn icon>...</v-btn>
</div>
```

### 检查项
- [ ] 使用 `d-flex` 布局
- [ ] 主操作区：`gap-2` 或 `gap-3`
- [ ] 工具栏图标：`gap-1` 或 `gap-2`
- [ ] 不使用 `mr-2` 等单独间距（除非有特殊原因）

---

## 按钮状态检查 ✓

### 禁用状态
```vue
<v-btn 
  :disabled="!valid || loading"      <!-- ✓ 使用响应式判断 -->
  :loading="loading"                 <!-- ✓ 异步操作显示加载 -->
>
```

### 检查项
- [ ] 异步操作有 `:loading` 属性
- [ ] 禁用逻辑使用 `:disabled` 绑定
- [ ] 禁用时仍保持样式美观

---

## 特殊场景检查 ✓

### 登录按钮（大按钮）
```vue
<v-btn
  block                                <!-- ✓ 全宽 -->
  color="primary"
  size="large"                         <!-- ✓ 大尺寸 -->
  elevation="2"
  rounded="lg"
  class="text-none font-weight-bold"  <!-- ✓ 加粗 -->
>
```

### 浮动操作按钮（FAB）
```vue
<v-btn
  icon="mdi-xxx"
  color="primary"
  size="large"
  elevation="4"                        <!-- ✓ 更高阴影 -->
  rounded="circle"                     <!-- ✓ 圆形 -->
>
```

### Snackbar 按钮（简单）
```vue
<v-btn variant="text" @click="close"> <!-- ✓ 无需过多装饰 -->
  Close
</v-btn>
```

---

## 颜色使用规范 ✓

### 语义化颜色
- [ ] `primary` - 主要操作（新建、保存、确认）
- [ ] `error` - 危险操作（删除、取消）
- [ ] `secondary` - 次要操作（导出、刷新）
- [ ] `success` - 成功确认（发布、完成）
- [ ] `grey-darken-1` - 取消、关闭

### 避免使用
- ❌ `warning` - 容易与 error 混淆
- ❌ 自定义颜色 - 除非品牌需要

---

## 常见错误 ❌

### 1. 图标按钮太小
```vue
<!-- ❌ 错误 -->
<v-btn icon="mdi-xxx" size="x-small"></v-btn>

<!-- ✅ 正确 -->
<v-btn icon="mdi-xxx" size="small" density="comfortable"></v-btn>
```

### 2. 对话框按钮缺少圆角
```vue
<!-- ❌ 错误 -->
<v-btn variant="flat" class="ml-2">Save</v-btn>

<!-- ✅ 正确 -->
<v-btn variant="flat" rounded="lg" class="text-none ml-3">Save</v-btn>
```

### 3. 按钮间距不统一
```vue
<!-- ❌ 错误 -->
<v-btn class="mr-2">Button1</v-btn>
<v-btn class="ml-1">Button2</v-btn>

<!-- ✅ 正确 -->
<div class="d-flex gap-2">
  <v-btn>Button1</v-btn>
  <v-btn>Button2</v-btn>
</div>
```

### 4. 主按钮缺少阴影
```vue
<!-- ❌ 错误 -->
<v-btn color="primary">Save</v-btn>

<!-- ✅ 正确 -->
<v-btn color="primary" elevation="2" rounded="lg" class="text-none">Save</v-btn>
```

### 5. 文本自动大写
```vue
<!-- ❌ 错误（按钮会显示 SAVE） -->
<v-btn>Save</v-btn>

<!-- ✅ 正确（按钮显示 Save） -->
<v-btn class="text-none">Save</v-btn>
```

---

## 新页面开发检查流程

### 步骤 1：设计阶段
- [ ] 确定页面主要操作（1-2个）
- [ ] 确定次要操作（2-3个）
- [ ] 规划按钮位置和层次

### 步骤 2：实现阶段
- [ ] 按照规范添加主操作按钮
- [ ] 添加图标按钮（如需要）
- [ ] 实现对话框及其按钮
- [ ] 使用正确的容器和间距

### 步骤 3：验证阶段
- [ ] 检查所有按钮大小
- [ ] 检查按钮间距
- [ ] 检查圆角和阴影
- [ ] 检查颜色语义
- [ ] 检查响应式表现

### 步骤 4：测试阶段
- [ ] 桌面端点击测试
- [ ] 移动端触摸测试
- [ ] 键盘导航测试
- [ ] 禁用/加载状态测试

---

## 快速参考

### 必备属性速查

| 按钮类型 | elevation | rounded | size | variant | class |
|---------|-----------|---------|------|---------|-------|
| 主操作 | `2` | `lg` | - | `flat` | `text-none` |
| 图标 | - | `lg` | `small` | `text` | - |
| 对话框确认 | - | `lg` | - | `flat` | `text-none ml-3` |
| 对话框取消 | - | `lg` | - | `text` | `text-none` |
| 工具栏图标 | - | `lg` | `small` | `text` | - |

### 间距速查

| 场景 | 间距方式 | 值 |
|-----|---------|---|
| 主操作按钮组 | `gap-2` 或 `gap-3` | 8px / 12px |
| 工具栏图标 | `gap-1` 或 `gap-2` | 4px / 8px |
| 对话框按钮 | `ml-3` | 12px |
| 对话框容器 | `px-6 pb-4` | 24px / 16px |

---

## 代码片段模板

### 主操作按钮
```vue
<v-btn 
  color="primary" 
  prepend-icon="mdi-plus"
  elevation="2"
  rounded="lg"
  class="text-none"
  @click="openDialog"
>
  {{ $t('xxx.new') }}
</v-btn>
```

### 图标菜单按钮
```vue
<v-menu>
  <template v-slot:activator="{ props }">
    <v-btn 
      icon="mdi-dots-vertical"
      variant="text"
      size="small"
      density="comfortable"
      v-bind="props"
    ></v-btn>
  </template>
  <v-list>...</v-list>
</v-menu>
```

### 标准对话框
```vue
<v-dialog v-model="dialog" max-width="500px">
  <v-card class="rounded-xl">
    <v-card-title>...</v-card-title>
    <v-card-text>...</v-card-text>
    <v-card-actions class="px-6 pb-4">
      <v-spacer></v-spacer>
      <v-btn variant="text" color="grey-darken-1" rounded="lg" class="text-none" @click="dialog = false">
        {{ $t('common.cancel') }}
      </v-btn>
      <v-btn color="primary" variant="flat" rounded="lg" class="text-none ml-3" @click="save">
        {{ $t('common.save') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</v-dialog>
```

---

## 工具和资源

### VS Code 代码片段
创建 `.vscode/vue.code-snippets`:
```json
{
  "Primary Button": {
    "prefix": "vbtn-primary",
    "body": [
      "<v-btn ",
      "  color=\"primary\"",
      "  elevation=\"2\"",
      "  rounded=\"lg\"",
      "  class=\"text-none\"",
      "  @click=\"$1\"",
      ">",
      "  {{ \\$t('$2') }}",
      "</v-btn>"
    ]
  }
}
```

### ESLint 规则（可选）
检测缺少必需属性的按钮

---

## 更新记录

| 日期 | 版本 | 更新内容 |
|------|------|---------|
| 2026-02-06 | 1.0 | 初始版本 |

---

## 问题反馈

如发现规范问题或需要补充，请：
1. 记录具体场景
2. 说明现有规范的不足
3. 提出改进建议

# useCRUDDialog Composable 使用指南

## 概述

`useCRUDDialog` 是一个通用的 CRUD（创建、读取、更新、删除）对话框 composable，用于减少 Agent/Task/Crew 等资源管理页面的重复代码。

## 基础用法

### 1. 简单场景（Crews.vue）

```vue
<script setup lang="ts">
import { onMounted } from 'vue'
import { useCRUDDialog } from '@/composables/useCRUDDialog'
import { api } from '@/api'
import type { Crew } from '@/api'

const {
  items: crews,
  loading,
  showDialog,
  form,
  dialogTitle,
  openCreateDialog,
  openEditDialog,
  saveItem,
  deleteItem,
  loadItems
} = useCRUDDialog<Crew>({
  resourceName: 'Crew',
  apiService: api.crews,
  defaultForm: {
    name: '',
    description: '',
    agent_ids: [],
    task_ids: [],
    process_type: 'sequential'
  },
  validate: (form) => {
    if (!form.name) return '请填写 Crew 名称'
    if (!form.agent_ids?.length) return '请至少选择一个 Agent'
    if (!form.task_ids?.length) return '请至少选择一个 Task'
    return null
  }
})

onMounted(() => {
  loadItems()
})
</script>

<template>
  <div>
    <el-button @click="openCreateDialog">新建 Crew</el-button>
    
    <el-table :data="crews" v-loading="loading">
      <!-- 表格列 -->
      <el-table-column label="操作">
        <template #default="{ row }">
          <el-button @click="openEditDialog(row)">编辑</el-button>
          <el-button @click="deleteItem(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <el-dialog v-model="showDialog" :title="dialogTitle">
      <el-form :model="form">
        <!-- 表单项 -->
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="saveItem">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
```

### 2. 复杂场景（Agents.vue - 带额外逻辑）

对于有额外业务逻辑的场景（如 Agents 的 Skills 推荐），可以组合使用：

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useCRUDDialog } from '@/composables/useCRUDDialog'
import { api } from '@/api'
import type { Agent, Skill } from '@/api'

// 基础 CRUD 逻辑
const {
  items: agents,
  loading,
  showDialog,
  form,
  dialogTitle,
  openCreateDialog,
  openEditDialog: baseOpenEditDialog,
  saveItem,
  deleteItem,
  loadItems
} = useCRUDDialog<Agent>({
  resourceName: 'Agent',
  apiService: api.agents,
  defaultForm: {
    name: '',
    role: '',
    goal: '',
    backstory: '',
    skills_config: {
      mode: 'auto',
      preferred: [],
      auto_match: true,
      include_patterns: [],
      exclude_patterns: []
    }
  },
  validate: (form) => {
    if (!form.name || !form.role || !form.goal || !form.backstory) {
      return '请填写所有必填项'
    }
    return null
  }
})

// 额外的业务逻辑
const availableSkills = ref<Skill[]>([])
const aiRecommending = ref(false)

const loadSkills = async () => {
  availableSkills.value = await api.skills.list()
}

const requestAIRecommendation = async () => {
  // AI 推荐逻辑...
}

// 扩展编辑逻辑（处理 skills_config）
const openEditDialog = (agent: Agent) => {
  baseOpenEditDialog(agent)
  // 额外处理...
}

onMounted(() => {
  loadItems()
  loadSkills()
})
</script>
```

## API 参考

### useCRUDDialog 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `resourceName` | `string` | 资源名称，用于提示消息（如 "Agent"、"Task"） |
| `apiService` | `object` | API 服务对象，需包含 `list`, `create`, `update`, `delete` 方法 |
| `defaultForm` | `Partial<T>` | 默认表单数据 |
| `validate` | `(form) => string \| null` | 可选的自定义验证函数，返回错误消息或 null |

### 返回值

| 属性/方法 | 类型 | 说明 |
|----------|------|------|
| `items` | `Ref<T[]>` | 资源列表 |
| `loading` | `Ref<boolean>` | 加载状态 |
| `showDialog` | `Ref<boolean>` | 对话框显示状态 |
| `form` | `Ref<Partial<T>>` | 表单数据 |
| `editingId` | `Ref<string \| null>` | 当前编辑的资源 ID |
| `isEditing` | `ComputedRef<boolean>` | 是否为编辑模式 |
| `dialogTitle` | `ComputedRef<string>` | 对话框标题 |
| `loadItems()` | `() => Promise<void>` | 加载资源列表 |
| `openCreateDialog()` | `() => void` | 打开创建对话框 |
| `openEditDialog(item)` | `(item: T) => void` | 打开编辑对话框 |
| `closeDialog()` | `() => void` | 关闭对话框 |
| `saveItem()` | `() => Promise<void>` | 保存（创建或更新） |
| `deleteItem(id)` | `(id: string) => Promise<void>` | 删除资源 |

## 优势

1. **减少重复代码** — 列表加载、对话框状态、CRUD 操作逻辑复用
2. **统一用户体验** — 所有资源管理页面的交互一致
3. **易于维护** — 修改一处，所有使用的地方都生效
4. **类型安全** — 完整的 TypeScript 支持

## 重构建议

### 优先级

1. **高优先级** — Crews.vue（最简单，没有额外逻辑）
2. **中优先级** — Tasks.vue（有分组展示，但 CRUD 逻辑可复用）
3. **低优先级** — Agents.vue（有 Skills 推荐等复杂逻辑，需要组合使用）

### 重构步骤

1. 导入 `useCRUDDialog`
2. 替换现有的 `ref` 状态声明
3. 替换 `loadItems`, `saveItem`, `deleteItem` 等方法
4. 更新模板中的变量引用
5. 保留特殊业务逻辑（如 AI 推荐、分组展示等）
6. 测试所有功能

## 注意事项

- 如果资源有复杂的嵌套结构，确保 `defaultForm` 完整定义
- 自定义验证函数应返回用户友好的错误消息
- 对于有额外业务逻辑的场景，可以扩展返回的方法（如示例中的 `openEditDialog`）

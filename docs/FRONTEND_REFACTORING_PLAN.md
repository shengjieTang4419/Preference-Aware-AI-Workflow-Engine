# 前端代码重构建议

## 问题诊断

### 代码量分析

| 文件 | 行数 | 问题 |
|-----|------|------|
| `Preferences.vue` | 504 | ❌ 太多状态管理 + 重复逻辑 |
| `LLMSettings.vue` | 491 | ❌ 大量重复表单代码 |
| `Chat.vue` | 436 | ❌ 110 行 SSE 流式处理逻辑 |
| `DiffViewer.vue` | 250 | ⚠️ 可以优化 |
| `Agents.vue` | 259 | ⚠️ 表单逻辑可提取 |

**总代码量：** 4202 行（.vue + .ts）

---

## 核心问题

### 1. **Chat.vue** - SSE 流式处理逻辑未提取

**问题：** 127-236 行（110 行）的 SSE 流式处理逻辑直接写在组件中

```vue
// ❌ 不好 - 逻辑耦合在组件中
const sendMessage = async () => {
  // ... 110 行 SSE 处理逻辑
  const response = await fetch('/api/chat/generate-crew-stream', ...)
  const reader = response.body?.getReader()
  while (true) {
    const { done, value } = await reader.read()
    // ... 解析 SSE 事件
  }
}
```

**解决方案：** 提取为 `composables/useSSEStream.ts`

```typescript
// ✅ 好 - 逻辑复用
export function useSSEStream() {
  const connect = async (url: string, onMessage: (data: any) => void) => {
    const response = await fetch(url, ...)
    const reader = response.body?.getReader()
    // ... SSE 处理逻辑
  }
  return { connect }
}

// Chat.vue 中使用
const { connect } = useSSEStream()
const sendMessage = async () => {
  await connect('/api/chat/generate-crew-stream', (data) => {
    if (data.type === 'log') {
      logMessage.text += data.message
    }
  })
}
```

---

### 2. **LLMSettings.vue** - 重复表单代码

**问题：** 每个 Provider 都有相同的表单结构（80-150 行 × 3 个 Provider）

```vue
<!-- ❌ 不好 - 重复 3 次 -->
<div class="provider-card">
  <h2>DashScope</h2>
  <input v-model="settings.dashscope.api_key" type="password" />
  <input v-model="settings.dashscope.base_url" />
  <select v-model="settings.dashscope.default_model">...</select>
</div>

<div class="provider-card">
  <h2>OpenAI</h2>
  <input v-model="settings.openai.api_key" type="password" />
  <input v-model="settings.openai.base_url" />
  <select v-model="settings.openai.default_model">...</select>
</div>
```

**解决方案：** 提取为 `ProviderConfigCard.vue` 组件

```vue
<!-- ✅ 好 - 组件复用 -->
<ProviderConfigCard
  v-for="provider in providers"
  :key="provider.name"
  :provider="provider"
  :settings="settings[provider.name]"
  @update="updateProvider"
  @test="testConnection"
/>
```

---

### 3. **Preferences.vue** - 状态管理过多

**问题：** 15+ 个 ref 状态，职责不清晰

```typescript
// ❌ 不好 - 状态分散
const proposals = ref([])
const loading = ref(false)
const showDetail = ref(false)
const currentProposal = ref(null)
const loadingDetail = ref(false)
const diffLines = ref([])
const diffStats = ref({})
const merging = ref(false)
const rejecting = ref(false)
const showRejectDialog = ref(false)
const rejectReason = ref('')
const currentRejectExecId = ref('')
const showCurrent = ref(false)
const currentPrefContent = ref('')
const currentPrefPath = ref('')
const loadingCurrent = ref('')
```

**解决方案：** 拆分为 composables

```typescript
// ✅ 好 - 逻辑分组
// composables/useProposalList.ts
export function useProposalList() {
  const proposals = ref([])
  const loading = ref(false)
  const loadProposals = async () => { ... }
  return { proposals, loading, loadProposals }
}

// composables/useProposalDetail.ts
export function useProposalDetail() {
  const currentProposal = ref(null)
  const diffLines = ref([])
  const loadDetail = async (execId) => { ... }
  return { currentProposal, diffLines, loadDetail }
}

// composables/useProposalActions.ts
export function useProposalActions() {
  const merging = ref(false)
  const merge = async (execId) => { ... }
  const reject = async (execId, reason) => { ... }
  return { merging, merge, reject }
}
```

---

### 4. **表单逻辑重复** - Agents/Tasks/Crews

**问题：** 每个 CRUD 页面都有相同的表单逻辑

```vue
<!-- ❌ 不好 - 每个页面重复 -->
<!-- Agents.vue -->
const showDialog = ref(false)
const form = ref({ name: '', role: '', ... })
const handleCreate = () => { showDialog.value = true }
const handleSave = async () => { await api.agents.create(form.value) }

<!-- Tasks.vue -->
const showDialog = ref(false)
const form = ref({ name: '', description: '', ... })
const handleCreate = () => { showDialog.value = true }
const handleSave = async () => { await api.tasks.create(form.value) }
```

**解决方案：** 提取为通用 composable

```typescript
// ✅ 好 - 逻辑复用
// composables/useCRUDDialog.ts
export function useCRUDDialog<T>(api: any) {
  const showDialog = ref(false)
  const form = ref<T>({} as T)
  const saving = ref(false)
  
  const openCreate = () => {
    form.value = {} as T
    showDialog.value = true
  }
  
  const save = async () => {
    saving.value = true
    try {
      await api.create(form.value)
      showDialog.value = false
    } finally {
      saving.value = false
    }
  }
  
  return { showDialog, form, saving, openCreate, save }
}

// 使用
const { showDialog, form, save } = useCRUDDialog(api.agents)
```

---

## 重构优先级

### 🔴 高优先级（立即重构）

#### 1. 提取 SSE 流式处理 composable

**文件：** `composables/useSSEStream.ts`

**收益：**
- Chat.vue 减少 110 行
- 可复用于其他流式场景

**工作量：** 1-2 小时

---

#### 2. 提取 Provider 配置卡片组件

**文件：** `components/settings/ProviderConfigCard.vue`

**收益：**
- LLMSettings.vue 减少 300+ 行
- 新增 Provider 只需配置数据

**工作量：** 2-3 小时

---

#### 3. 拆分 Preferences.vue 为 composables

**文件：**
- `composables/useProposalList.ts`
- `composables/useProposalDetail.ts`
- `composables/useProposalActions.ts`

**收益：**
- Preferences.vue 减少 200+ 行
- 逻辑清晰，易于测试

**工作量：** 3-4 小时

---

### 🟡 中优先级（逐步优化）

#### 4. 提取通用 CRUD Dialog composable

**文件：** `composables/useCRUDDialog.ts`

**收益：**
- Agents/Tasks/Crews 各减少 50+ 行
- 统一表单处理逻辑

**工作量：** 2-3 小时

---

#### 5. 提取通用表单组件

**文件：**
- `components/common/FormField.vue`
- `components/common/FormDialog.vue`

**收益：**
- 统一表单样式
- 减少重复代码

**工作量：** 3-4 小时

---

### 🟢 低优先级（可选优化）

#### 6. 优化 DiffViewer 组件

**当前：** 250 行，包含 diff 算法和渲染

**优化：** 拆分为 `useDiffParser.ts` + `DiffViewer.vue`

**工作量：** 2 小时

---

## 重构原则

### ✅ 遵循的原则

1. **组件化** - 重复的 UI 提取为组件
2. **逻辑复用** - 重复的逻辑提取为 composables
3. **功能内聚** - 相关功能放在一起
4. **单一职责** - 每个组件/composable 只做一件事

### ❌ 避免的陷阱

1. **过度抽象** - 不要为了复用而复用
2. **过早优化** - 只重构明显重复的代码
3. **过度设计** - 保持简单，不引入复杂架构

---

## 重构后预期

### 代码量对比

| 文件 | 重构前 | 重构后 | 缩减率 |
|-----|-------|-------|--------|
| Chat.vue | 436 行 | ~300 行 | -31% |
| LLMSettings.vue | 491 行 | ~150 行 | -69% |
| Preferences.vue | 504 行 | ~250 行 | -50% |
| **总计** | 4202 行 | ~3500 行 | -17% |

### 新增文件

**Composables (6 个):**
- `useSSEStream.ts` (~80 行)
- `useProposalList.ts` (~60 行)
- `useProposalDetail.ts` (~70 行)
- `useProposalActions.ts` (~50 行)
- `useCRUDDialog.ts` (~80 行)
- `useDiffParser.ts` (~60 行)

**Components (2 个):**
- `ProviderConfigCard.vue` (~150 行)
- `FormDialog.vue` (~100 行)

**新增代码：** ~650 行  
**净减少：** 4202 - 3500 - 650 = **52 行**

虽然净减少不多，但：
- ✅ 代码复用性提升
- ✅ 可维护性提升
- ✅ 可测试性提升
- ✅ 新功能开发更快

---

## 实施步骤

### Phase 1: 提取 Composables（1 周）

1. `useSSEStream.ts` - SSE 流式处理
2. `useProposalList.ts` - 提案列表管理
3. `useProposalDetail.ts` - 提案详情管理
4. `useProposalActions.ts` - 提案操作（merge/reject）
5. `useCRUDDialog.ts` - 通用 CRUD 对话框

### Phase 2: 提取 Components（1 周）

1. `ProviderConfigCard.vue` - Provider 配置卡片
2. `FormDialog.vue` - 通用表单对话框

### Phase 3: 重构现有页面（1 周）

1. 重构 `Chat.vue` 使用 `useSSEStream`
2. 重构 `LLMSettings.vue` 使用 `ProviderConfigCard`
3. 重构 `Preferences.vue` 使用提案相关 composables
4. 重构 `Agents/Tasks/Crews.vue` 使用 `useCRUDDialog`

### Phase 4: 测试验证（3 天）

1. 功能测试 - 确保所有功能正常
2. 回归测试 - 确保没有引入 bug
3. 性能测试 - 确保性能没有退化

---

## 验收标准

### 代码质量

- [ ] 单个 .vue 文件 < 300 行
- [ ] 单个 composable < 100 行
- [ ] 无重复代码（DRY 原则）
- [ ] 每个函数职责单一

### 功能完整性

- [ ] 所有现有功能正常工作
- [ ] 无新增 bug
- [ ] 用户体验无变化

### 可维护性

- [ ] 代码结构清晰
- [ ] 易于添加新功能
- [ ] 易于修改现有功能

---

## 后续优化建议

1. **TypeScript 类型优化** - 补充完整的类型定义
2. **单元测试** - 为 composables 添加单元测试
3. **E2E 测试** - 为关键流程添加端到端测试
4. **性能优化** - 使用虚拟滚动优化长列表
5. **状态管理** - 考虑引入 Pinia（如果状态复杂度继续增加）

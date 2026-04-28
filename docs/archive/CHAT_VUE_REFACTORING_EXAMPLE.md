# Chat.vue 重构示例

## 重构前（436 行）

```vue
<script setup lang="ts">
// ... 100+ 行 SSE 处理逻辑
const sendMessage = async () => {
  if (!userInput.value.trim() || loading.value) return

  const userMessage = userInput.value.trim()
  messages.value.push({ role: 'user', text: userMessage })
  userInput.value = ''
  scrollToBottom()

  const logMessage = {
    role: 'assistant' as const,
    text: '🤖 后台正在生成 Crew，请稍候...\n\n',
    isGenerating: true
  }
  messages.value.push(logMessage)
  scrollToBottom()

  ElMessage.info({ message: '已提交生成任务，正在后台处理...', duration: 3000 })

  try {
    // ❌ 110 行 SSE 处理逻辑
    const response = await fetch('/api/chat/generate-crew-stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scenario: userMessage,
        context: '',
        doc_filename: selectedDoc.value || null
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()

    if (!reader) {
      throw new Error('No response body')
    }

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6))

          if (data.type === 'log') {
            logMessage.text += `[${data.level}] ${data.message}\n`
            scrollToBottom()
          } else if (data.type === 'complete') {
            logMessage.isGenerating = false
            messages.value.pop()
            messages.value.push({
              role: 'assistant',
              text: '',
              result: data.result
            })
            ElNotification.success({
              title: '✅ Crew 创建成功',
              message: data.result.summary,
              duration: 5000,
              position: 'top-right'
            })
            scrollToBottom()
          } else if (data.type === 'error') {
            logMessage.isGenerating = false
            logMessage.text += `\n❌ 错误：${data.message}`
            ElNotification.error({
              title: '❌ 生成失败',
              message: data.message,
              duration: 5000,
              position: 'top-right'
            })
            scrollToBottom()
          }
        }
      }
    }
  } catch (error) {
    logMessage.isGenerating = false
    logMessage.text += `\n❌ 连接失败：${(error as any).message}`
    ElNotification.error({
      title: '❌ 请求失败',
      message: (error as any).message,
      duration: 5000,
      position: 'top-right'
    })
    scrollToBottom()
  } finally {
    loading.value = false
  }
}
</script>
```

---

## 重构后（~300 行）

```vue
<script setup lang="ts">
import { useSSEStream } from '@/composables/useSSEStream'

// ✅ 使用 composable
const { connect } = useSSEStream()

const sendMessage = async () => {
  if (!userInput.value.trim() || loading.value) return

  const userMessage = userInput.value.trim()
  messages.value.push({ role: 'user', text: userMessage })
  userInput.value = ''
  scrollToBottom()

  // 添加日志消息容器
  const logMessage = {
    role: 'assistant' as const,
    text: '🤖 后台正在生成 Crew，请稍候...\n\n',
    isGenerating: true
  }
  messages.value.push(logMessage)
  scrollToBottom()

  ElMessage.info({ message: '已提交生成任务，正在后台处理...', duration: 3000 })

  try {
    // ✅ 只需 20 行，逻辑清晰
    await connect(
      '/api/chat/generate-crew-stream',
      {
        scenario: userMessage,
        context: '',
        doc_filename: selectedDoc.value || null
      },
      {
        onMessage: (data) => {
          logMessage.text += `[${data.level}] ${data.message}\n`
          scrollToBottom()
        },
        onComplete: (data) => {
          logMessage.isGenerating = false
          messages.value.pop()
          messages.value.push({
            role: 'assistant',
            text: '',
            result: data.result
          })
          ElNotification.success({
            title: '✅ Crew 创建成功',
            message: data.result.summary,
            duration: 5000,
            position: 'top-right'
          })
          scrollToBottom()
        },
        onError: (data) => {
          logMessage.isGenerating = false
          logMessage.text += `\n❌ 错误：${data.message}`
          ElNotification.error({
            title: '❌ 生成失败',
            message: data.message,
            duration: 5000,
            position: 'top-right'
          })
          scrollToBottom()
        }
      }
    )
  } catch (error) {
    // 已在 composable 中处理
  } finally {
    loading.value = false
  }
}
</script>
```

---

## 收益

### 代码量

- **重构前：** 436 行
- **重构后：** ~300 行
- **减少：** 136 行（-31%）

### 可维护性

- ✅ SSE 逻辑独立，易于测试
- ✅ 可复用于其他流式场景
- ✅ Chat.vue 专注于 UI 逻辑

### 可测试性

```typescript
// composables/useSSEStream.test.ts
import { describe, it, expect } from 'vitest'
import { useSSEStream } from './useSSEStream'

describe('useSSEStream', () => {
  it('should parse SSE messages correctly', async () => {
    const { connect } = useSSEStream()
    const messages: any[] = []
    
    await connect('/test', {}, {
      onMessage: (data) => messages.push(data)
    })
    
    expect(messages).toHaveLength(3)
  })
})
```

---

## 类似重构

### LLMSettings.vue - 提取 ProviderConfigCard

**重构前：** 491 行，重复 3 次表单代码

**重构后：** ~150 行

```vue
<!-- ProviderConfigCard.vue -->
<template>
  <div class="provider-card">
    <div class="provider-header">
      <h2>{{ provider.display_name }}</h2>
      <span :class="['status-badge', provider.is_configured ? 'configured' : 'not-configured']">
        {{ provider.is_configured ? '已配置' : '未配置' }}
      </span>
    </div>

    <div class="form-group">
      <label>API Key</label>
      <input v-model="localSettings.api_key" type="password" />
    </div>

    <div class="form-group">
      <label>Base URL</label>
      <input v-model="localSettings.base_url" />
    </div>

    <div class="form-row">
      <div class="form-group">
        <label>默认模型</label>
        <select v-model="localSettings.default_model">
          <option v-for="model in provider.available_models" :key="model" :value="model">
            {{ model }}
          </option>
        </select>
      </div>

      <div class="form-group">
        <label>Temperature</label>
        <input v-model.number="localSettings.temperature" type="number" min="0" max="2" step="0.1" />
      </div>
    </div>

    <button @click="$emit('test')" :disabled="testing">
      {{ testing ? '测试中...' : '测试连接' }}
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  provider: Provider
  settings: ProviderSettings
  testing: boolean
}>()

defineEmits<{
  test: []
  update: [settings: ProviderSettings]
}>()
</script>
```

**使用：**

```vue
<!-- LLMSettings.vue -->
<template>
  <div class="providers-config">
    <ProviderConfigCard
      v-for="provider in providers"
      :key="provider.name"
      :provider="provider"
      :settings="settings[provider.name]"
      :testing="testing[provider.name]"
      @test="testConnection(provider.name)"
      @update="updateProvider(provider.name, $event)"
    />
  </div>
</template>
```

**收益：** 491 行 → 150 行（-69%）

---

## 总结

### 重构原则

1. **提取重复逻辑** → Composables
2. **提取重复 UI** → Components
3. **保持简单** → 不过度设计

### 优先级

1. 🔴 **useSSEStream** - 立即重构（收益最大）
2. 🔴 **ProviderConfigCard** - 立即重构（减少最多代码）
3. 🟡 **Preferences composables** - 逐步优化
4. 🟢 **useCRUDDialog** - 可选优化

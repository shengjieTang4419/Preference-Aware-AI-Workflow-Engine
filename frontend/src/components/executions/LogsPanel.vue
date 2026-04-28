<template>
  <div>
    <div style="margin-bottom: 10px;">
      <el-button size="small" @click="refresh" :loading="loading">刷新</el-button>
    </div>
    <div v-loading="loading" style="height: 60vh; overflow-y: auto;">
      <pre style="background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 4px; font-size: 12px; line-height: 1.5;">{{ logs }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const props = defineProps<{
  executionId: string
}>()

const loading = ref(false)
const logs = ref('')

const refresh = async () => {
  if (!props.executionId) return
  loading.value = true
  try {
    const result: any = await api.executions.getLogs(props.executionId)
    const logContent = typeof result === 'object' ? result.content : result
    logs.value = logContent || '暂无日志'
  } catch {
    ElMessage.error('加载日志失败')
  } finally {
    loading.value = false
  }
}

watch(
  () => props.executionId,
  (id) => {
    if (id) refresh()
  },
  { immediate: true },
)

defineExpose({ refresh })
</script>

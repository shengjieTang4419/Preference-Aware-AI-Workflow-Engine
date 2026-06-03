<template>
  <div class="pipeline-progress-page">
    <!-- Header -->
    <div class="progress-header">
      <el-button link @click="goBack" class="back-btn">
        <el-icon><ArrowLeft /></el-icon>
        <span>返回创意工坊</span>
      </el-button>
      <h2 class="page-title">🚀 任务执行中</h2>
      <p class="page-subtitle">{{ scenario }}</p>
    </div>

    <!-- Progress steps -->
    <div class="steps-container">
      <div
        v-for="(step, idx) in steps"
        :key="idx"
        class="step-item"
        :class="step.status"
      >
        <div class="step-icon">
          <span v-if="step.status === 'success'">✅</span>
          <span v-else-if="step.status === 'running'" class="spinner-sm">⏳</span>
          <span v-else-if="step.status === 'error'">❌</span>
          <span v-else class="step-pending">{{ idx + 1 }}</span>
        </div>
        <div class="step-content">
          <div class="step-name">{{ step.name }}</div>
          <div v-if="step.message" class="step-message">{{ step.message }}</div>
        </div>
        <div v-if="step.status === 'running'" class="step-progress">
          <el-progress :percentage="percentage" :stroke-width="4" :show-text="false" />
        </div>
      </div>
    </div>

    <!-- Overall progress -->
    <div class="overall-bar">
      <el-progress
        :percentage="percentage"
        :stroke-width="8"
        :status="overallProgressStatus"
      />
      <span class="progress-text">{{ currentStep }} / {{ totalSteps }}</span>
    </div>

    <!-- Result -->
    <div v-if="result" class="result-card">
      <h3>✅ Pipeline 完成</h3>
      <pre class="result-text">{{ JSON.stringify(result, null, 2) }}</pre>
      <el-button type="primary" @click="viewFlow">查看执行流程</el-button>
    </div>

    <!-- Error -->
    <div v-if="errorMsg" class="error-card">
      <h3>❌ 执行失败</h3>
      <p>{{ errorMsg }}</p>
      <el-button @click="goBack">返回重试</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const executionId = computed(() => route.params.id as string)
const scenario = ref('')
const currentStep = ref(0)
const totalSteps = ref(9)
const result = ref<any>(null)
const errorMsg = ref('')
let ws: WebSocket | null = null

interface StepInfo {
  name: string
  status: 'pending' | 'running' | 'success' | 'error'
  message: string
}

const steps = ref<StepInfo[]>([
  { name: '生成项目主题', status: 'pending', message: '' },
  { name: '规划任务', status: 'pending', message: '' },
  { name: '匹配/创建 Agent', status: 'pending', message: '' },
  { name: '创建 Crew', status: 'pending', message: '' },
  { name: '创建 Tasks', status: 'pending', message: '' },
  { name: '分配模型', status: 'pending', message: '' },
  { name: '验证配置', status: 'pending', message: '' },
  { name: '运行 Crew', status: 'pending', message: '' },
  { name: '生成制品', status: 'pending', message: '' },
])

const percentage = computed(() => {
  if (totalSteps.value === 0) return 0
  return Math.round((currentStep.value / totalSteps.value) * 100)
})

const overallProgressStatus = computed(() => {
  if (errorMsg.value) return 'exception'
  if (result.value) return 'success'
  return ''
})

function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/api/chat/ws/${executionId.value}`
  ws = new WebSocket(wsUrl)

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)

    if (data.type === 'progress') {
      const stepIdx = (data.step || 1) - 1
      if (stepIdx >= 0 && stepIdx < steps.value.length) {
        steps.value[stepIdx].status = data.status || 'running'
        steps.value[stepIdx].message = data.message || ''
        currentStep.value = data.step || currentStep.value
        totalSteps.value = data.total || totalSteps.value
      }
      // Mark previous steps as success
      for (let i = 0; i < stepIdx; i++) {
        if (steps.value[i].status !== 'success') {
          steps.value[i].status = 'success'
        }
      }
    } else if (data.type === 'complete') {
      result.value = data.result
      steps.value.forEach(s => {
        if (s.status === 'running') s.status = 'success'
      })
      currentStep.value = totalSteps.value
      ws?.close()
    } else if (data.type === 'error') {
      errorMsg.value = data.message || '未知错误'
      steps.value.forEach(s => {
        if (s.status === 'running') s.status = 'error'
      })
      ws?.close()
    }
  }

  ws.onerror = () => {
    errorMsg.value = 'WebSocket 连接失败'
  }

  ws.onclose = () => {
    // If no result and no error, try polling
    if (!result.value && !errorMsg.value) {
      setTimeout(connectWebSocket, 3000)
    }
  }
}

function viewFlow() {
  router.push(`/flow/${executionId.value}`)
}

function goBack() {
  router.push('/')
}

onMounted(() => {
  connectWebSocket()
})

onUnmounted(() => {
  ws?.close()
})
</script>

<style scoped>
.pipeline-progress-page {
  max-width: 700px;
  margin: 0 auto;
  padding: 24px;
}

.progress-header {
  text-align: center;
  margin-bottom: 32px;
}

.back-btn {
  color: #909399;
  margin-bottom: 12px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
  margin: 0 0 8px;
}

.page-subtitle {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.steps-container {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  margin-bottom: 24px;
}

.step-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.step-item:last-child {
  border-bottom: none;
}

.step-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 16px;
}

.step-pending {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #e4e7ed;
  color: #909399;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

.step-content {
  flex: 1;
  min-width: 0;
}

.step-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.step-message {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.step-item.running .step-name {
  color: #409eff;
  font-weight: 600;
}

.step-item.success .step-name {
  color: #67c23a;
}

.step-item.error .step-name {
  color: #f56c6c;
}

.step-progress {
  width: 80px;
  flex-shrink: 0;
}

.spinner-sm {
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.overall-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  background: #fff;
  border-radius: 12px;
  padding: 16px 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  margin-bottom: 24px;
}

.overall-bar :deep(.el-progress) {
  flex: 1;
}

.progress-text {
  font-size: 14px;
  font-weight: 600;
  color: #606266;
  white-space: nowrap;
}

.result-card {
  background: #f0f9eb;
  border: 1px solid #c2e7b0;
  border-radius: 12px;
  padding: 24px;
}

.result-card h3 {
  margin: 0 0 12px;
  color: #67c23a;
}

.result-text {
  font-size: 12px;
  color: #606266;
  background: #fff;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  max-height: 200px;
  margin-bottom: 16px;
}

.error-card {
  background: #fef0f0;
  border: 1px solid #fbc4c4;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
}

.error-card h3 {
  margin: 0 0 8px;
  color: #f56c6c;
}

.error-card p {
  color: #606266;
  margin-bottom: 16px;
}
</style>

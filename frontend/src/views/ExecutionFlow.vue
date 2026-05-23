<template>
  <div class="execution-flow-page">
    <!-- Header -->
    <div class="flow-header">
      <div class="header-left">
        <el-button link @click="goBack" class="back-btn">
          <el-icon><ArrowLeft /></el-icon>
          <span>返回创意工坊</span>
        </el-button>
        <h2 class="page-title">🚀 执行流程图</h2>
        <p class="page-subtitle" v-if="flowData">
          Crew: {{ flowData.crew.name }} · 任务ID: {{ flowData.execution.id }}
        </p>
      </div>
      <div class="header-right">
        <el-tag :type="overallStatusType" size="large" effect="dark">
          {{ overallStatusText }}
        </el-tag>
        <el-button
          v-if="flowData"
          size="small"
          :loading="refreshing"
          @click="fetchData"
          circle
        >
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>加载流程数据...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="error-container">
      <el-icon size="48" color="#f56c6c"><CircleCloseFilled /></el-icon>
      <p>{{ error }}</p>
      <el-button type="primary" @click="fetchData">重试</el-button>
    </div>

    <!-- Main content -->
    <template v-else-if="flowData">
      <!-- Stats bar -->
      <div class="stats-bar">
        <div class="stat-item">
          <span class="stat-icon">📊</span>
          <span class="stat-label">执行模式</span>
          <span class="stat-value">{{ flowData.crew.process_type === 'sequential' ? '顺序执行' : '层级执行' }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-icon">🤖</span>
          <span class="stat-label">智能体数</span>
          <span class="stat-value">{{ flowData.agents.length }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-icon">📋</span>
          <span class="stat-label">任务数</span>
          <span class="stat-value">{{ flowData.tasks.length }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-icon">🔗</span>
          <span class="stat-label">依赖关系</span>
          <span class="stat-value">{{ flowData.edges.length }}</span>
        </div>
        <div class="stat-item" v-if="executionDuration">
          <span class="stat-icon">⏱️</span>
          <span class="stat-label">总耗时</span>
          <span class="stat-value">{{ executionDuration }}</span>
        </div>
      </div>

      <!-- Flow graph area with sidebar -->
      <div class="flow-main-area">
        <div class="flow-canvas-container">
          <FlowCanvas
            :flowData="flowData"
            :selectedTaskId="selectedTaskId"
            @select="handleSelectTask"
          />
        </div>
        <FlowSidebar
          :selectedTask="selectedTask"
          @close="selectedTaskId = null"
        />
      </div>

      <!-- Agents legend -->
      <div class="agents-legend">
        <h3 class="section-title">🤖 智能体团队</h3>
        <div class="legend-grid">
          <div
            v-for="agent in flowData.agents"
            :key="agent.id"
            class="legend-card"
            @click="highlightAgentTasks(agent.id)"
          >
            <div class="legend-avatar">
              {{ agent.name.charAt(0) }}
            </div>
            <div class="legend-info">
              <div class="legend-name">{{ agent.name }}</div>
              <div class="legend-role">{{ agent.role }}</div>
            </div>
            <el-tag
              :type="agentTierType(agent.model_tier)"
              size="small"
              effect="plain"
            >
              {{ agentTierLabel(agent.model_tier) }}
            </el-tag>
          </div>
        </div>
      </div>

      <!-- Bottom actions -->
      <div class="bottom-actions">
        <el-button type="primary" size="large" @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回创意工坊
        </el-button>
        <el-button size="large" @click="fetchData" :loading="refreshing">
          <el-icon><Refresh /></el-icon>
          刷新状态
        </el-button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/api'
import type { FlowData, FlowTask } from '@/api'
import FlowCanvas from '@/components/flow/FlowCanvas.vue'
import FlowSidebar from '@/components/flow/FlowSidebar.vue'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const refreshing = ref(false)
const error = ref('')
const flowData = ref<FlowData | null>(null)
const selectedTaskId = ref<string | null>(null)
let pollTimer: ReturnType<typeof setInterval> | null = null

const executionId = computed(() => route.params.id as string)

const selectedTask = computed<FlowTask | null>(() => {
  if (!flowData.value || !selectedTaskId.value) return null
  return flowData.value.tasks.find(t => t.id === selectedTaskId.value) || null
})

const overallStatusType = computed(() => {
  if (!flowData.value) return 'info'
  const map: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = {
    completed: 'success',
    running: 'warning',
    pending: 'info',
    failed: 'danger',
  }
  return map[flowData.value.execution.status] || 'info'
})

const overallStatusText = computed(() => {
  if (!flowData.value) return '加载中'
  const map: Record<string, string> = {
    completed: '已完成',
    running: '执行中',
    pending: '等待中',
    failed: '失败',
  }
  return map[flowData.value.execution.status] || flowData.value.execution.status
})

const executionDuration = computed(() => {
  if (!flowData.value) return ''
  const { created_at, completed_at } = flowData.value.execution
  if (!created_at || !completed_at) return ''
  const start = new Date(created_at).getTime()
  const end = new Date(completed_at).getTime()
  const diff = Math.round((end - start) / 1000)
  if (diff < 60) return `${diff} 秒`
  const mins = Math.floor(diff / 60)
  const secs = diff % 60
  return `${mins} 分 ${secs} 秒`
})

function handleSelectTask(id: string) {
  selectedTaskId.value = selectedTaskId.value === id ? null : id
}

function highlightAgentTasks(agentId: string) {
  if (!flowData.value) return
  const agent = flowData.value.agents.find(a => a.id === agentId)
  if (agent && agent.assigned_tasks.length > 0) {
    selectedTaskId.value = agent.assigned_tasks[0]
  }
}

function agentTierType(tier: string): '' | 'success' | 'warning' | 'info' | 'danger' {
  const map: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = {
    advanced: 'warning',
    standard: '',
    basic: 'success',
  }
  return map[tier] || 'success'
}

function agentTierLabel(tier: string): string {
  const map: Record<string, string> = {
    advanced: '🚀 高级',
    standard: '⚡ 标准',
    basic: '📦 基础',
  }
  return map[tier] || '📦 基础'
}

function goBack() {
  router.push('/')
}

async function fetchData() {
  try {
    if (!loading.value) refreshing.value = true
    const data = await api.executions.getFlow(executionId.value)
    flowData.value = data
    error.value = ''

    // Poll if running
    if (data.execution.status === 'running' || data.execution.status === 'pending') {
      startPolling()
    } else {
      stopPolling()
    }
  } catch (err: any) {
    if (err?.response?.status === 404) {
      error.value = '找不到该执行记录'
    } else {
      error.value = '加载失败，请重试'
    }
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(() => fetchData(), 5000)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

onMounted(() => fetchData())
onUnmounted(() => stopPolling())
</script>

<style scoped>
.execution-flow-page {
  max-width: 1400px;
  margin: 0 auto;
  padding-bottom: 40px;
}

/* Header */
.flow-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  margin-bottom: 20px;
  color: #fff;
}

.header-left {
  flex: 1;
}

.back-btn {
  color: rgba(255, 255, 255, 0.85) !important;
  margin-bottom: 8px;
  font-size: 14px;
}

.back-btn:hover {
  color: #fff !important;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 4px;
}

.page-subtitle {
  font-size: 13px;
  opacity: 0.8;
  margin: 0;
  font-family: monospace;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* Loading and error */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: #909399;
}

.loading-container p {
  margin-top: 16px;
  font-size: 14px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e4e7ed;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: #606266;
}

.error-container p {
  margin: 16px 0;
  font-size: 14px;
}

/* Stats bar */
.stats-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.04);
  flex: 1;
  min-width: 140px;
}

.stat-icon {
  font-size: 18px;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-left: auto;
}

/* Flow main area */
.flow-main-area {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  min-height: 300px;
}

.flow-canvas-container {
  flex: 1;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

/* Agents legend */
.agents-legend {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 16px;
}

.legend-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.legend-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: #f9fafb;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.legend-card:hover {
  background: #ecf5ff;
  border-color: #b3d8ff;
}

.legend-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 16px;
  flex-shrink: 0;
}

.legend-info {
  flex: 1;
  min-width: 0;
}

.legend-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.legend-role {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

/* Bottom actions */
.bottom-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding: 24px 0;
}

/* Responsive */
@media (max-width: 768px) {
  .flow-header {
    flex-direction: column;
    gap: 12px;
  }

  .stats-bar {
    flex-direction: column;
  }

  .flow-main-area {
    flex-direction: column;
  }

  .legend-grid {
    grid-template-columns: 1fr;
  }

  .bottom-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>

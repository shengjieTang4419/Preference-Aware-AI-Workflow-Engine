<template>
  <div class="flow-sidebar" :class="{ open: !!selectedTask }">
    <!-- No selection state -->
    <div v-if="!selectedTask" class="sidebar-empty">
      <div class="empty-icon">👆</div>
      <p class="empty-text">点击任务节点查看详情</p>
    </div>

    <!-- Task detail -->
    <div v-else class="sidebar-content">
      <!-- Header -->
      <div class="sidebar-header">
        <div class="header-top">
          <span class="status-dot" :class="selectedTask.status"></span>
          <h3 class="task-name">{{ selectedTask.name }}</h3>
          <el-button link @click="$emit('close')" class="close-btn">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
        <el-tag :type="statusTagType" size="small" effect="dark">
          {{ statusText }}
        </el-tag>
      </div>

      <!-- Agent info -->
      <div class="detail-section">
        <h4 class="section-label">👤 智能体信息</h4>
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">名称</span>
            <span class="info-value">{{ selectedTask.agent_name }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">角色</span>
            <span class="info-value">{{ selectedTask.agent_role || selectedTask.agent_name }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">模型等级</span>
            <el-tag :type="tierTagType" size="small">
              {{ tierLabel }}
            </el-tag>
          </div>
        </div>
      </div>

      <!-- Agent goal -->
      <div v-if="selectedTask.agent_goal" class="detail-section">
        <h4 class="section-label">🎯 目标</h4>
        <p class="detail-text">{{ selectedTask.agent_goal }}</p>
      </div>

      <!-- Agent backstory -->
      <div v-if="selectedTask.agent_backstory" class="detail-section">
        <h4 class="section-label">📖 背景</h4>
        <p class="detail-text">{{ selectedTask.agent_backstory }}</p>
      </div>

      <!-- Task description -->
      <div class="detail-section">
        <h4 class="section-label">📋 任务描述</h4>
        <p class="detail-text">{{ selectedTask.description }}</p>
      </div>

      <!-- Expected output -->
      <div class="detail-section">
        <h4 class="section-label">📤 预期输出</h4>
        <p class="detail-text">{{ selectedTask.expected_output }}</p>
      </div>

      <!-- Dependencies -->
      <div v-if="selectedTask.context_task_ids.length > 0" class="detail-section">
        <h4 class="section-label">🔗 依赖任务</h4>
        <div class="dep-list">
          <el-tag
            v-for="depId in selectedTask.context_task_ids"
            :key="depId"
            size="small"
            type="info"
            class="dep-tag"
          >
            {{ depId }}
          </el-tag>
        </div>
      </div>

      <!-- Execution config -->
      <div class="detail-section">
        <h4 class="section-label">⚙️ 执行配置</h4>
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">异步执行</span>
            <span class="info-value">{{ selectedTask.async_execution ? '是' : '否' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">执行顺序</span>
            <span class="info-value">#{{ selectedTask.index + 1 }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { FlowTask } from '@/api'

const props = defineProps<{
  selectedTask: FlowTask | null
}>()

defineEmits<{
  close: []
}>()

const statusTagType = computed(() => {
  if (!props.selectedTask) return 'info'
  const map: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = {
    completed: 'success',
    running: 'warning',
    pending: 'info',
    failed: 'danger',
  }
  return map[props.selectedTask.status] || 'info'
})

const statusText = computed(() => {
  if (!props.selectedTask) return ''
  const map: Record<string, string> = {
    completed: '已完成',
    running: '执行中',
    pending: '等待中',
    failed: '失败',
  }
  return map[props.selectedTask.status] || props.selectedTask.status
})

const tierTagType = computed(() => {
  if (!props.selectedTask) return 'info'
  const map: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = {
    advanced: 'warning',
    standard: '',
    basic: 'success',
  }
  return map[props.selectedTask.model_tier] || 'success'
})

const tierLabel = computed(() => {
  if (!props.selectedTask) return ''
  const map: Record<string, string> = {
    advanced: '🚀 高级模型',
    standard: '⚡ 标准模型',
    basic: '📦 基础模型',
  }
  return map[props.selectedTask.model_tier] || '📦 基础模型'
})
</script>

<style scoped>
.flow-sidebar {
  width: 0;
  min-width: 0;
  overflow: hidden;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.flow-sidebar.open {
  width: 360px;
  min-width: 360px;
}

.sidebar-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 40px 20px;
  color: #909399;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.6;
}

.empty-text {
  font-size: 14px;
  text-align: center;
}

.sidebar-content {
  padding: 0;
  height: 100%;
  overflow-y: auto;
}

.sidebar-header {
  padding: 20px 20px 16px;
  border-bottom: 1px solid #f0f0f0;
  background: linear-gradient(135deg, #f5f7fa 0%, #fff 100%);
  border-radius: 12px 12px 0 0;
}

.header-top {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-dot.completed { background: #67c23a; }
.status-dot.running { background: #409eff; animation: blink 1.5s infinite; }
.status-dot.pending { background: #c0c4cc; }
.status-dot.failed { background: #f56c6c; }

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.task-name {
  flex: 1;
  font-size: 17px;
  font-weight: 700;
  color: #303133;
  margin: 0;
}

.close-btn {
  color: #909399 !important;
  flex-shrink: 0;
}

.detail-section {
  padding: 16px 20px;
  border-bottom: 1px solid #f5f5f5;
}

.detail-section:last-child {
  border-bottom: none;
}

.section-label {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  margin: 0 0 10px;
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.info-label {
  font-size: 13px;
  color: #909399;
}

.info-value {
  font-size: 13px;
  color: #303133;
  font-weight: 500;
}

.detail-text {
  font-size: 13px;
  color: #606266;
  line-height: 1.7;
  margin: 0;
  word-break: break-all;
}

.dep-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.dep-tag {
  font-size: 12px;
}
</style>

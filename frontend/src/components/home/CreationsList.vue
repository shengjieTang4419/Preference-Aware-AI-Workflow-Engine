<template>
  <div class="section" v-if="creations.length > 0">
    <h2 class="section-title">📋 我的创作</h2>
    <div class="creations-list">
      <div
        v-for="creation in creations"
        :key="creation.id"
        class="creation-item"
      >
        <span class="creation-icon">{{ creation.scene_icon || '✨' }}</span>
        <div class="creation-info">
          <div class="creation-title">{{ creation.scene_title || '创意任务' }}</div>
          <div class="creation-text">{{ creation.input_text }}</div>
        </div>
        <div class="creation-meta">
          <el-tag :type="getStatusType(creation.status)" size="small">
            {{ getStatusText(creation.status) }}
          </el-tag>
          <span class="creation-time">{{ formatTime(creation.created_at) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Creation } from '@/api'

defineProps<{
  creations: Creation[]
}>()

function getStatusType(status: string) {
  const map: Record<string, 'success' | 'info' | 'warning' | 'danger'> = {
    success: 'success', running: 'warning', pending: 'info', failed: 'danger',
  }
  return map[status] || 'info'
}

function getStatusText(status: string) {
  const map: Record<string, string> = {
    success: '已完成', running: '进行中', pending: '等待中', failed: '失败',
  }
  return map[status] || status
}

function formatTime(time: string) {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  return `${date.getMonth() + 1}/${date.getDate()}`
}
</script>

<style scoped>
.section {
  margin-bottom: 30px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 16px;
}

.creations-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.creation-item {
  background: #fff;
  border-radius: 10px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.creation-icon {
  font-size: 28px;
  flex-shrink: 0;
}

.creation-info {
  flex: 1;
  min-width: 0;
}

.creation-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.creation-text {
  font-size: 13px;
  color: #909399;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
}

.creation-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  flex-shrink: 0;
}

.creation-time {
  font-size: 12px;
  color: #c0c4cc;
}
</style>

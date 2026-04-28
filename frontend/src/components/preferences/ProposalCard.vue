<template>
  <el-card class="proposal-card" :class="{ 'is-merged': merged, 'is-rejected': rejected }">
    <div class="proposal-header">
      <div class="proposal-info">
        <h4 class="proposal-title">
          <el-icon v-if="merged" color="#67c23a"><CircleCheck /></el-icon>
          <el-icon v-else-if="rejected" color="#f56c6c"><CircleClose /></el-icon>
          <el-icon v-else><Document /></el-icon>
          {{ proposal.exec_topic }}
        </h4>
        <p class="proposal-meta">
          <el-tag size="small" :type="statusType">{{ statusText }}</el-tag>
          <span class="meta-item">
            <el-icon><Clock /></el-icon>
            {{ formatDate(proposal.created_at) }}
          </span>
          <span class="meta-item">
            <el-icon><DocumentChecked /></el-icon>
            {{ proposal.suggestions_count }} 条建议
          </span>
        </p>
      </div>
      <div class="proposal-actions">
        <el-button
          v-if="!merged && !rejected"
          type="primary"
          size="small"
          @click="$emit('view', proposal.exec_id)"
        >
          <el-icon><View /></el-icon>
          查看 Diff
        </el-button>
        <el-tag v-else-if="merged" type="success">已合并</el-tag>
        <el-tag v-else-if="rejected" type="danger">已拒绝</el-tag>
      </div>
    </div>

    <div class="proposal-summary">
      <p class="summary-text">{{ proposal.diff_summary }}</p>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  Document,
  CircleCheck,
  CircleClose,
  Clock,
  DocumentChecked,
  View,
} from '@element-plus/icons-vue'
import type { PreferenceProposal } from '@/api'

interface Props {
  proposal: PreferenceProposal
}

const props = defineProps<Props>()

defineEmits<{
  view: [execId: string]
}>()

const merged = computed(() => props.proposal.status === 'merged')
const rejected = computed(() => props.proposal.status === 'rejected')

const statusType = computed(() => {
  const map: Record<string, string> = {
    pending: 'info',
    merged: 'success',
    rejected: 'danger',
  }
  return map[props.proposal.status] || 'info'
})

const statusText = computed(() => {
  const map: Record<string, string> = {
    pending: '待处理',
    merged: '已合并',
    rejected: '已拒绝',
  }
  return map[props.proposal.status] || '待处理'
})

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<style scoped>
.proposal-card {
  margin-bottom: 16px;
  transition: all 0.3s;
}

.proposal-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.proposal-card.is-merged {
  opacity: 0.7;
  border-color: #67c23a;
}

.proposal-card.is-rejected {
  opacity: 0.7;
  border-color: #f56c6c;
}

.proposal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.proposal-info {
  flex: 1;
}

.proposal-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 8px 0;
  font-size: 16px;
  color: #303133;
}

.proposal-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0;
  font-size: 13px;
  color: #606266;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.proposal-actions {
  flex-shrink: 0;
}

.proposal-summary {
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
}

.summary-text {
  margin: 0;
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>

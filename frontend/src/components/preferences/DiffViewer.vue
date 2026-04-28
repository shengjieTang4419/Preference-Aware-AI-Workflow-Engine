<template>
  <div class="diff-viewer">
    <div class="diff-header">
      <div class="diff-stats">
        <el-tag type="success">+ {{ stats.added }} 新增</el-tag>
        <el-tag type="danger">- {{ stats.removed }} 删除</el-tag>
        <el-tag>{{ stats.unchanged }} 未变更</el-tag>
      </div>
      <div class="diff-actions">
        <el-button type="primary" @click="$emit('merge')" :loading="merging">
          <el-icon><Check /></el-icon> 合并到 preferences.md
        </el-button>
        <el-button @click="$emit('reject')" :loading="rejecting">
          <el-icon><Close /></el-icon> 拒绝
        </el-button>
      </div>
    </div>

    <div class="diff-content">
      <div class="diff-side-by-side">
        <!-- 原始内容 -->
        <div class="diff-panel original">
          <div class="panel-header">
            <span class="panel-title">📄 原始 preferences.md</span>
            <span class="panel-badge">当前</span>
          </div>
          <div class="panel-content">
            <pre><code>{{ original }}</code></pre>
          </div>
        </div>

        <!-- 建议内容 -->
        <div class="diff-panel suggested">
          <div class="panel-header">
            <span class="panel-title">✨ 建议的 preferences.md</span>
            <span class="panel-badge suggested-badge">建议</span>
          </div>
          <div class="panel-content">
            <pre><code>{{ suggested }}</code></pre>
          </div>
        </div>
      </div>

      <!-- 或者行级 diff -->
      <div v-if="lines.length > 0" class="diff-lines">
        <div class="diff-line-header">
          <span>行级对比</span>
        </div>
        <div class="diff-lines-content">
          <div
            v-for="(line, index) in lines"
            :key="index"
            class="diff-line"
            :class="line.type"
          >
            <span class="line-number">{{ line.line_number }}</span>
            <span class="line-marker">
              {{ line.type === 'added' ? '+' : line.type === 'removed' ? '-' : ' ' }}
            </span>
            <span class="line-content">{{ line.content }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Check, Close } from '@element-plus/icons-vue'
import type { DiffLine } from '@/api'

interface Props {
  original: string
  suggested: string
  lines: DiffLine[]
  stats: {
    added: number
    removed: number
    unchanged: number
  }
  merging?: boolean
  rejecting?: boolean
}

defineProps<Props>()

defineEmits<{
  merge: []
  reject: []
}>()
</script>

<style scoped>
.diff-viewer {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.diff-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
}

.diff-stats {
  display: flex;
  gap: 8px;
}

.diff-actions {
  display: flex;
  gap: 12px;
}

.diff-content {
  flex: 1;
  overflow: auto;
  padding: 20px;
  background: #f5f7fa;
}

.diff-side-by-side {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.diff-panel {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e4e7ed;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}

.panel-title {
  font-weight: 500;
  color: #303133;
}

.panel-badge {
  padding: 2px 8px;
  font-size: 12px;
  background: #409eff;
  color: #fff;
  border-radius: 4px;
}

.suggested-badge {
  background: #67c23a;
}

.panel-content {
  max-height: 400px;
  overflow: auto;
  padding: 16px;
}

.panel-content pre {
  margin: 0;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #303133;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.diff-lines {
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  overflow: hidden;
}

.diff-line-header {
  padding: 12px 16px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
  font-weight: 500;
  color: #303133;
}

.diff-lines-content {
  max-height: 300px;
  overflow: auto;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.diff-line {
  display: flex;
  padding: 2px 16px;
  white-space: pre-wrap;
}

.diff-line.added {
  background: #f0f9eb;
}

.diff-line.added .line-marker {
  color: #67c23a;
  font-weight: bold;
}

.diff-line.removed {
  background: #fef0f0;
}

.diff-line.removed .line-marker {
  color: #f56c6c;
  font-weight: bold;
}

.diff-line.context {
  background: #fff;
}

.line-number {
  width: 40px;
  color: #909399;
  text-align: right;
  margin-right: 12px;
  flex-shrink: 0;
}

.line-marker {
  width: 20px;
  flex-shrink: 0;
}

.line-content {
  flex: 1;
  color: #303133;
}
</style>

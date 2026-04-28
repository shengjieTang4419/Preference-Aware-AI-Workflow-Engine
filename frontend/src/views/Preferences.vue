<template>
  <div class="preferences-page">
    <div class="page-header">
      <div class="header-left">
        <h2>🧬 偏好进化</h2>
        <p class="subtitle">
          每次 Crew 执行后，AI 会自动分析并生成改进建议。
          你可以像 Git Merge 一样审核并合并这些建议。
        </p>
      </div>
      <div class="header-right">
        <el-button @click="loadCurrentPreferences" :loading="loadingCurrent">
          <el-icon><Document /></el-icon>
          查看当前偏好
        </el-button>
        <el-button type="primary" @click="loadProposals" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新列表
        </el-button>
      </div>
    </div>

    <!-- 状态统计 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value">{{ pendingCount }}</div>
          <div class="stat-label">待处理</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card success">
          <div class="stat-value">{{ mergedCount }}</div>
          <div class="stat-label">已合并</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card danger">
          <div class="stat-value">{{ rejectedCount }}</div>
          <div class="stat-label">已拒绝</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card info">
          <div class="stat-value">{{ totalCount }}</div>
          <div class="stat-label">总计提案</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 提案列表 -->
    <el-card class="proposals-section">
      <template #header>
        <div class="section-header">
          <span>📋 提案列表</span>
          <el-radio-group v-model="filterStatus" size="small">
            <el-radio-button label="all">全部</el-radio-button>
            <el-radio-button label="pending">待处理</el-radio-button>
            <el-radio-button label="merged">已合并</el-radio-button>
            <el-radio-button label="rejected">已拒绝</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="5" animated />
      </div>

      <div v-else-if="filteredProposals.length === 0" class="empty-container">
        <el-empty description="暂无提案">
          <p class="empty-tip">
            Crew 执行完成后会自动生成提案。<br />
            或者手动触发：选择一次执行 → 点击「生成回顾」
          </p>
        </el-empty>
      </div>

      <div v-else class="proposals-list">
        <ProposalCard
          v-for="proposal in filteredProposals"
          :key="proposal.exec_id"
          :proposal="proposal"
          @view="viewProposalDetail"
        />
      </div>
    </el-card>

    <!-- 详情弹窗 - Git Merge 风格 -->
    <el-dialog
      v-model="showDetail"
      title="提案详情 - 偏好合并"
      width="90%"
      top="5vh"
      :close-on-click-modal="false"
      class="proposal-detail-dialog"
    >
      <div v-if="loadingDetail" class="loading-container">
        <el-skeleton :rows="10" animated />
      </div>

      <DiffViewer
        v-else-if="currentProposal"
        :original="currentProposal.original_content"
        :suggested="currentProposal.suggested_content"
        :lines="diffLines"
        :stats="diffStats"
        :merging="merging"
        :rejecting="rejecting"
        @merge="handleMerge"
        @reject="handleReject"
      />

      <div v-if="currentProposal" class="proposal-info-footer">
        <div class="info-item">
          <span class="info-label">来源执行:</span>
          <el-link type="primary" @click="viewExecution(currentProposal.exec_id)">
            {{ currentProposal.exec_id }}
          </el-link>
        </div>
        <div class="info-item">
          <span class="info-label">生成时间:</span>
          <span>{{ formatFullDate(currentProposal.created_at) }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">变更摘要:</span>
          <span>{{ currentProposal.diff_summary }}</span>
        </div>
      </div>
    </el-dialog>

    <!-- 当前偏好弹窗 -->
    <el-dialog
      v-model="showCurrent"
      title="📄 当前 preferences.md"
      width="80%"
      top="5vh"
    >
      <div class="current-pref-container">
        <div class="pref-meta">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="文件路径">{{ currentPrefPath }}</el-descriptions-item>
          </el-descriptions>
        </div>
        <div class="pref-content">
          <MarkdownViewer :content="currentPrefContent" />
        </div>
      </div>
    </el-dialog>

    <!-- 拒绝原因弹窗 -->
    <el-dialog v-model="showRejectDialog" title="拒绝提案" width="400px">
      <el-form>
        <el-form-item label="拒绝原因（可选）">
          <el-input
            v-model="rejectReason"
            type="textarea"
            :rows="3"
            placeholder="简要说明拒绝原因，方便后续改进..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRejectDialog = false">取消</el-button>
        <el-button type="danger" @click="confirmReject">确认拒绝</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Document, Refresh } from '@element-plus/icons-vue'
import MarkdownViewer from '@/components/common/MarkdownViewer.vue'
import ProposalCard from '@/components/preferences/ProposalCard.vue'
import DiffViewer from '@/components/preferences/DiffViewer.vue'
import { useProposalList } from '@/composables/useProposalList'
import { useProposalDetail } from '@/composables/useProposalDetail'
import { useProposalActions } from '@/composables/useProposalActions'
import { useCurrentPreferences } from '@/composables/useCurrentPreferences'

const router = useRouter()

// 提案列表管理
const {
  loading,
  filterStatus,
  pendingCount,
  mergedCount,
  rejectedCount,
  totalCount,
  filteredProposals,
  loadProposals,
  updateProposalStatus
} = useProposalList()

// 提案详情管理
const {
  showDetail,
  currentProposal,
  loadingDetail,
  diffLines,
  diffStats,
  viewProposalDetail
} = useProposalDetail()

// 提案操作
const {
  merging,
  rejecting,
  showRejectDialog,
  rejectReason,
  mergeProposal,
  openRejectDialog,
  confirmReject: confirmRejectAction
} = useProposalActions()

// 当前偏好查看
const {
  showCurrent,
  currentPrefContent,
  currentPrefPath,
  loadingCurrent,
  loadCurrentPreferences
} = useCurrentPreferences()

// 合并提案
const handleMerge = async () => {
  if (!currentProposal.value) return
  
  const success = await mergeProposal(currentProposal.value.exec_id)
  if (success) {
    updateProposalStatus(currentProposal.value.exec_id, 'merged')
    showDetail.value = false
  }
}

// 拒绝提案
const handleReject = () => {
  if (!currentProposal.value) return
  openRejectDialog(currentProposal.value.exec_id)
}

// 确认拒绝
const confirmReject = async () => {
  const success = await confirmRejectAction()
  if (success && currentProposal.value) {
    updateProposalStatus(currentProposal.value.exec_id, 'rejected')
    showDetail.value = false
  }
}

// 查看执行记录
const viewExecution = (execId: string) => {
  router.push(`/executions?highlight=${execId}`)
}

// 格式化日期
const formatFullDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

onMounted(() => {
  loadProposals()
})
</script>

<style scoped>
.preferences-page {
  padding: 20px;
}

.stat-card.success {
  background: #f0f9eb;
}

.stat-card.danger {
  background: #fef0f0;
}

.stat-card.info {
  background: #f4f4f5;
}

.proposals-section {
  min-height: 400px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-header span {
  font-weight: 500;
  font-size: 16px;
}

.loading-container {
  padding: 40px 20px;
}

.empty-container {
  padding: 60px 20px;
  text-align: center;
}

.empty-tip {
  color: #909399;
  font-size: 14px;
  line-height: 1.8;
  margin-top: 16px;
}

.proposals-list {
  padding: 8px 0;
}

:deep(.proposal-detail-dialog .el-dialog__body) {
  padding: 0;
  max-height: calc(100vh - 200px);
  overflow: hidden;
}

.proposal-info-footer {
  padding: 16px 20px;
  background: #f5f7fa;
  border-top: 1px solid #e4e7ed;
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.info-label {
  color: #606266;
  font-weight: 500;
}

.current-pref-container {
  max-height: 70vh;
  overflow: auto;
}

.pref-meta {
  margin-bottom: 16px;
}

.pref-content {
  background: #fff;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
  overflow: auto;
  max-height: calc(70vh - 100px);
}
</style>

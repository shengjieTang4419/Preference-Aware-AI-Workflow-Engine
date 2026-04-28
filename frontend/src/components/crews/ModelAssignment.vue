<template>
  <div class="model-assignment">
    <!-- 折叠状态的头部 -->
    <div class="assignment-header" @click="toggleExpand">
      <div class="header-left">
        <el-icon class="expand-icon" :class="{ expanded: isExpanded }">
          <ArrowRight />
        </el-icon>
        <el-icon class="header-icon"><Setting /></el-icon>
        <span class="header-title">模型分配</span>
        
        <!-- 折叠时显示的摘要 -->
        <div v-if="!isExpanded && agentIds.length > 0" class="summary-badges">
          <el-tag v-if="modelStats.basic > 0" size="small" type="success" effect="plain">
            Basic × {{ modelStats.basic }}
          </el-tag>
          <el-tag v-if="modelStats.standard > 0" size="small" type="primary" effect="plain">
            Standard × {{ modelStats.standard }}
          </el-tag>
          <el-tag v-if="modelStats.advanced > 0" size="small" type="warning" effect="plain">
            Advanced × {{ modelStats.advanced }}
          </el-tag>
        </div>
      </div>
      <el-tag size="small" type="info" effect="plain">
        <el-icon><TrendCharts /></el-icon>
        优化成本与性能
      </el-tag>
    </div>

    <!-- 展开状态的内容 -->
    <div v-show="isExpanded">
      <div v-if="agentIds.length === 0" class="empty-state">
        <el-empty description="请先选择 Agents" :image-size="80" />
      </div>

      <div v-else class="assignment-grid">
      <div
        v-for="agentId in agentIds"
        :key="agentId"
        class="assignment-card"
        :class="`tier-${modelValue[agentId] || 'standard'}`"
      >
        <div class="card-header">
          <div class="agent-info">
            <el-avatar :size="32" class="agent-avatar">
              <el-icon><User /></el-icon>
            </el-avatar>
            <span class="agent-name">{{ getAgentName(agentId) }}</span>
          </div>
          <el-tag
            :type="getModelTagType(modelValue[agentId] || 'standard')"
            size="small"
            effect="dark"
          >
            {{ getModelLabel(modelValue[agentId] || 'standard') }}
          </el-tag>
        </div>

        <el-select
          :model-value="modelValue[agentId] || 'standard'"
          @update:model-value="(val: string) => updateModel(agentId, val as 'basic' | 'standard' | 'advanced')"
          class="model-selector"
          size="default"
        >
          <el-option value="basic">
            <div class="option-content">
              <span class="option-label">Basic</span>
              <span class="option-desc">快速响应 · 低成本</span>
            </div>
          </el-option>
          <el-option value="standard">
            <div class="option-content">
              <span class="option-label">Standard</span>
              <span class="option-desc">平衡性能 · 推荐</span>
            </div>
          </el-option>
          <el-option value="advanced">
            <div class="option-content">
              <span class="option-label">Advanced</span>
              <span class="option-desc">深度思考 · 高级</span>
            </div>
          </el-option>
        </el-select>
      </div>
    </div>

    <div v-if="agentIds.length > 0" class="assignment-summary">
      <div class="summary-item">
        <el-icon class="summary-icon"><Coin /></el-icon>
        <span class="summary-text">成本优化建议：优先使用 Basic/Standard 模型</span>
      </div>
    </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Setting, TrendCharts, User, Coin, ArrowRight } from '@element-plus/icons-vue'
import type { Agent } from '@/api'

const props = defineProps<{
  modelValue: Record<string, 'basic' | 'standard' | 'advanced'>
  agentIds: string[]
  agents: Agent[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: Record<string, 'basic' | 'standard' | 'advanced'>]
}>()

// 折叠/展开状态
const isExpanded = ref(false)

const toggleExpand = () => {
  isExpanded.value = !isExpanded.value
}

// 统计各模型等级的数量
const modelStats = computed(() => {
  const stats = { basic: 0, standard: 0, advanced: 0 }
  props.agentIds.forEach((agentId) => {
    const tier = props.modelValue[agentId] || 'standard'
    stats[tier as keyof typeof stats]++
  })
  return stats
})

const getAgentName = (agentId: string): string => {
  const agent = props.agents.find((a) => a.id === agentId)
  return agent ? agent.role : agentId
}

const updateModel = (agentId: string, tier: 'basic' | 'standard' | 'advanced') => {
  const updated: Record<string, 'basic' | 'standard' | 'advanced'> = { 
    ...props.modelValue, 
    [agentId]: tier 
  }
  emit('update:modelValue', updated)
}

const getModelLabel = (tier: string): string => {
  const labels = {
    basic: 'Basic',
    standard: 'Standard',
    advanced: 'Advanced',
  }
  return labels[tier as keyof typeof labels] || 'Standard'
}

const getModelTagType = (tier: string): string => {
  const types = {
    basic: 'success',
    standard: 'primary',
    advanced: 'warning',
  }
  return types[tier as keyof typeof types] || 'primary'
}
</script>

<style scoped>
.model-assignment {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 16px;
  background: #ffffff;
}

.assignment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  user-select: none;
  transition: background-color 0.2s;
  border-radius: 4px;
  margin: -16px -16px 16px -16px;
}

.assignment-header:hover {
  background-color: #f5f7fa;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.expand-icon {
  font-size: 16px;
  color: #909399;
  transition: transform 0.3s;
}

.expand-icon.expanded {
  transform: rotate(90deg);
}

.header-icon {
  font-size: 18px;
  color: #409eff;
}

.summary-badges {
  display: flex;
  gap: 6px;
  margin-left: 12px;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.empty-state {
  padding: 40px 0;
}

.assignment-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.assignment-card {
  background: #fafafa;
  border-radius: 4px;
  padding: 12px 16px;
  border: 1px solid #e4e7ed;
  border-left-width: 3px;
  transition: all 0.2s ease;
}

.assignment-card:hover {
  background: #f5f7fa;
  border-color: #c6e2ff;
}

.assignment-card.tier-basic {
  border-left-color: #67c23a;
}

.assignment-card.tier-standard {
  border-left-color: #409eff;
}

.assignment-card.tier-advanced {
  border-left-color: #e6a23c;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.agent-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.agent-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  flex-shrink: 0;
}

.agent-name {
  font-weight: 500;
  color: #303133;
  font-size: 15px;
}

.model-selector {
  width: 100%;
}

.option-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.option-label {
  font-weight: 500;
  color: #303133;
}

.option-desc {
  font-size: 12px;
  color: #909399;
}

.assignment-summary {
  margin-top: 12px;
  padding: 10px 12px;
  background: #f0f9ff;
  border-radius: 4px;
  border-left: 3px solid #409eff;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.summary-icon {
  color: #409eff;
  font-size: 14px;
}

.summary-text {
  font-size: 12px;
  color: #606266;
}
</style>
